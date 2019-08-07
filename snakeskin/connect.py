"""
    Manage connections to peer and orderer
"""

from .errors import handle_conn_errors
from .factories import build_envelope_stream
from .models import Orderer, Peer
from .protos.common.common_pb2 import Envelope
from .protos.peer.proposal_pb2 import SignedProposal
from .protos.peer.proposal_response_pb2 import ProposalResponse


async def broadcast_to_orderer(envelope: Envelope,
                               orderer: Orderer):
    """ Broadcasts an envelope of data to an orderer node
        and returns the first response
    """
    with handle_conn_errors():
        envelope = build_envelope_stream(envelope)
        async for resp in orderer.broadcaster.Broadcast(envelope):
            return resp


async def process_proposal_on_peer(proposal: SignedProposal,
                                   peer: Peer) -> ProposalResponse:
    """
        Processes a proposed connection on the peer
    """
    with handle_conn_errors():
        return await peer.endorser.ProcessProposal(proposal)
