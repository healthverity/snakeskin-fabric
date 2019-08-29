"""
    End-to-end tests
"""


import asyncio
from time import sleep
from subprocess import check_output

import pytest
from snakeskin.config import BlockchainConfig
from snakeskin.operations import query_installed_chaincodes
from snakeskin.events import OrdererEvents
from snakeskin.models import Channel


@pytest.yield_fixture(scope='session')
def event_loop():
    """ Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope='session', name='docker_network', autouse=True)
def dc_up():
    """ Loads docker network """
    check_output(['docker-compose', 'down', '-v'])
    check_output(['docker-compose', 'up', '-d'])
    yield
    check_output(['docker-compose', 'down', '-v'])


@pytest.fixture(scope='session', name='network_config')
def load_network_config():
    """ Configuration for the network """
    return BlockchainConfig.from_file('network-config/network-config.yaml')


@pytest.fixture(scope='session', name='gateway')
async def load_example_gateway(network_config, docker_network):
    """ Loads the `example-gw` Gateway """

    gateway = network_config.get_gateway('example-gw')

    await asyncio.gather(
        *(
            _wait_for_orderer(orderer=o, requestor=gateway.requestor)
            for o in gateway.orderers
        ),
        *(
            _wait_for_peer(peer=p, requestor=gateway.requestor)
            for p in gateway.endorsing_peers
        ),
    )
    return gateway



@pytest.fixture(autouse=True, scope='session', name='channel')
async def create_channel(gateway):
    """ Creates the channel in the default gateway """
    await gateway.create_channel(tx_file_path='network-config/channel.tx')
    await gateway.join_channel()
    return gateway.channel


@pytest.fixture(autouse=True, scope='session', name='chaincode')
async def deploy_chaincode(channel, gateway):
    await gateway.install_chaincode()
    await gateway.instantiate_chaincode()



async def _wait_for_orderer(requestor, orderer):
    sleep_time = .5
    for i in range(30):
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
        sleep(sleep_time)
    raise TimeoutError('Timed out waiting for orderer to come on-line')


async def _wait_for_peer(requestor, peer):
    sleep_time = .5
    for i in range(30):
        try:
            await query_installed_chaincodes(requestor, peer)
            return
        except ConnectionError:
            pass
        sleep(sleep_time)
    raise TimeoutError('Timed out waiting for peer to come on-line')
