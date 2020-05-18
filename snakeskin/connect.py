"""
    Manage connections to peer and orderer
"""

from typing import List, Iterator, Optional

from .errors import (
    handle_conn_errors, TrasactionCommitError, BlockchainError,
    BlockchainConnectionError, TransactionProposalError
)
from .factories import build_envelope_stream
from .models import Orderer, Peer
from .protos.common.common_pb2 import Envelope
from .protos.peer.proposal_pb2 import SignedProposal
from .protos.peer.proposal_response_pb2 import ProposalResponse
from .protos.discovery.protocol_pb2 import Response, SignedRequest


async def broadcast_to_orderer(envelope: Envelope,
                               orderer: Orderer,
                               tx_id: str):
    """ Broadcasts an envelope of data to an orderer node
        and returns the first response
    """
    with handle_conn_errors():
        envelope = build_envelope_stream(envelope)
        async for resp in orderer.broadcaster.Broadcast(envelope):
            if resp.status != 200:
                raise TrasactionCommitError(
                    'Failed to commit transaction',
                    response=resp,
                    tx_id=tx_id
                )
            return resp


async def broadcast_to_orderers(envelope: Envelope,
                                orderers: List[Orderer],
                                tx_id: str):
    """ Broadcast an envelope of data to orderer nodes in order and
        returns the first successful response """

    if not orderers:
        raise ValueError('Must provide at least one orderer')

    error: BlockchainError
    for orderer in orderers:

        try:
            resp = await broadcast_to_orderer(envelope, orderer, tx_id)
        # If connection error, try next orderer
        except BlockchainConnectionError as err:
            error = err
            continue

        # If response is unsuccessful, store error and continue
        return resp

    raise error


async def process_proposal_on_peer(proposal: SignedProposal,
                                   peer: Peer) -> ProposalResponse:
    """
        Processes a proposed connection on the peer
    """
    with handle_conn_errors():
        return await peer.endorser.ProcessProposal(proposal)


async def process_peer_discovery(request: SignedRequest,
                                 peer: Peer) -> Response:
    """
        Processes a peer dicovery request and returns the response
    """
    with handle_conn_errors():
        return await peer.discovery.Discover(request)


async def first_proposal_success(proposal: SignedProposal,
                                 peers: Iterator[Peer]) -> ProposalResponse:
    """
        Process a proposal against one or more peers, returning either the
        first successful response received or, if no responses succeeded,
        the last response received.

        Note that if the peer iterator is empty or all of the peers
        failed to even connect, an error will be raised.
    """
    resp = None
    conn_error = None
    for peer in peers:
        try:
            resp = await process_proposal_on_peer(proposal, peer)
            if resp.response.status == 200:
                return resp
        except BlockchainConnectionError as exc:
            conn_error = exc
    # If there's no response at all, raise the last connection error
    # or raise a configuration error indicating that no peers were provided
    if not resp:
        if conn_error:
            raise conn_error
        raise BlockchainError(
            'Not enough peers supplied to propose'
        )
    return resp
