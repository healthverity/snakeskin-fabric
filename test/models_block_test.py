"""
    Tests for the models.block module
"""

from unittest.mock import patch

from snakeskin.protos.common.common_pb2 import (
    BlockHeader,
    BlockData,
    BlockMetadata,
    Block,
    HeaderType,
)

from snakeskin.protos.peer.events_pb2 import (
    FilteredBlock as FilteredBlockProto,
    FilteredTransaction,
    FilteredTransactionActions
)
from snakeskin.protos.peer.transaction_pb2 import (
    TxValidationCode
)

from snakeskin.models.block import RawBlock, DecodedBlock, FilteredBlock

def test_raw_block_from_proto(raw_block):
    """ Tests RawBlock.from_proto() """
    proto_block = Block(
        header=BlockHeader(
            number=5,
            previous_hash=b'12345',
            data_hash=b'234567'
        ),
        data=BlockData(
            data=[b'']
        ),
        metadata=BlockMetadata(
            metadata=[b'']
        )
    )
    assert RawBlock.from_proto(proto_block) == raw_block


def test_raw_block_transactions(raw_block):
    """ Tests RawBlock().transactions """
    assert raw_block.transactions == [b'']


@patch.object(DecodedBlock, 'decode')
def test_raw_block_decode(db_decode, raw_block):
    """ Tests RawBlock().transactions """
    assert raw_block.decode() == db_decode.return_value
    db_decode.assert_called_with(raw_block)


def test_raw_block_as_proto(raw_block):
    """ Tests RawBlock().as_proto """
    proto_block = Block(
        header=BlockHeader(
            number=5,
            previous_hash=b'12345',
            data_hash=b'234567'
        ),
        data=BlockData(
            data=[b'']
        ),
        metadata=BlockMetadata(
            metadata=[b'']
        )
    )
    assert raw_block.as_proto() == proto_block


@patch('snakeskin.models.block.FilteredTX.from_proto')
def test_filt_block_from_proto(tx_from_proto):
    """ Tests FilteredBlock.from_proto """
    ftx = FilteredTransaction(
        txid=b'123',
        type=HeaderType.MESSAGE,
        tx_validation_code=TxValidationCode.VALID,
        transaction_actions=FilteredTransactionActions(
            chaincode_actions=[]
        )
    )
    proto_block = FilteredBlockProto(
        channel_id='somechannel',
        number=10,
        filtered_transactions=[ftx]
    )
    assert FilteredBlock.from_proto(proto_block) == FilteredBlock(
        channel_id='somechannel',
        number=10,
        transactions=[tx_from_proto.return_value]
    )
    tx_from_proto.assert_called_with(ftx)
