"""
    Blockchain models
"""
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Mapping, Union, Optional

import aiogrpc # type: ignore

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

@dataclass()
class User:
    """ A model to represent a Hyperledger Fabric User """

    name: str
    msp_id: str
    cert_path: Optional[str] = None
    private_key_path: Optional[str] = None
    cert: Optional[bytes] = None
    private_key: Optional[bytes] = None
    cryptoSuite = field(default_factory=CryptoSuite.default)

    def __post_init__(self):

        if not self.cert:
            if not self.cert_path:
                raise ValueError('Must provide either cert or cert_path')
            with open(self.cert_path, 'rb') as inf:
                self.cert = inf.read()

        if not self.private_key:
            if not self.private_key_path:
                raise ValueError(
                    'Must provide either private_key or private_key_path'
                )
            with open(self.private_key_path, 'rb') as inf:
                self.private_key = inf.read()


@dataclass()
class _ConnectedModel:
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
        ]

        # pylint: disable=attribute-defined-outside-init
        # Create GRPC channel
        if self.tls_ca_cert:
            cred_kwargs = {}
            # Add client credentials if available
            if self.client_cert and self.client_key:
                cred_kwargs.update({
                    'private_key': self.client_key,
                    'certificate_chain': self.client_cert
                })

            # Create secure channel
            creds = aiogrpc.ssl_channel_credentials(
                self.tls_ca_cert, **cred_kwargs
            )
            self._grpc_channel = aiogrpc.secure_channel(
                self.endpoint, creds, opts
            )
        else:
            # Create insecure channel if no cert
            self._grpc_channel = aiogrpc.insecure_channel(self.endpoint, opts)
        # pylint: enable=attribute-defined-outside-init


@dataclass()
class _PeerBase:
    name: str


@dataclass()
class Peer(_ConnectedModel, _PeerBase):
    """ A model to represent a Hyperledger Fabric Peer """

    def __post_init__(self):
        super().__post_init__()
        # pylint: disable=attribute-defined-outside-init
        self.endorser = EndorserStub(self._grpc_channel)
        self.discovery = DiscoveryStub(self._grpc_channel)
        self.deliver = DeliverStub(self._grpc_channel)
        # pylint: enable=attribute-defined-outside-init


@dataclass()
class _OrdererBase:
    name: str


@dataclass()
class Orderer(_ConnectedModel, _OrdererBase):
    """ A model to represent a Hyperledger Fabric Orderer """

    def __post_init__(self):
        super().__post_init__()
        # pylint: disable=attribute-defined-outside-init
        self.broadcaster = AtomicBroadcastStub(self._grpc_channel)
        self.deliver = AtomicBroadcastStub(self._grpc_channel)
        # pylint: enable=attribute-defined-outside-init


@dataclass
class Channel:
    """ A model to represent a Hyperledger Fabric Channel """
    name: str


@dataclass()
class ChaincodeSpec:
    """ A model to specify metadata about a Hyperledger Fabric chaincode
        package
    """
    name: str
    version: Optional[str] = None
    language: ChaincodeLanguage = ChaincodeLanguage.GOLANG
    path: Optional[str] = None
    args: Optional[List[str]] = None


@dataclass(unsafe_hash=True)
class EndorsementPolicyRole:
    """ A role specified for an EndorsementPolicy"""
    msp: str
    role: str

    def __post_init__(self):
        self.role = self.role.lower()


@dataclass()
class EndorsementPolicy:
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
        roles = set()
        for policy in self.sub_policies: # pylint: disable=not-an-iterable
            roles |= set(policy.all_roles)
        return sorted(roles, key=lambda r: f'{r.msp}.{r.role}')

    @property
    def role_map(self):
        """ A map of role and an int id for all roles in the endorsement
            policy
        """
        return {role: idx for idx, role in enumerate(self.all_roles)}
