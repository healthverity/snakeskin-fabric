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
