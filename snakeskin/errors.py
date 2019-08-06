"""
    HLF Blockchain errors
"""

import sys
from functools import wraps

import grpc # type: ignore

from .protos.peer.proposal_response_pb2 import ProposalResponse
from .protos.peer.transaction_pb2 import TxValidationCode
from .protos.common.common_pb2 import Status
from .protos.orderer.ab_pb2 import BroadcastResponse
from .models.transaction import TXContext

class BlockchainError(Exception):
    """ Generic blockhchain exception """


class TransactionError(BlockchainError):
    """ A abstract exception class for failures in committing a blockchain
        transaction
    """

    def __init__(self, msg: str, tx_context: TXContext):
        super().__init__(
            f'{msg} for tx {tx_context.tx_id} '
            f'(status: {self.status}): {self.response_message}'
        )


    @property
    def response_message(self) -> str:
        """ The error message of the response """
        raise NotImplementedError

    @property
    def status(self) -> int:
        """ The response status of the error """
        raise NotImplementedError


class TrasactionCommitError(TransactionError):
    """ An exception class for failures when broadcasting a transaction to
        the orderer
    """

    def __init__(self, msg: str, tx_context: TXContext,
                 response: BroadcastResponse):
        self.response = response
        super().__init__(msg, tx_context)

    @property
    def response_message(self) -> str:
        return self.response.info

    @property
    def status(self) -> Status:
        return self.response.status


class TransactionProposalError(TransactionError):
    """ An exception class for failures in generating a proposal on a peer """

    def __init__(self, msg: str, tx_context: TXContext,
                 response: ProposalResponse):
        self.response = response
        super().__init__(msg, tx_context)

    @property
    def response_message(self) -> str:
        return self.response.response.message

    @property
    def status(self) -> int:
        return self.response.response.status


class BlockRetrievalError(BlockchainError):
    """ An exception class for failures when delivering a block from
        the orderer
    """

    def __init__(self, msg: str, status: Status):
        self.status = status
        super().__init__(
            f'{msg}: status ({status})'
        )


class BlockchainConnectionError(BlockchainError, ConnectionError):
    """ An exception class for blockchain connection errors """

    def __init__(self, rpc_error_call):
        self.code = rpc_error_call.code()
        self.details = rpc_error_call.details()
        super().__init__(
            f'Blockchain communication failure ({self.code}): {self.details}'
        )


class TransactionValidationError(BlockchainError):
    """ An exception class for a transactions that failed to commit to the blockchain """

    def __init__(self, code: TxValidationCode):
        self.code = code
        super().__init__(
            'Transaction failed validations, with the following code: '
            f'{self.code_name}'
        )

    @property
    def code_name(self):
        """ The human-readable name of the validation code """
        return TxValidationCode.Name(self.code)



def handle_conn_errors(func):
    """ A decorator function for catching all gRPC errors and re-raising them
        to blockchain connection errors
    """

    @wraps(func)
    async def _wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except grpc.RpcError as rpc_error_call:
            traceback = sys.exc_info()[2]
            conn_error = BlockchainConnectionError(rpc_error_call)
            raise BlockchainConnectionError.with_traceback(
                conn_error, traceback
            )

    return _wrapper
