"""
    Configures pytest
"""

import pytest

from snakeskin.protos.common.common_pb2 import (
    BlockHeader,
    BlockData,
    BlockMetadata,
    Block
)
from snakeskin.models.block import RawBlock
from snakeskin.models.transaction import DecodedTX
from snakeskin.models import User

@pytest.fixture()
def raw_block():
    """ Raw block """
    yield RawBlock(
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

@pytest.fixture()
def genesis_block():
    """ A genesis block """
    with open('network-config/genesis.block', 'rb') as gen_bytes:
        gen_block = RawBlock.from_proto(Block.FromString(gen_bytes.read()))
    yield gen_block


@pytest.fixture()
def channel_tx():
    """ A channel transaction, generated from configtxgen, decoded """
    with open('network-config/channel.tx', 'rb') as chan_bytes:
        trans = DecodedTX.decode(chan_bytes.read())
    yield trans


@pytest.fixture(scope='function')
def org1_user():
    """ User with Org1 MSP """
    yield User(
        name='Org1User',
        msp_id='Org1MSP',
        cert_path=(
            'network-config/crypto/peerOrganizations/org1.com/users/'
            'Admin@org1.com/msp/signcerts/Admin@org1.com-cert.pem'
        ),
        key_path=(
            'network-config/crypto/peerOrganizations/org1.com/users/'
            'Admin@org1.com/msp/keystore/'
            '09ac257cbf389db23b05c93f2acdb94093d8397884d19ca8e6e40a515c1ab34a'
            '_sk'
        )
    )
