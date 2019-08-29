"""
    Tests for the config module
"""

import pytest

from snakeskin.config import BlockchainConfig, GatewayConfig
from snakeskin.models import Peer, Orderer, ChaincodeSpec, Channel
from snakeskin.models.gateway import Gateway

def test_from_file_yaml():
    """ Tests loads file from YAML """
    BlockchainConfig.from_file(
        'network-config/network-config.yaml'
    )

def test_from_file_json():
    """ Tests loads file from JSON """
    BlockchainConfig.from_file(
        'network-config/network-config.json'
    )


def test_bad_file_ext():
    """ Tests unsupported file extension """
    with pytest.raises(ValueError):
        BlockchainConfig.from_file(
            'network-config/genesis.block'
        )


def test_no_names(org1_user):
    """ Tests defaults names to the config key """
    org1_user.name = None
    peer = Peer(endpoint='123')
    orderer = Orderer(endpoint='123')
    chaincode = ChaincodeSpec()
    config = BlockchainConfig(
        peers={'abc': peer},
        orderers={'bcd': orderer},
        chaincodes={'cde': chaincode},
        users={'def': org1_user}
    )
    assert config.get_peer('abc').name == 'abc'
    assert config.get_orderer('bcd').name == 'bcd'
    assert config.get_chaincode('cde').name == 'cde'
    assert config.get_user('def').name == 'def'


def test_no_config_with_name():
    """ Tests getters raise key errors """
    config = BlockchainConfig()
    with pytest.raises(KeyError):
        config.get_peer('abc')
    with pytest.raises(KeyError):
        config.get_orderer('abc')
    with pytest.raises(KeyError):
        config.get_user('abc')
    with pytest.raises(KeyError):
        config.get_chaincode('abc')
    with pytest.raises(KeyError):
        config.get_gateway('abc')


def test_get_gateway(org1_user):
    """ Tests gets gateway by name """
    print(org1_user.name)
    gwc = GatewayConfig(channel='123', requestor='org1_user')
    config = BlockchainConfig(
        gateways={'mygw': gwc},
        users={'org1_user': org1_user}
    )
    assert config.get_gateway('mygw') == Gateway(
        channel=Channel(name='123'),
        requestor=org1_user
    )
