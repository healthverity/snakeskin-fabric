"""
    Manage connections to peer and orderer
"""

from .errors import (
    handle_conn_errors,
    TransactionProposalError,
)
from .factories import build_envelope_stream
from .models import Orderer, Peer
from .models.transaction import TXContext
from .protos.common.common_pb2 import Envelope
from .protos.peer.proposal_pb2 import SignedProposal
from .protos.peer.proposal_response_pb2 import ProposalResponse

@handle_conn_errors
async def broadcast_to_orderer(envelope: Envelope,
                               orderer: Orderer):
    """ Broadcasts an envelope of data to an orderer node
        and returns the first response
    """
    envelope = build_envelope_stream(envelope)
    async for resp in orderer.broadcaster.Broadcast(envelope):
        return resp


@handle_conn_errors
async def process_proposal_on_peer(tx_context: TXContext,
                                   proposal: SignedProposal,
                                   peer: Peer,
                                   error_msg: str) -> ProposalResponse:
    """
        Processes a proposed connection on the peer
    """
    resp = await peer.endorser.ProcessProposal(proposal)
    if resp.response.status != 200:
        raise TransactionProposalError(
            error_msg,
            response=resp,
            tx_context=tx_context
        )
    return resp
