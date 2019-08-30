"""
    Tests gateway functions
"""

import pytest

@pytest.mark.asyncio
async def test_gateway_transact(org1_gw):
    """ Tests Gateway.transact() """
    await org1_gw.transact(
        fcn='makeStatement',
        args=['hello!'],
    ).propose().submit().wait_for_commit()


@pytest.mark.asyncio
async def test_query_inst_chaincodes(org1_gw):
    """ Tests querying instantiated chaincodes """
    res = await org1_gw.query_instantiated_chaincodes()
    assert res.chaincodes
