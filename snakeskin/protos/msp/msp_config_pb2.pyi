# @generated by generate_proto_mypy_stubs.py.  Do not edit!
import sys
from google.protobuf.descriptor import (
    Descriptor as google___protobuf___descriptor___Descriptor,
)

from google.protobuf.internal.containers import (
    RepeatedCompositeFieldContainer as google___protobuf___internal___containers___RepeatedCompositeFieldContainer,
    RepeatedScalarFieldContainer as google___protobuf___internal___containers___RepeatedScalarFieldContainer,
)

from google.protobuf.message import (
    Message as google___protobuf___message___Message,
)

from typing import (
    Iterable as typing___Iterable,
    Optional as typing___Optional,
    Text as typing___Text,
)

from typing_extensions import (
    Literal as typing_extensions___Literal,
)


class MSPConfig(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    type = ... # type: int
    config = ... # type: bytes

    def __init__(self,
        *,
        type : typing___Optional[int] = None,
        config : typing___Optional[bytes] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> MSPConfig: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"config",u"type"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"config",b"config",u"type",b"type"]) -> None: ...

class FabricMSPConfig(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    name = ... # type: typing___Text
    root_certs = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[bytes]
    intermediate_certs = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[bytes]
    admins = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[bytes]
    revocation_list = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[bytes]
    tls_root_certs = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[bytes]
    tls_intermediate_certs = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[bytes]

    @property
    def signing_identity(self) -> SigningIdentityInfo: ...

    @property
    def organizational_unit_identifiers(self) -> google___protobuf___internal___containers___RepeatedCompositeFieldContainer[FabricOUIdentifier]: ...

    @property
    def crypto_config(self) -> FabricCryptoConfig: ...

    @property
    def fabric_node_ous(self) -> FabricNodeOUs: ...

    def __init__(self,
        *,
        name : typing___Optional[typing___Text] = None,
        root_certs : typing___Optional[typing___Iterable[bytes]] = None,
        intermediate_certs : typing___Optional[typing___Iterable[bytes]] = None,
        admins : typing___Optional[typing___Iterable[bytes]] = None,
        revocation_list : typing___Optional[typing___Iterable[bytes]] = None,
        signing_identity : typing___Optional[SigningIdentityInfo] = None,
        organizational_unit_identifiers : typing___Optional[typing___Iterable[FabricOUIdentifier]] = None,
        crypto_config : typing___Optional[FabricCryptoConfig] = None,
        tls_root_certs : typing___Optional[typing___Iterable[bytes]] = None,
        tls_intermediate_certs : typing___Optional[typing___Iterable[bytes]] = None,
        fabric_node_ous : typing___Optional[FabricNodeOUs] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> FabricMSPConfig: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"crypto_config",u"fabric_node_ous",u"signing_identity"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"admins",u"crypto_config",u"fabric_node_ous",u"intermediate_certs",u"name",u"organizational_unit_identifiers",u"revocation_list",u"root_certs",u"signing_identity",u"tls_intermediate_certs",u"tls_root_certs"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"crypto_config",b"crypto_config",u"fabric_node_ous",b"fabric_node_ous",u"signing_identity",b"signing_identity"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"admins",b"admins",u"crypto_config",b"crypto_config",u"fabric_node_ous",b"fabric_node_ous",u"intermediate_certs",b"intermediate_certs",u"name",b"name",u"organizational_unit_identifiers",b"organizational_unit_identifiers",u"revocation_list",b"revocation_list",u"root_certs",b"root_certs",u"signing_identity",b"signing_identity",u"tls_intermediate_certs",b"tls_intermediate_certs",u"tls_root_certs",b"tls_root_certs"]) -> None: ...

class FabricCryptoConfig(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    signature_hash_family = ... # type: typing___Text
    identity_identifier_hash_function = ... # type: typing___Text

    def __init__(self,
        *,
        signature_hash_family : typing___Optional[typing___Text] = None,
        identity_identifier_hash_function : typing___Optional[typing___Text] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> FabricCryptoConfig: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"identity_identifier_hash_function",u"signature_hash_family"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"identity_identifier_hash_function",b"identity_identifier_hash_function",u"signature_hash_family",b"signature_hash_family"]) -> None: ...

