"""
    Tests for errors module
"""

from unittest.mock import Mock, patch

import pytest
import grpc

from snakeskin.protos.orderer.ab_pb2 import BroadcastResponse
from snakeskin.protos.common.common_pb2 import Status
from snakeskin.protos.peer.proposal_response_pb2 import ProposalResponse, Response
from snakeskin.protos.peer.transaction_pb2 import TxValidationCode
from snakeskin.models.transaction import EndorsedTX, TXContext
from snakeskin.errors import (
    TrasactionCommitError,
    TransactionProposalError,
    BlockRetrievalError,
    TransactionError,
    BlockchainConnectionError,
    TransactionValidationError,
    handle_conn_errors
)


class _MockConnError(grpc.RpcError):
    """ GRPC has an error subclass that it raises on connection errors. It's
        not accessible via stable imports, so we mock it instead.
    """

    @staticmethod
    def code():
        """ Error code """
        return 5

    @staticmethod
    def details():
        """ Error details """
        return 'some details'


def test_tx_error_abstract():
    """ Tests that the TransactionError can not be used directly """
    with patch.object(TransactionError, 'status'):
        with pytest.raises(NotImplementedError):
            TransactionError('123', '456')
    with pytest.raises(NotImplementedError):
        TransactionError('123', '456')


def test_tx_commit_error_msg():
    """ Tests for TransactionCommitError message """
    resp = BroadcastResponse(
        status=Status.FORBIDDEN,
        info='someinfo'
    )
    error_msg = str(TrasactionCommitError('Failed to commit', '123', resp))
    assert error_msg == 'Failed to commit for tx 123 (status: 403): someinfo'


def test_tx_prop_error_msg():
    """ Tests for TransactionProposalError message """
    endorsed_tx = EndorsedTX(
        peer_responses=[
            ProposalResponse(
                response=Response(
                    status=500,
                    message='tx failed'
                )
            )
        ],
        proposal=Mock(),
        header=Mock(),
        tx_context=TXContext(
            identity=Mock(),
            nonce=b'',
            tx_id='123',
        )
    )
    error_msg = str(TransactionProposalError('uh oh', endorsed_tx))
    assert error_msg == 'uh oh for tx 123 (status: 500): tx failed'


def test_tx_prop_no_err():
    """ Tests for TransactionProposalError if no error responses """
    endorsed_tx = EndorsedTX(
        peer_responses=[],
        proposal=Mock(),
        header=Mock(),
        tx_context=TXContext(
            identity=Mock(),
            nonce=b'',
            tx_id='123',
        )
    )
    error_msg = str(TransactionProposalError('uh oh', endorsed_tx))
    assert error_msg == 'uh oh for tx 123 (status: 0): <no error message>'


def test_block_retreival_error_msg():
    """ Tests for BlockRetrievalError message """
    error_msg = str(BlockRetrievalError(msg='123', status=Status.FORBIDDEN))
    assert error_msg == '123: status (403)'


def test_bc_conn_err_msg():
    """ Tests for BlockchainConnectionError message """
    rpc_err_call = Mock()
    rpc_err_call.code.return_value = 'E123'
    rpc_err_call.details.return_value = 'Bad conn'

    error_msg = str(BlockchainConnectionError(rpc_err_call))
    assert error_msg == 'Blockchain communication failure (E123): Bad conn'


def test_tx_validation_err_msg():
    """ Tests for TransactionValidationError message """

    error_msg = str(TransactionValidationError(TxValidationCode.BAD_PAYLOAD))
    assert error_msg == (
        'Transaction failed validations, with the following code: BAD_PAYLOAD'
    )


def test_handle_conn_errs():
    """ Tests handle_conn_errors """
    with pytest.raises(BlockchainConnectionError):
        with handle_conn_errors():
            raise _MockConnError()
