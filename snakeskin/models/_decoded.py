"""
    Models for storing information about a _decoded HyperledgerFabric block,
    where all of the properties are deserialized into their corresponding
    models.

"""

from typing import List, Union, Tuple
from dataclasses import dataclass

from ..protos.common.common_pb2 import (
    BlockHeader,
    Header,
    ChannelHeader,
    SignatureHeader,
    Envelope,
    Payload,
    SIGNATURES,
    LAST_CONFIG,
    TRANSACTIONS_FILTER,
    Metadata,
    LastConfig
)
from ..protos.common.configtx_pb2 import (
    Config,
    ConfigEnvelope,
    ConfigUpdateEnvelope,
    ConfigUpdate,
)
from ..protos.msp.identities_pb2 import SerializedIdentity
from ..protos.peer.proposal_response_pb2 import (
    ProposalResponsePayload
)
from ..protos.peer.proposal_pb2 import ChaincodeProposalPayload
from ..protos.peer.transaction_pb2 import (
    Transaction,
    TransactionAction,
    ChaincodeActionPayload,
)


from ..constants import TransactionType


@dataclass()
class DecodedBlock:
    """ A Hyperledger Fabric block, decoded into a normalized data-structure
        decoded
    """
    header: BlockHeader
    data: '_DecodedBlockData'
    metadata: '_DecodedBlockMetadata'

    @classmethod
    def decode(cls, raw_block) -> 'DecodedBlock':
        """ Decodes from a raw block """
        return cls(
            header=raw_block.header,
            data=_DecodedBlockData(
                data=[
                    _decode_block_data(d) for d in raw_block.data.data
                ]
            ),
            metadata=_DecodedBlockMetadata(
                metadata=_decode_block_metadata(raw_block.metadata.metadata)
            )
        )

    @property
    def transactions(self) -> List['DecodedTX']:
        """ A list of transactions in this block """
        return self.data.data


@dataclass()
class DecodedTX:
    """ Decoded BlockDataEnvelope """
    signature: bytes
    payload: '_DecodedPayload'

    @property
    def tx_id(self) -> str:
        """ The unique identifier for this transaction """
        return self.payload.header.channel_header.tx_id


@dataclass()
class _DecodedSignatureHeader:
    """ Decoded SignatureHeader"""
    creator: SerializedIdentity
    nonce: bytes


@dataclass()
class _DecodedConfigUpdateSignature:
    """ Decoded ConfigUpdateSignature """
    signature_header: _DecodedSignatureHeader
    signature: bytes


@dataclass()
class _DecodedConfigUpdateEnvelope:
    """ Decoded ConfigUpdate Signature """
    config_update: ConfigUpdate
    signatures: List[_DecodedConfigUpdateSignature]


@dataclass()
class _DecodedHeader:
    """ Decoded Header """
    channel_header: ChannelHeader
    signature_header: _DecodedSignatureHeader


@dataclass()
class _DecodedConfigLastUpdate:
    """ Decoded ConfigLastUpdate """
    header: _DecodedHeader
    data: _DecodedConfigUpdateEnvelope


@dataclass()
class _DecodedConfigLastUpdateEnvelope:
    """ Decoded ConfigLastUpdateEnvelope """
    payload: _DecodedConfigLastUpdate
    signature: bytes


@dataclass()
class _DecodedConfig:
    """ Decoded Config """
    config: Config
    last_update: _DecodedConfigLastUpdateEnvelope


@dataclass()
class _DecodedEndoresement:
    """ Decoded Endorsement """
    endorser: SerializedIdentity
    signature: bytes


@dataclass()
class _DecodedChaincodeEndorsedAction:
    """ Decoded ChaincodeEndorsedAction """
    proposal_response_payload: ProposalResponsePayload
    endorsements: List[_DecodedEndoresement]


@dataclass()
class _DecodedChaincodeActionPayload:
    """ Decoded ChaincodeActionPayload """
    action: _DecodedChaincodeEndorsedAction
    chaincode_proposal_payload: ChaincodeProposalPayload


@dataclass()
class _DecodedTransactionAction:
    """ Decoded TransactionAction """
    header: _DecodedSignatureHeader
    payload: _DecodedChaincodeActionPayload


@dataclass()
class _DecodedTransactionBody:
    """ Decoded Transaction """
    actions: List[_DecodedTransactionAction]

_DecodedPayloadData = Union[
    _DecodedConfig,
    _DecodedConfigUpdateEnvelope,
    _DecodedTransactionBody,
    bytes
]

@dataclass()
class _DecodedPayload:
    """ Decoded Payload """
    header: _DecodedHeader
    data: _DecodedPayloadData

    @property
    def type(self) -> TransactionType:
        """ Returns the type data based on the header, which is useful
            for filtering payloads based on type
        """
        return TransactionType(self.header.channel_header.type)

@dataclass()
class _DecodedMetadataSignature:
    """ Decoded MetadataSignature """
    signatures: bytes
    signature_header: _DecodedSignatureHeader


@dataclass()
class _DecodedLastConfigMetadata:
    """ Decoded LastConfigMetadata """
    signatures: List[_DecodedMetadataSignature]
    value: LastConfig

