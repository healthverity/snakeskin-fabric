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

from snakeskin.models.block import RawBlock, FilteredBlock

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


def test_raw_block_decode(genesis_block):
    """ Tests RawBlock().decode """
    assert genesis_block.decode()


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


def test_decode_block_transactions(genesis_block):
    """ Tests DecodedBlock().transactions """
    assert len(genesis_block.decode().transactions) == 1
