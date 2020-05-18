"""
    Transact
    --------

    This module contains functions for proposing
    and committing transactions against the blockchain
"""

import asyncio
from typing import List, Union, AsyncIterator

from .events import PeerFilteredEvents
from .protos.orderer.ab_pb2 import BroadcastResponse
from .models.transaction import (
    EndorsedTX,
    GeneratedTX
)
from .models import (
    Channel,
    Orderer,
    Peer,
    User,
    ChaincodeSpec,
    EndorsementPolicy,
)
from .models.endorsement import EndorsementPeerProvider

from .constants import ChaincodeProposalType
from .errors import TransactionProposalError, BlockchainError
from .factories import (
    build_signature_policy_envelope,
    build_cc_deployment_spec,
    build_generated_tx,
    build_endorsed_tx_envelope,
    encode_proto_bytes,
)

from .connect import (
    broadcast_to_orderers, process_proposal_on_peer, first_proposal_success
)

def generate_instantiate_cc_tx(requestor: User,
                               cc_spec: ChaincodeSpec,
                               channel: Channel,
                               upgrade: bool = False) -> GeneratedTX:
    """ Generates an instantiate/upgrade transaction """

    if upgrade:
        proposal_type = ChaincodeProposalType.Upgrade
    else:
        proposal_type = ChaincodeProposalType.Instantiate

    policy = None
    if cc_spec.endorsement_policy:
        sig_policy_env = build_signature_policy_envelope(
            cc_spec.endorsement_policy
        )
        policy = sig_policy_env.SerializeToString()

    if not cc_spec.name:
        raise ValueError('Must specify chaincode name')

    cc_deploy_spec = build_cc_deployment_spec(
        name=cc_spec.name,
        language=cc_spec.language,
        version=cc_spec.version,
        fcn='init',
        args=cc_spec.args,
    )

    args = [
        encode_proto_bytes(proposal_type.value),
        encode_proto_bytes(channel.name),
        cc_deploy_spec.SerializeToString(),
        policy if policy else b'',
        encode_proto_bytes('escc'),
        encode_proto_bytes('vscc'),
    ]

    return build_generated_tx(
        requestor=requestor,
        cc_name='lscc',
        args=args,
        channel=channel,
    )


def generate_cc_tx(requestor: User,
                   cc_name: str,
                   channel: Channel,
                   fcn: str,
                   args: List[str] = None,
                   transient_map: dict = None) -> GeneratedTX:
    """ Generates an invoke transaction """
    full_args = [
        encode_proto_bytes(a) for a in [fcn] + (args or [])
    ]

    return build_generated_tx(
        requestor=requestor,
        cc_name=cc_name,
        args=full_args,
        channel=channel,
        transient_map=transient_map,
    )


async def propose_tx(peers: Union[List[Peer], EndorsementPeerProvider],
                     generated_tx: GeneratedTX) -> EndorsedTX:
    """ Execute a transaction proposal across all provided peers, raising an
        error if any of the peers fails to propose the transaction
    """

    if not peers:
        raise ValueError('Must provide at least one peer to propose a tx')

    # If an endorsement peer provider is used, we attempt to find a successful
    # proposal for each endorsing group, multiplied by the number of required
    # endorsements for that group
    if isinstance(peers, EndorsementPeerProvider):
        peer_responses = await asyncio.gather(*[
            first_proposal_success(
                proposal=generated_tx.signed_proposal,
                peers=peer_iter
            )
            for required_peers, peer_iter in peers.provide_endorsing_groups()
            for _ in range(required_peers)

        ])
    else:
        peer_responses = await asyncio.gather(*[
            process_proposal_on_peer(
                proposal=generated_tx.signed_proposal,
                peer=peer,
            ) for peer in peers
        ])

    # Return the result object
    return EndorsedTX(
        peer_responses=list(peer_responses),
        header=generated_tx.header,
        proposal=generated_tx.proposal,
        tx_context=generated_tx.tx_context,
    )


async def commit_tx(requestor: User,
                    orderers: List[Orderer],
                    endorsed_tx: EndorsedTX) -> BroadcastResponse:
    """ Sends a transaction proposal to the orderer for committing,
        raising an error if there is a synchronous error response from
        the orderer
    """

    envelope = build_endorsed_tx_envelope(endorsed_tx, requestor)
    return await broadcast_to_orderers(
        envelope, orderers, endorsed_tx.tx_id
    )


def raise_tx_proposal_error(endorsed_tx: EndorsedTX, msg: str):
    """ Raises a TransactionProposalError if any of the peer responses
        in the EndorsedTX is a failure
    """
    if not endorsed_tx.fully_endorsed:
        raise TransactionProposalError(
            msg=msg,
            transaction=endorsed_tx
        )


async def commit_tx_and_wait(requestor: User,
                             channel: Channel,
                             peers: List[Peer],
                             orderers: List[Orderer],
                             endorsed_tx: EndorsedTX,
                             timeout: int):
    """
        Commits transaction and checks to ensure that it committed
        successfully
    """
    await commit_tx(
        requestor=requestor,
        orderers=orderers,
        endorsed_tx=endorsed_tx,
    )

    event_hub = PeerFilteredEvents(requestor, channel, peers[0])
    await event_hub.check_transaction(endorsed_tx.tx_context.tx_id, timeout)