@dataclass()
class _DecodedMetadata:
    """ Decoded Metadata """
    signatures: List[_DecodedMetadataSignature]
    value: bytes


_DecodedMetadataSequence = Tuple[
    _DecodedMetadata, _DecodedLastConfigMetadata, List[int]
]


@dataclass()
class _DecodedBlockMetadata:
    """ Decoded BlockMetadata """
    metadata: _DecodedMetadataSequence


@dataclass()
class _DecodedBlockData:
    """ Decoded BlockData """
    data: List[DecodedTX]


def _decode_block_data(envelope_bytes: bytes) -> DecodedTX:
    envelope = Envelope.FromString(envelope_bytes)
    payload = Payload.FromString(envelope.payload)
    header = _decode_header(payload.header)
    payload_type = TransactionType(header.channel_header.type)

    payload_data: _DecodedPayloadData
    if payload_type == TransactionType.Config:
        payload_data = _decode_config(payload.data)
    elif payload_type == TransactionType.ConfigUpdate:
        payload_data = _decode_config_update(payload.data)
    elif payload_type == TransactionType.EndorserTransaction:
        payload_data = _decode_transaction(payload.data)
    else:
        payload_data = payload.data

    return DecodedTX(
        signature=envelope.signature,
        payload=_DecodedPayload(
            header=header,
            data=payload_data,
        )
    )

def _decode_header(header: Header) -> _DecodedHeader:
    return _DecodedHeader(
        channel_header=_decode_channel_header(header.channel_header),
        signature_header=_decode_signature_header(header.signature_header),
    )


def _decode_channel_header(header_bytes: bytes) -> ChannelHeader:
    return ChannelHeader.FromString(header_bytes)


def _decode_signature_header(header_bytes: bytes) -> _DecodedSignatureHeader:
    signature_header = SignatureHeader.FromString(header_bytes)
    return _DecodedSignatureHeader(
        creator=SerializedIdentity.FromString(signature_header.creator),
        nonce=signature_header.nonce
    )

def _decode_config(config_bytes: bytes) -> _DecodedConfig:
    config_env = ConfigEnvelope.FromString(config_bytes)
    last_update_payload = Payload.FromString(config_env.last_update.payload)

    return _DecodedConfig(
        config=config_env.config,
        last_update=_DecodedConfigLastUpdateEnvelope(
            payload=_DecodedConfigLastUpdate(
                header=_decode_header(last_update_payload.header),
                data=_decode_config_update(last_update_payload.data)
            ),
            signature=config_env.last_update.signature
        )
    )


def _decode_config_update(config_update_bytes: bytes) -> _DecodedConfigUpdateEnvelope:
    envelope = ConfigUpdateEnvelope.FromString(config_update_bytes)
    return _DecodedConfigUpdateEnvelope(
        config_update=ConfigUpdate.FromString(envelope.config_update),
        signatures=[
            _DecodedConfigUpdateSignature(
                signature_header=_decode_signature_header(s.signature_header),
                signature=s.signature,
            )
            for s in envelope.signatures
        ]
    )


def _decode_transaction(tx_bytes: bytes) -> _DecodedTransactionBody:
    transaction = Transaction.FromString(tx_bytes)
    return _DecodedTransactionBody(
        actions=[_decode_transaction_action(a) for a in transaction.actions]
    )


def _decode_transaction_action(action: TransactionAction) -> _DecodedTransactionAction:
    payload = ChaincodeActionPayload.FromString(action.payload)

    return _DecodedTransactionAction(
        header=_decode_signature_header(action.header),
        payload=_DecodedChaincodeActionPayload(
            action=_DecodedChaincodeEndorsedAction(
                proposal_response_payload=ProposalResponsePayload.FromString(
                    payload.action.proposal_response_payload
                ),
                endorsements=[
                    _DecodedEndoresement(
                        endorser=SerializedIdentity.FromString(e.endorser),
                        signature=e.signature
                    ) for e in payload.action.endorsements
                ]
            ),
            chaincode_proposal_payload=ChaincodeProposalPayload.FromString(
                payload.chaincode_proposal_payload
            )
        ),
    )


def _decode_block_metadata(metadata_list: List[bytes]) -> _DecodedMetadataSequence:
    last_config_meta = Metadata.FromString(metadata_list[LAST_CONFIG])
    last_config = LastConfig.FromString(last_config_meta.value)
    sig_metadata = Metadata.FromString(metadata_list[SIGNATURES])
    return (
        _DecodedMetadata(
            value=sig_metadata.value,
            signatures=_decode_metadata_signatures(sig_metadata)
        ),
        _DecodedLastConfigMetadata(
            value=last_config,
            signatures=_decode_metadata_signatures(last_config_meta),
        ),
        list(metadata_list[TRANSACTIONS_FILTER])
    )


def _decode_metadata_signatures(metadata: Metadata) -> List[_DecodedMetadataSignature]:
    return [
        _DecodedMetadataSignature(
            signatures=s.signature,
            signature_header=_decode_signature_header(s.signature_header),
        ) for s in metadata.signatures
    ]
