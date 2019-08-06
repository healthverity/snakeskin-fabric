"""
    Constants defined for HLF blockchain
"""

import sys
from enum import Enum


class ChaincodeLanguage(Enum):
    """ Available chaincode languages """

    GOLANG: str = 'GOLANG'
    JAVA: str = 'JAVA'
    NODE: str = 'NODE'


class PolicyExpression(Enum):
    """ Endorsement Policy expressions """

    And: str = 'AND'
    Or: str = 'OR' # pylint: disable=invalid-name
    OutOf: str = 'NOf'


class PolicyRole(Enum):
    """ Endorsement Policy roles """
    Peer: str = 'PEER'
    Member: str = 'MEMBER'
    Admin: str = 'ADMIN'
    Client: str = 'CLIENT'


class ChaincodeProposalType(Enum):
    """ Chaincode Proposal Type """
    Install: str = 'install'
    Instantiate = 'deploy'
    Invoke = 'invoke'
    Upgrade = 'upgrade'
    Query = 'query'


class TransactionType(Enum):
    """ Types for decoded blocks data """
    # Used for messages which are signed but opaque
    Message = 0
    # Used for messages which express the channel config
    Config = 1
    # Used for transactions which update the channel config
    ConfigUpdate = 2
    # Used by the SDK to submit endorser based transactions
    EndorserTransaction = 3
    # Used internally by the orderer for management
    OrdererTransaction = 4
    # Used as the type for Envelope messages submitted to instruct the Deliver API to seek
    DeliverSeekInfo = 5
    # Used for packaging chaincode artifacts for install
    ChaincodePackage = 6
    # Used for invoking an administrative operation on a peer
    PeerAdminOperation = 8
    # Used to denote transactions that invoke token management operations
    TokenTransaction = 9


class SeekBehavior(Enum):
    """ A strategy for pulling blocks from the peer """

    # Wait until the next block is ready
    BlockUntilReady = 'BLOCK_UNTIL_READY'
    # Fail out if the next block is not ready
    FailIfNotReady = 'FAIL_IF_NOT_READY'


class DeliveredBlockType(Enum):
    """ A strategy for pulling blocks from the peer """

    # Deliver the original protobuf block object
    Original = 'ORIGINAL'
    # Deliver block data, decoded into a structured object
    Decoded = 'DECODED'
    # Deliver filtered block protobuf object
    Filtered = 'FILTERED'


INDEFINITE_STOP_POSITION = sys.maxsize
