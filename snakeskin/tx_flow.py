"""
    Transaction Flow
    ----------------

    This module contains
"""

import asyncio
from typing import List


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

from .constants import ChaincodeProposalType
from .errors import TrasactionCommitError, TransactionProposalError
from .factories import (
    build_signature_policy_envelope,
    build_cc_deployment_spec,
    build_generated_tx,
    build_endorsed_tx_envelope,
    encode_proto_bytes,
    tx_context_from_user
)

from .connect import broadcast_to_orderer, process_proposal_on_peer

def generate_instantiate_cc_tx(requestor: User,
                               cc_spec: ChaincodeSpec,
                               channel: Channel,
                               endorsement_policy: EndorsementPolicy = None,
                               upgrade: bool = False) -> GeneratedTX:
    """ Generates an instantiate/upgrade transaction """

    if upgrade:
        proposal_type = ChaincodeProposalType.Upgrade
    else:
        proposal_type = ChaincodeProposalType.Instantiate

    policy = None
    if endorsement_policy:
        sig_policy_env = build_signature_policy_envelope(endorsement_policy)
        policy = sig_policy_env.SerializeToString()

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


async def propose_tx(peers: List[Peer],
                     generated_tx: GeneratedTX) -> EndorsedTX:
    """ Execute a transaction proposal across all provided peers, raising an
        error if any of the peers fails to propose the transaction
    """

    if not peers:
        raise ValueError('Must provide at least one peer to propose a tx')

    peer_responses = await asyncio.gather(*[
        process_proposal_on_peer(
            tx_context=generated_tx.tx_context,
            proposal=generated_tx.signed_proposal,
            peer=peer,
            error_msg='Failed to propose transaction',
        ) for peer in peers
    ])

    # Return the result object
    return EndorsedTX(
        peer_responses=peer_responses,
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

    if orderers:

        tx_context = tx_context_from_user(requestor)


        for idx, orderer in enumerate(orderers):
            is_last = len(orderers) - 1 == idx

            envelope = build_endorsed_tx_envelope(endorsed_tx, requestor)

            resp = await broadcast_to_orderer(envelope, orderer)

            if resp.status != 200:
                # Only raise error for last attempt
                if is_last:
                    raise TrasactionCommitError(
                        'Failed to commit transaction',
                        response=resp,
                        tx_context=tx_context
                    )
                # If response is unsuccessful, try another orderer
                continue
            return resp

    raise ValueError('Must provide at least one orderer to commit tx')


def raise_tx_proposal_error(endorsed_tx: EndorsedTX, msg: str):
    """ Raises a TransactionProposalError if any of the peer responses
        in the EndorsedTX is a failure
    """
    for resp in endorsed_tx.peer_responses:
        if resp.response.status != 200:
            raise TransactionProposalError(
                msg=msg,
                tx_context=endorsed_tx.tx_context,
                response=resp
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
