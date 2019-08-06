"""
    Models to represent Hyperledger Fabric transactions at various points
    in the transaction lifecycle
"""

from dataclasses import dataclass
from typing import List, Optional

from ..protos.common.common_pb2 import Header
from ..protos.msp.identities_pb2 import SerializedIdentity
from ..protos.peer.proposal_response_pb2 import ProposalResponse
from ..protos.peer.proposal_pb2 import Proposal, SignedProposal
from ..protos.peer.transaction_pb2 import TxValidationCode
from ..protos.peer.events_pb2 import (
    FilteredTransaction as FilteredTXProto,
    FilteredTransactionActions,
)

from ..constants import TransactionType

from ._decoded import DecodedTX # pylint: disable=unused-import


@dataclass()
class TXContext:
    """ Contextual information about a Hyperledger Fabric transaction """
    identity: SerializedIdentity
    nonce: str
    tx_id: str
    epoch: int = 0


@dataclass()
class EndorsedTX:
    """ A model to represent a transaction that has been sent out for proposal
        to peers, and returned with endorsements
    """
    peer_responses: List[ProposalResponse]
    proposal: Proposal
    header: Header
    tx_context: TXContext

    @property
    def response_payload(self):
        """ Gets the response payload from the first valid peer response,
            decoded that response into a string. If there are no valid peer
            responses, this will raise an error
        """
        for resp in self.peer_responses:
            if resp.response.status == 200:
                return resp.response.payload.decode('utf-8')
        raise ValueError(
            'Could not find a response payload in any of the peer responses'
        )

    @property
    def tx_id(self):
        """ The unique identifier for this transaction """
        return self.tx_context.tx_id


@dataclass()
class GeneratedTX:
    """ A model to represent a transaction that has been generated but not
        yet sent for endorsement
    """

    # The transaction context used to generate this proposal
    tx_context: TXContext

    # The unsigned full proposal (without any transient data)
    proposal: Proposal

    # The signed proposal which will be sent to peers for endorsement
    signed_proposal: SignedProposal

    # The transaction header
    header: Header

    @property
    def tx_id(self):
        """ The unique identifier for this transaction """
        return self.tx_context.tx_id


@dataclass()
class FilteredTX:
    """ A model to represent filtered transaction data return from a peer's
        event hub
    """

    tx_id: str
    type: TransactionType
    tx_validation_code: TxValidationCode
    actions: Optional[FilteredTransactionActions] = None

    @classmethod
    def from_proto(cls, filtered_tx: FilteredTXProto) -> 'FilteredTX':
        """ Build from protobuf  """
        return cls(
            tx_id=filtered_tx.txid,
            type=TransactionType(filtered_tx.type),
            tx_validation_code=filtered_tx.tx_validation_code,
            actions=filtered_tx.transaction_actions
        )
