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
                    DecodedTX.decode(d) for d in raw_block.data.data
                ]
            ),
            metadata=_DecodedBlockMetadata(
                metadata=cls._decode_block_metadata(raw_block.metadata.metadata)
            )
        )

    @property
    def transactions(self) -> List['DecodedTX']:
        """ A list of transactions in this block """
        return self.data.data


    @classmethod
    def _decode_block_metadata(cls, metadata_list: List[bytes]) -> '_DecodedMetadataSequence':
        last_config_meta = Metadata.FromString(metadata_list[LAST_CONFIG])
        last_config = LastConfig.FromString(last_config_meta.value)
        sig_metadata = Metadata.FromString(metadata_list[SIGNATURES])
        return (
            _DecodedMetadata(
                value=sig_metadata.value,
                signatures=cls._decode_metadata_signatures(sig_metadata)
            ),
            _DecodedLastConfigMetadata(
                value=last_config,
                signatures=cls._decode_metadata_signatures(last_config_meta),
            ),
            list(metadata_list[TRANSACTIONS_FILTER])
        )

    @staticmethod
    def _decode_metadata_signatures(metadata: Metadata) -> List['_DecodedMetadataSignature']:
        return [
            _DecodedMetadataSignature(
                signatures=s.signature,
                signature_header=_DecodedSignatureHeader.decode(s.signature_header),
            ) for s in metadata.signatures
        ]


@dataclass()
class DecodedTX:
    """ Decoded BlockDataEnvelope """
    signature: bytes
    payload: '_DecodedPayload'

    @classmethod
    def decode(cls, envelope_bytes: bytes) -> 'DecodedTX':
        """ Decode from envelope bytes """
        envelope = Envelope.FromString(envelope_bytes)
        payload = Payload.FromString(envelope.payload)
        header = _DecodedHeader.decode(payload.header)
        payload_type = TransactionType(header.channel_header.type)

        payload_data: _DecodedPayloadData
        if payload_type == TransactionType.Config:
            payload_data = _DecodedConfig.decode(payload.data)
        elif payload_type == TransactionType.ConfigUpdate:
            payload_data = _DecodedConfigUpdateEnvelope.decode(payload.data)
        elif payload_type == TransactionType.EndorserTransaction:
            payload_data = _DecodedTransactionBody.decode(payload.data)
        else:
            payload_data = payload.data

        return cls(
            signature=envelope.signature,
            payload=_DecodedPayload(
                header=header,
                data=payload_data,
            )
        )

    @property
    def tx_id(self) -> str:
        """ The unique identifier for this transaction """
        return self.payload.header.channel_header.tx_id


@dataclass()
class _DecodedSignatureHeader:
    """ Decoded SignatureHeader"""
    creator: SerializedIdentity
    nonce: bytes

    @classmethod
    def decode(cls, header_bytes: bytes) -> '_DecodedSignatureHeader':
        """ Decodes from bytes """
        signature_header = SignatureHeader.FromString(header_bytes)
        return cls(
            creator=SerializedIdentity.FromString(signature_header.creator),
            nonce=signature_header.nonce
        )


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

    @classmethod
    def decode(cls, config_update_bytes: bytes) -> '_DecodedConfigUpdateEnvelope':
        """ Decode from bytes """
        envelope = ConfigUpdateEnvelope.FromString(config_update_bytes)
        return cls(
            config_update=ConfigUpdate.FromString(envelope.config_update),
            signatures=[
                _DecodedConfigUpdateSignature(
                    signature_header=_DecodedSignatureHeader.decode(s.signature_header),
                    signature=s.signature,
                )
                for s in envelope.signatures
            ]
        )


@dataclass()
class _DecodedHeader:
    """ Decoded Header """
    channel_header: ChannelHeader
    signature_header: _DecodedSignatureHeader

    @classmethod
    def decode(cls, header: Header) -> '_DecodedHeader':
        """ Decodes from proto """
        return cls(
            channel_header=ChannelHeader.FromString(header.channel_header),
            signature_header=_DecodedSignatureHeader.decode(
                header.signature_header
            ),
        )


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

    @classmethod
    def decode(cls, config_bytes: bytes) -> '_DecodedConfig':
        """ Decodes from bytes """
        config_env = ConfigEnvelope.FromString(config_bytes)
        last_update_payload = Payload.FromString(config_env.last_update.payload)

        return cls(
            config=config_env.config,
            last_update=_DecodedConfigLastUpdateEnvelope(
                payload=_DecodedConfigLastUpdate(
                    header=_DecodedHeader.decode(last_update_payload.header),
                    data=_DecodedConfigUpdateEnvelope.decode(last_update_payload.data)
                ),
                signature=config_env.last_update.signature
            )
        )


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

    @classmethod
    def decode(cls, action: TransactionAction) -> '_DecodedTransactionAction':
        """ Decodes from a TransactionAction proto """
        payload = ChaincodeActionPayload.FromString(action.payload)

        return cls(
            header=_DecodedSignatureHeader.decode(action.header),
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


@dataclass()
class _DecodedTransactionBody:
    """ Decoded Transaction """
    actions: List[_DecodedTransactionAction]

    @classmethod
    def decode(cls, tx_bytes: bytes) -> '_DecodedTransactionBody':
        """ Decodes from bytes """
        transaction = Transaction.FromString(tx_bytes)
        return _DecodedTransactionBody(
            actions=[_DecodedTransactionAction.decode(a) for a in transaction.actions]
        )


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
