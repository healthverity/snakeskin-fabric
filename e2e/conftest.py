"""
    End-to-end tests
"""


import asyncio
from time import sleep

import pytest
from subprocess import check_output
from snakeskin.config import BlockchainConfig


@pytest.yield_fixture(scope='session')
def event_loop():
    """ Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope='session', name='docker_network')
def dc_up():
    """ Loads docker network """
    check_output(['docker-compose', 'down', '-v'])
    check_output(['docker-compose', 'up', '-d'])
    sleep(10)
    yield
    # check_output(['docker-compose', 'down', '-v'])


@pytest.fixture(scope='session', name='network_config')
def load_network_config(docker_network):
    """ Configuration for the network """
    return BlockchainConfig.from_file('network-config/network-config.yaml')


@pytest.fixture(scope='session', name='gateway')
def load_example_gateway(network_config):
    """ Loads the `example-gw` Gateway """
    return network_config.get_gateway('example-gw')


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
