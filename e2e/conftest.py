"""
    End-to-end tests
"""


import asyncio
from subprocess import check_output

import pytest

from snakeskin.config import BlockchainConfig
from snakeskin.operations import query_installed_chaincodes, query_instantiated_chaincodes
from snakeskin.events import OrdererEvents
from snakeskin.models import Channel


@pytest.yield_fixture(scope='session')
def event_loop():
    """ Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session', name='network_config', autouse=True)
async def prepare_network():
    """ Configuration for the network """
    config = BlockchainConfig.from_file('network-config/network-config.yaml')
    org1_admin = config.get_user('org1_admin')
    org2_admin = config.get_user('org2_admin')
    org1_peer = config.get_peer('org1_peer')
    org2_peer = config.get_peer('org2_peer')
    org1_gw = config.get_gateway('org1_gw')
    org2_gw = config.get_gateway('org2_gw')

    check_output(['docker-compose', 'down', '-v'])
    check_output(['docker-compose', 'up', '-d'])
    await asyncio.wait_for(
        asyncio.gather(
            _wait_for_orderer(org1_admin, config.get_orderer('orderer')),
            _wait_for_peer(org1_admin, org1_peer),
            _wait_for_peer(org2_admin, org2_peer),
        ),
        timeout=40
    )

    await org1_gw.create_channel(tx_file_path='network-config/channel.tx')
    await org1_gw.join_channel(peers=[org1_peer])
    await org2_gw.join_channel(peers=[org2_peer])
    await org1_gw.install_chaincode(peers=[org1_peer])
    await org2_gw.install_chaincode(peers=[org2_peer])
    await org1_gw.instantiate_chaincode()
    channel = org1_gw.channel
    chaincode = org1_gw.chaincode
    await asyncio.wait_for(
        asyncio.gather(
            _wait_for_instantiation(org1_admin, org1_peer, channel, chaincode),
            _wait_for_instantiation(org2_admin, org2_peer, channel, chaincode)
        )
    , timeout=60)

    yield config

    # check_output(['docker-compose', 'down', '-v'])


@pytest.fixture(scope='session', name='org1_gw')
def load_org1_gateway(network_config):
    """ Loads the `org1_gw` Gateway """
    return network_config.get_gateway('org1_gw')


@pytest.fixture(scope='session', name='org2_gw')
def load_org2_gateway(network_config):
    """ Loads the `org2_gw` Gateway """
    return network_config.get_gateway('org2_gw')


@pytest.fixture(scope='session', name='channel')
def get_channel(org1_gw):
    """ Gets channel in default gw """
    yield org1_gw.channel


@pytest.fixture(autouse=True, scope='session', name='chaincode')
def get_chaincode(org1_gw):
    """ Gets chaincode in default gw """
    yield org1_gw.chaincode


async def _wait_for_orderer(requestor, orderer):
    while True:
        try:
            evts = OrdererEvents(
                requestor=requestor,
                orderer=orderer,
                channel=Channel(name='genesis-channel')
            )
            async for _ in evts.stream_blocks():
                return
        except ConnectionError:
            pass


async def _wait_for_peer(requestor, peer):
    while True:
        try:
            await query_installed_chaincodes(requestor, peer)
            return
        except ConnectionError:
            pass


async def _wait_for_instantiation(requestor, peer, channel, chaincode):
    while True:
        resp = await query_instantiated_chaincodes(
            requestor=requestor,
            peers=[peer],
            channel=channel
        )

        for cc_info in resp.chaincodes:
            if (
                    cc_info.name == chaincode.name
                    and cc_info.version == chaincode.version
            ):
                return
