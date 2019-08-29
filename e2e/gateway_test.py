"""
    Tests gateway functions
"""

import pytest

@pytest.mark.asyncio
async def test_gateway_transact(gateway, channel):
    """ Tests Gateway.transact() """
    await gateway.transact(
        fcn='makeStatement',
        args=['hello!'],
    ).propose().submit().wait_for_commit()


@pytest.mark.asyncio
async def test_upgrade_chaincode(gateway):
    """ Tests upgrade chaincode """
    version = 'gateway-upgrade'
    gateway = gateway.update_chaincode_version(version)
    await gateway.install_chaincode()
    await gateway.instantiate_chaincode(upgrade=True)


@pytest.mark.asyncio
async def test_query_inst_chaincodes(gateway):
    """ Tests querying instantiated chaincodes """
    assert await gateway.query_instantiated_chaincodes()
