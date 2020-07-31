"""
    Protobuf factory functions
"""

import base64
from hashlib import sha256
from typing import List

from google.protobuf.timestamp_pb2 import Timestamp
from .protos.common.common_pb2 import (
    SignatureHeader,
    Payload,
    Envelope,
    ChannelHeader,
    Header,
)
from .protos.common.configtx_pb2 import (
    ConfigSignature,
    ConfigUpdateEnvelope,
)
from .protos.common.policies_pb2 import (
    SignaturePolicyEnvelope,
    SignaturePolicy,
)
from .protos.msp.identities_pb2 import SerializedIdentity
from .protos.peer.transaction_pb2 import (
    ChaincodeActionPayload,
    Transaction,
    TransactionAction,
    ChaincodeEndorsedAction
)
from .protos.peer.chaincode_pb2 import (
    ChaincodeSpec as ChaincodeSpecProto,
    ChaincodeID,
    ChaincodeInput,
    ChaincodeInvocationSpec,
    ChaincodeDeploymentSpec,
)
from .protos.peer.proposal_pb2 import (
    ChaincodeHeaderExtension,
    ChaincodeProposalPayload,
    Proposal,
    SignedProposal,
)
from .protos.msp.msp_principal_pb2 import (
    MSPRole,
    MSPPrincipal,
)

from .protos.orderer.ab_pb2 import (
    SeekNewest,
    SeekPosition,
    SeekSpecified,
    SeekInfo
)

from .models import (
    Channel,
    User,
    EndorsementPolicy,
)
from .models.transaction import (
    TXContext,
    EndorsedTX,
    GeneratedTX,
)
from .constants import (
    SeekBehavior, TransactionType, PolicyExpression,
    ChaincodeLanguage, INDEFINITE_STOP_POSITION
)


def build_header(tx_context: TXContext,
                 channel: Channel = None,
                 extension: bytes = None,
                 tx_type: TransactionType = TransactionType.EndorserTransaction,
                 tls_cert: bytes = None) -> Header:
    """ Builds a transaction Header proto """

    timestamp = Timestamp()
    timestamp.GetCurrentTime()

    channel_header = ChannelHeader(
        type=tx_type.value,
        version=1,
        tx_id=tx_context.tx_id,
        channel_id=encode_proto_str(channel and channel.name or ''),
        epoch=tx_context.epoch,
        timestamp=timestamp,
    )

    if tls_cert:
        b64der = pem_to_der(tls_cert)
        channel_header.tls_cert_hash = sha256(b64der).digest()

    if extension:
        channel_header.extension = extension

    signature_header = SignatureHeader(
        creator=tx_context.identity.SerializeToString(),
        nonce=tx_context.nonce
    )

    header = Header(
        channel_header=channel_header.SerializeToString(),
        signature_header=signature_header.SerializeToString(),
    )

    return header


def build_envelope(requestor: User,
                   tx_context: TXContext,
                   data: bytes,
                   channel: Channel = None,
                   tls_cert: bytes = None,
                   extension: bytes = None,
                   tx_type: TransactionType = TransactionType.EndorserTransaction,
                   ) -> Envelope:
    """ Builds an Envelope for sending to peer or orderer """

    header = build_header(
        tx_context=tx_context,
        channel=channel,
        tls_cert=tls_cert,
        extension=extension,
        tx_type=tx_type
    )
    payload = Payload(
        header=header,
        data=data,
    )

    return wrap_transaction(requestor, payload)


def build_seek_info(start=None, stop=INDEFINITE_STOP_POSITION,
                    behavior=SeekBehavior.BlockUntilReady):
    """ For block streaming, builds a SeekInfo protobuf that will
        indicate when to start and stop streaming
    """

    if start is None:
        seek_start = SeekPosition(
            newest=SeekNewest()
        )
    else:
        seek_start = SeekPosition(
            specified=SeekSpecified(
                number=start
            )
        )

    if stop is None:
        seek_stop = SeekPosition(
            newest=SeekNewest()
        )
    else:
        seek_stop = SeekPosition(
            specified=SeekSpecified(
                number=stop
            )
        )

    return SeekInfo(
        start=seek_start,
        stop=seek_stop,
        behavior=SeekInfo.SeekBehavior.Value(behavior.value)
    )


