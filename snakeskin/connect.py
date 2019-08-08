"""
    Manage connections to peer and orderer
"""

from typing import List

from .errors import (
    handle_conn_errors, TrasactionCommitError, BlockchainError,
    BlockchainConnectionError
)
from .factories import build_envelope_stream
from .models import Orderer, Peer
from .protos.common.common_pb2 import Envelope
from .protos.peer.proposal_pb2 import SignedProposal
from .protos.peer.proposal_response_pb2 import ProposalResponse


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