class IdemixMSPConfig(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    name = ... # type: typing___Text
    ipk = ... # type: bytes
    revocation_pk = ... # type: bytes
    epoch = ... # type: int

    @property
    def signer(self) -> IdemixMSPSignerConfig: ...

    def __init__(self,
        *,
        name : typing___Optional[typing___Text] = None,
        ipk : typing___Optional[bytes] = None,
        signer : typing___Optional[IdemixMSPSignerConfig] = None,
        revocation_pk : typing___Optional[bytes] = None,
        epoch : typing___Optional[int] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> IdemixMSPConfig: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"signer"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"epoch",u"ipk",u"name",u"revocation_pk",u"signer"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"signer",b"signer"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"epoch",b"epoch",u"ipk",b"ipk",u"name",b"name",u"revocation_pk",b"revocation_pk",u"signer",b"signer"]) -> None: ...

class IdemixMSPSignerConfig(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    cred = ... # type: bytes
    sk = ... # type: bytes
    organizational_unit_identifier = ... # type: typing___Text
    role = ... # type: int
    enrollment_id = ... # type: typing___Text
    credential_revocation_information = ... # type: bytes

    def __init__(self,
        *,
        cred : typing___Optional[bytes] = None,
        sk : typing___Optional[bytes] = None,
        organizational_unit_identifier : typing___Optional[typing___Text] = None,
        role : typing___Optional[int] = None,
        enrollment_id : typing___Optional[typing___Text] = None,
        credential_revocation_information : typing___Optional[bytes] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> IdemixMSPSignerConfig: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"cred",u"credential_revocation_information",u"enrollment_id",u"organizational_unit_identifier",u"role",u"sk"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"cred",b"cred",u"credential_revocation_information",b"credential_revocation_information",u"enrollment_id",b"enrollment_id",u"organizational_unit_identifier",b"organizational_unit_identifier",u"role",b"role",u"sk",b"sk"]) -> None: ...

class SigningIdentityInfo(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    public_signer = ... # type: bytes

    @property
    def private_signer(self) -> KeyInfo: ...

    def __init__(self,
        *,
        public_signer : typing___Optional[bytes] = None,
        private_signer : typing___Optional[KeyInfo] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> SigningIdentityInfo: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"private_signer"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"private_signer",u"public_signer"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"private_signer",b"private_signer"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"private_signer",b"private_signer",u"public_signer",b"public_signer"]) -> None: ...

class KeyInfo(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    key_identifier = ... # type: typing___Text
    key_material = ... # type: bytes

    def __init__(self,
        *,
        key_identifier : typing___Optional[typing___Text] = None,
        key_material : typing___Optional[bytes] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> KeyInfo: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"key_identifier",u"key_material"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"key_identifier",b"key_identifier",u"key_material",b"key_material"]) -> None: ...

class FabricOUIdentifier(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    certificate = ... # type: bytes
    organizational_unit_identifier = ... # type: typing___Text

    def __init__(self,
        *,
        certificate : typing___Optional[bytes] = None,
        organizational_unit_identifier : typing___Optional[typing___Text] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> FabricOUIdentifier: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"certificate",u"organizational_unit_identifier"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"certificate",b"certificate",u"organizational_unit_identifier",b"organizational_unit_identifier"]) -> None: ...

class FabricNodeOUs(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    enable = ... # type: bool

    @property
    def client_ou_identifier(self) -> FabricOUIdentifier: ...

    @property
    def peer_ou_identifier(self) -> FabricOUIdentifier: ...

    def __init__(self,
        *,
        enable : typing___Optional[bool] = None,
        client_ou_identifier : typing___Optional[FabricOUIdentifier] = None,
        peer_ou_identifier : typing___Optional[FabricOUIdentifier] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> FabricNodeOUs: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"client_ou_identifier",u"peer_ou_identifier"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"client_ou_identifier",u"enable",u"peer_ou_identifier"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"client_ou_identifier",b"client_ou_identifier",u"peer_ou_identifier",b"peer_ou_identifier"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"client_ou_identifier",b"client_ou_identifier",u"enable",b"enable",u"peer_ou_identifier",b"peer_ou_identifier"]) -> None: ...