def build_endorsed_tx_envelope(endorsed_tx: EndorsedTX,
                               requestor: User) -> Envelope:
    """ Builds an Envelope protobuf that contains an endorsed transaction
        payload for sending to the Orderer
    """

    response = endorsed_tx.peer_responses[0]

    action_payload = ChaincodeActionPayload(
        action=ChaincodeEndorsedAction(
            proposal_response_payload=response.payload,
            endorsements=[
                r.endorsement for r in endorsed_tx.peer_responses
            ]
        ),
        chaincode_proposal_payload=endorsed_tx.proposal.payload
    ).SerializeToString()

    transaction = Transaction(
        actions=[
            TransactionAction(
                header=endorsed_tx.header.signature_header,
                payload=action_payload
            )
        ]
    )
    payload = Payload(
        header=endorsed_tx.header,
        data=transaction.SerializeToString()
    )

    return wrap_transaction(
        requestor, payload
    )


def tx_context_from_user(user: User) -> TXContext:
    """ Creates a TXContext object from a User """
    nonce = user.crypto_suite.generate_nonce(24)
    identity = SerializedIdentity(
        mspid=user.msp_id,
        id_bytes=user.cert
    )

    return TXContext(
        identity=identity,
        nonce=nonce,
        tx_id=user.crypto_suite.hash(nonce + identity.SerializeToString()).hexdigest()
    )


def encode_proto_bytes(val: str) -> bytes:
    """ Encodes a proto string into latin1 bytes """
    return val.encode('latin1')


def encode_proto_str(val: str) -> str:
    """ Ensures proto str is in utf-8 encoding """
    return encode_proto_bytes(val).decode('utf-8')


def pem_to_der(pem: bytes) -> bytes:
    """ Pulls the base64 decoded DER from a PEM file """
    arr = pem.split(b'\n')
    der = b''.join(arr[1:-2])
    return base64.b64decode(der)


def wrap_transaction(user: User,
                     payload: Payload) -> Envelope:
    """ Wraps a transaction payload in an envelope """
    payload_bytes = payload.SerializeToString()
    return Envelope(
        signature=sign(user, payload_bytes),
        payload=payload_bytes
    )

def sign(user: User, payload: bytes) -> bytes:
    """ Signs a payload using the user's private key """
    return user.crypto_suite.sign(user.private_key, payload)


def build_endorsement_policy(policy: EndorsementPolicy,
                             role_map: dict = None) -> SignaturePolicy:
    """ Recursively Builds out a SignaturePolicy from an EndorsementPolicy
        definition
    """

    rmap = role_map or policy.role_map

    if policy.expr == PolicyExpression.And:
        n_out_of = len(policy.roles) + len(policy.sub_policies)

    elif policy.expr == PolicyExpression.Or:
        n_out_of = 1

    elif policy.expr == PolicyExpression.OutOf:
        if not policy.out_of:
            raise ValueError('Must supply out_of')
        n_out_of = policy.out_of

    else:
        raise ValueError(
            f'Unrecognized PolicyExpression {policy.expr}'
        )

    sig_policies = []
    for role in policy.roles:
        idx = rmap[role]
        sig_policies.append(SignaturePolicy(signed_by=idx))

    for sub_policy in policy.sub_policies:
        sig_policies.append(
            build_endorsement_policy(sub_policy, role_map=rmap)
        )

    return SignaturePolicy(
        n_out_of=SignaturePolicy.NOutOf(
            n=n_out_of,
            rules=sig_policies
        )
    )


def build_signature_policy_envelope(endorsement_policy: EndorsementPolicy
                                   ) -> SignaturePolicyEnvelope:
    """ Builds a SignaturePolicyEnvelope from an EndorsementPolicy """
    return SignaturePolicyEnvelope(
        version=0,
        rule=build_endorsement_policy(endorsement_policy),
        identities=[
            MSPPrincipal(
                principal_classification=MSPPrincipal.ROLE,
                principal=MSPRole(
                    role=MSPRole.MSPRoleType.Value(role.role.upper()),
                    msp_identifier=role.msp,
                ).SerializeToString(),
            )
            for role in endorsement_policy.all_roles
        ]
    )


