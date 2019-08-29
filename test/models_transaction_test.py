"""
    Tests for the models.transaction module
"""


from dataclasses import replace

import pytest

from snakeskin.protos.common.common_pb2 import HeaderType

from snakeskin.protos.peer.events_pb2 import (
    FilteredTransaction as FilteredTXProto,
    FilteredTransactionActions
)
from snakeskin.protos.peer.transaction_pb2 import TxValidationCode
from snakeskin.protos.msp.identities_pb2 import SerializedIdentity
from snakeskin.protos.common.common_pb2 import Header
from snakeskin.protos.peer.proposal_pb2 import Proposal, SignedProposal

from snakeskin.protos.peer.proposal_response_pb2 import ProposalResponse, Response

from snakeskin.models.transaction import (
    EndorsedTX, GeneratedTX, TXContext, FilteredTX
)
from snakeskin.constants import TransactionType


@pytest.fixture(name='generated_tx', scope='function')
def _get_generated_tx():
    yield GeneratedTX(
        header=Header(),
        proposal=Proposal(),
        signed_proposal=SignedProposal(),
        tx_context=TXContext(
            identity=SerializedIdentity(),
            nonce=b'',
            tx_id='234567',
            epoch=0
        )
    )

@pytest.fixture(name='endorsed_tx', scope='function')
def _get_endorsed_tx():
    yield EndorsedTX(
        peer_responses=[
            ProposalResponse(
                response=Response(status=200, payload=b'abc'),
            ),
            ProposalResponse(
                response=Response(status=500, payload=b'err'),
            )
        ],
        header=Header(),
        proposal=Proposal(),
        tx_context=TXContext(
            identity=SerializedIdentity(),
            nonce=b'',
            tx_id='123456',
            epoch=0
        )
    )


def test_endtx_resp_payload(endorsed_tx):
    """ Tests EndorsedTX().response_payload property """
    assert endorsed_tx.response_payload == b'abc'


def test_endtx_resp_payload_err(endorsed_tx):
    """ Tests EndorsedTX().response_payload property """
    with pytest.raises(ValueError, match='Could not find a response payload'):
        etx = replace(endorsed_tx, peer_responses=[])
        etx.response_payload # pylint: disable=pointless-statement


def test_endtx_error_resp(endorsed_tx):
    """ Tests EndorsedTX().error_responses yields all error responses """
    assert list(endorsed_tx.error_responses) == [
        ProposalResponse(response=Response(status=500, payload=b'err'))
    ]


def test_endtx_success_resp(endorsed_tx):
    """ Tests EndorsedTX().success_responses yields all success responses """
    assert list(endorsed_tx.success_responses) == [
        ProposalResponse(response=Response(status=200, payload=b'abc'))
    ]


def test_endtx_fully_end(endorsed_tx):
    """ Tests EndorsedTX().fully_endorsed true """
    endorsed_tx = replace(
        endorsed_tx,
        peer_responses=endorsed_tx.success_responses
    )
    assert endorsed_tx.fully_endorsed is True


def test_endtx_not_fully_end(endorsed_tx):
    """ Tests EndorsedTX().fully_endorsed false """
    assert endorsed_tx.fully_endorsed is False


def test_endtx_tx_id(endorsed_tx):
    """ Tests EndorsedTX().tx_id """
    assert endorsed_tx.tx_id == '123456'


def test_gen_tx_tx_id(generated_tx):
    """ Tests GeneratedTX().tx_id """
    assert generated_tx.tx_id == '234567'


def test_filt_tx_from_proto():
    """ Tests FilteredTX.from_proto """
    proto = FilteredTXProto(
        txid='09876',
        type=HeaderType.MESSAGE,
        tx_validation_code=TxValidationCode.VALID,
        transaction_actions=FilteredTransactionActions()
    )
    print(proto.transaction_actions)
    assert FilteredTX.from_proto(proto) == FilteredTX(
        tx_id='09876',
        type=TransactionType.Message,
        tx_validation_code=TxValidationCode.VALID,
        actions=FilteredTransactionActions()
    )


def test_decoded_tx_decode(channel_tx):
    """ Tests DecodedTX().decode """
    assert channel_tx


def test_decoded_tx_tx_id(genesis_block):
    """ Tests DecodedTX().tx_id property """
    assert genesis_block.decode().transactions[0].tx_id == (
        'f0e9c28f528210b234dd613fa5ed20fa49082df15e96ad35590080ae3d357c5d'
    )
