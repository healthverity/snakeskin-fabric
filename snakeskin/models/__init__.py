"""
    Blockchain models
"""
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Mapping, Union, Optional, Any

import aiogrpc # type: ignore
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend

from ..protos.orderer.ab_pb2_grpc import AtomicBroadcastStub
from ..protos.common.common_pb2 import (
    Header,
    BlockMetadata,
    BlockHeader,
    Metadata,
    LastConfig,
    ChannelHeader
)
from ..protos.common.configtx_pb2 import (Config, ConfigGroup)
from ..protos.msp.identities_pb2 import SerializedIdentity
from ..protos.peer.proposal_response_pb2 import (
    ProposalResponse,
    ProposalResponsePayload
)
from ..protos.peer.proposal_pb2 import (
    Proposal,
    ChaincodeProposalPayload,
    SignedProposal
)
from ..protos.peer.peer_pb2_grpc import EndorserStub
from ..protos.peer.events_pb2_grpc import DeliverStub
from ..protos.peer.transaction_pb2 import TxValidationCode
from ..protos.peer.events_pb2 import FilteredTransaction
from ..protos.discovery.protocol_pb2_grpc import DiscoveryStub

from ..constants import ChaincodeLanguage, PolicyExpression
from ..crypto import CryptoSuite
from ._base import BaseModel

DEFAULT_CRYPTO_BACKEND = default_backend()


@dataclass()
class User(BaseModel):
    """ A model to represent a Hyperledger Fabric User """

    msp_id: str
    name: Optional[str] = None
    cert_path: Optional[str] = None
    key_path: Optional[str] = None
    cert: Optional[bytes] = None
    key: Optional[bytes] = None
    crypto_suite: Any = field(default=CryptoSuite.default, compare=False)
    private_key: Any = field(default=None, compare=False)

    def __post_init__(self):

        if not self.cert:
            if not self.cert_path:
                raise ValueError('Must provide either cert or cert_path')
            with open(self.cert_path, 'rb') as inf:
                self.cert = inf.read()

        if not self.key:
            if not self.key_path:
                raise ValueError(
                    'Must provide either key or key_path'
                )
            with open(self.key_path, 'rb') as inf:
                self.key = inf.read()

        self.private_key = load_pem_private_key(
            self.key, None, DEFAULT_CRYPTO_BACKEND
        )


@dataclass()
class _ConnectedModel(BaseModel):
    """ A base model to represent Hyperledger Fabric infrastructure that is
        accessible via a gRPC connection
    """
    endpoint: str
    ssl_target_name: Optional[str] = None
    tls_ca_cert_path: Optional[str] = None
    tls_ca_cert: Optional[bytes] = None
    client_cert_path: Optional[str] = None
    client_cert: Optional[bytes] = None
    client_key_path: Optional[str] = None
    client_key: Optional[bytes] = None

    def __post_init__(self):
        if not self.tls_ca_cert and self.tls_ca_cert_path:
            with open(self.tls_ca_cert_path, 'rb') as inf:
                self.tls_ca_cert = inf.read()
        if not self.client_cert and self.client_cert_path:
            with open(self.client_cert_path, 'rb') as inf:
                self.client_cert = inf.read()
        if not self.client_key and self.client_key_path:
            with open(self.client_key_path, 'rb') as inf:
                self.client_key = inf.read()

        opts = [
            ("grpc.ssl_target_name_override", self.ssl_target_name)
        ] if self.ssl_target_name else []

        # pylint: disable=attribute-defined-outside-init
        # Create GRPC channel
        if self.tls_ca_cert:
            # Add client credentials if available
            if self.client_cert and self.client_key:
                creds = aiogrpc.ssl_channel_credentials(
                    self.tls_ca_cert,
                    private_key=self.client_key,
                    certificate_chain=self.client_cert
                )
            else:
                creds = aiogrpc.ssl_channel_credentials(self.tls_ca_cert)
            # Create secure channel
            self._grpc_channel = aiogrpc.secure_channel(
                self.endpoint, creds, opts
            )
        else:
            # Create insecure channel if no cert
            self._grpc_channel = aiogrpc.insecure_channel(self.endpoint, opts)
        # pylint: enable=attribute-defined-outside-init


@dataclass()
class Peer(_ConnectedModel):
    """ A model to represent a Hyperledger Fabric Peer """
    name: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        # pylint: disable=attribute-defined-outside-init
        self.endorser = EndorserStub(self._grpc_channel)
        self.discovery = DiscoveryStub(self._grpc_channel)
        self.deliver = DeliverStub(self._grpc_channel)
        # pylint: enable=attribute-defined-outside-init




@dataclass()
class Orderer(_ConnectedModel):
    """ A model to represent a Hyperledger Fabric Orderer """
    name: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        # pylint: disable=attribute-defined-outside-init
        self.broadcaster = AtomicBroadcastStub(self._grpc_channel)
        self.deliver = AtomicBroadcastStub(self._grpc_channel)
        # pylint: enable=attribute-defined-outside-init


@dataclass
class Channel(BaseModel):
    """ A model to represent a Hyperledger Fabric Channel """
    name: str


@dataclass()
class ChaincodeSpec(BaseModel):
    """ A model to specify metadata about a Hyperledger Fabric chaincode
        package
    """
    name: Optional[str] = None
    version: Optional[str] = None
    language: ChaincodeLanguage = ChaincodeLanguage.GOLANG
    path: Optional[str] = None
    args: Optional[List[str]] = None
    endorsement_policy: Optional['EndorsementPolicy'] = None


@dataclass(unsafe_hash=True)
class EndorsementPolicyRole(BaseModel):
    """ A role specified for an EndorsementPolicy"""
    msp: str
    role: str

    def __post_init__(self):
        self.role = self.role.lower()


@dataclass()
class EndorsementPolicy(BaseModel):
    """ A structured object to represent a Hyperledger Fabric endorsement
        policy
    """

    expr: PolicyExpression
    out_of: Optional[int] = None
    roles: List[EndorsementPolicyRole] = field(default_factory=list)
    sub_policies: List['EndorsementPolicy'] = field(default_factory=list)

    @property
    def all_roles(self):
        """ A recursive list of all roles defined in this endorsement policy """
        roles = set(self.roles)
        for policy in self.sub_policies: # pylint: disable=not-an-iterable
            roles |= set(policy.all_roles)
        return sorted(roles, key=lambda r: f'{r.msp}.{r.role}')

    @property
    def role_map(self):
        """ A map of role and an int id for all roles in the endorsement
            policy
        """
        return {role: idx for idx, role in enumerate(self.all_roles)}