def build_config_update_envelope(channel: Channel,
                                 tx_context: TXContext,
                                 requestor: User,
                                 config_update: bytes) -> Envelope:
    """ Prepares a channel transaction for sending to the orderer """

    header = SignatureHeader(
        creator=tx_context.identity.SerializeToString(),
        nonce=tx_context.nonce
    )
    header_bytes = header.SerializeToString()
    signature = ConfigSignature(
        signature_header=header_bytes,
        signature=sign(requestor, header_bytes + config_update)
    )

    # Generate envelope
    config_update_envelope = ConfigUpdateEnvelope(
        config_update=config_update,
        signatures=[signature],
    )

    return build_envelope(
        requestor=requestor,
        tx_context=tx_context,
        channel=channel,
        data=config_update_envelope.SerializeToString(),
        tx_type=TransactionType.ConfigUpdate,
    )


async def build_envelope_stream(envelope: Envelope):
    """ Builds an async stream of the envelope """
    yield envelope


def build_cc_deployment_spec(name: str,
                             language: ChaincodeLanguage,
                             fcn: str = None,
                             version: str = None,
                             path: str = None,
                             code_package: bytes = None,
                             args: List[str] = None) -> ChaincodeDeploymentSpec:
    """
        Builds out a ChaincodeDeploymentSpec proto
    """

    input_args = []
    if fcn:
        input_args.append(encode_proto_bytes(fcn))
    if args:
        input_args.extend(encode_proto_bytes(arg) for arg in args)

    # construct the deployment spec
    cc_id = ChaincodeID(
        name=name,
    )
    if version:
        cc_id.version = version

    if path:
        cc_id.path = path

    cc_spec = ChaincodeSpecProto(
        chaincode_id=cc_id,
        type=ChaincodeSpecProto.Type.Value(language.value),
        input=ChaincodeInput(
            args=input_args
        ) if input_args else None
    )

    cc_deploy_spec = ChaincodeDeploymentSpec(chaincode_spec=cc_spec)

    if code_package:
        cc_deploy_spec.code_package = code_package

    return cc_deploy_spec


def build_generated_tx(requestor: User,
                       cc_name: str,
                       args: List[bytes],
                       channel: Channel = None,
                       transient_map: dict = None) -> GeneratedTX:
    """ Generically generates a transaction that can be sent to peers for
        endorsement
    """

    chaincode_id = ChaincodeID(
        name=cc_name,
    )

    tx_context = tx_context_from_user(requestor)

    extension = ChaincodeHeaderExtension(
        chaincode_id=chaincode_id
    )

    header = build_header(
        tx_context=tx_context,
        channel=channel,
        extension=extension.SerializeToString()
    )

    header_bytes = header.SerializeToString()

    cc_spec = ChaincodeSpecProto(
        type=ChaincodeSpecProto.Type.Value(
            ChaincodeLanguage.GOLANG.value
        ),
        chaincode_id=chaincode_id,
        input=ChaincodeInput(
            args=args
        ),
    )
    cc_invoke_spec = ChaincodeInvocationSpec(
        chaincode_spec=cc_spec
    ).SerializeToString()

    cc_payload = ChaincodeProposalPayload(
        input=cc_invoke_spec
    )

    proposal = Proposal(
        header=header_bytes,
        payload=cc_payload.SerializeToString(),
    )

    # If there is a transient map, create another proposal with that data
    # to sign and send to peers
    if transient_map:
        for name, bytes_value in transient_map.items():
            cc_payload.TransientMap[name] = bytes_value
        transient_proposal = Proposal(
            header=header_bytes,
            payload=cc_payload.SerializeToString(),
        )
    # If there is not a transient map, there is not distinction between the
    # transient and regular proposal
    else:
        transient_proposal = proposal

    transient_proposal_bytes = transient_proposal.SerializeToString()

    signed_proposal = SignedProposal(
        signature=sign(requestor, transient_proposal_bytes),
        proposal_bytes=transient_proposal_bytes
    )

    return GeneratedTX(
        tx_context=tx_context,
        signed_proposal=signed_proposal,
        proposal=proposal,
        header=header
    )
