"""
    Configures pytest
"""

import pytest

from snakeskin.protos.common.common_pb2 import (
    BlockHeader,
    BlockData,
    BlockMetadata
)
from snakeskin.models.block import RawBlock
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
def org1_user():
    """ User with Org1 MSP """
    yield User(
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
