"""
    Tests gateway functions
"""

import asyncio
from dataclasses import replace

import pytest

from snakeskin.config import BlockchainConfig
from snakeskin.models import (
    Channel,
    EndorsementPolicy,
    EndorsementPolicyRole
)
from snakeskin.constants import PolicyExpression
from snakeskin.operations import instantiate_chaincode, invoke, install_chaincode
from snakeskin.errors import TransactionValidationError


ALL_ROLES = ['member', 'admin', 'peer']

@pytest.mark.asyncio
async def test_endorsement_policy(network_config: BlockchainConfig,
                                  channel: Channel):
    """ Tests upgrade chaincode """
    chaincode = network_config.get_chaincode('helloworld')
    test_chaincode = replace(chaincode, version='endorsement_policy_test')

    org1_admin = network_config.get_user('org1_admin')
    org2_admin = network_config.get_user('org2_admin')
    orderer = network_config.get_orderer('orderer')
    org1_peer = network_config.get_peer('org1_peer')
    org2_peer = network_config.get_peer('org2_peer')
    both_peers = [org1_peer, org2_peer]

    # This policy requires endorsement by any role in org1 AND any role in org2
    policy = EndorsementPolicy(
        expr=PolicyExpression.And,
        sub_policies=[
            EndorsementPolicy(
                expr=PolicyExpression.Or,
                roles=[
                    EndorsementPolicyRole(msp='Org1MSP', role=r)
                    for r in ALL_ROLES
                ]
            ),
            EndorsementPolicy(
                expr=PolicyExpression.Or,
                roles=[
                    EndorsementPolicyRole(msp='Org2MSP', role=r)
                    for r in ALL_ROLES
                ]
            )
        ]
    )

    await asyncio.gather(
        install_chaincode(
            requestor=org1_admin,
            peers=[org1_peer],
            cc_spec=test_chaincode
        ),
        install_chaincode(
            requestor=org2_admin,
            peers=[org2_peer],
            cc_spec=test_chaincode
        )
    )

    await instantiate_chaincode(
        requestor=org1_admin,
        peers=both_peers,
        orderers=[orderer],
        channel=channel,
        cc_spec=test_chaincode,
        endorsement_policy=policy,
        upgrade=True
    )

    with pytest.raises(TransactionValidationError):
        await invoke(
            requestor=org1_admin,
            peers=[org1_peer],
            orderers=[orderer],
            channel=channel,
            cc_name=test_chaincode.name,
            fcn='makeStatement',
            args=['hello!'],
        )

    await invoke(
        requestor=org1_admin,
        peers=[org1_peer, org2_peer],
        orderers=[orderer],
        channel=channel,
        cc_name=test_chaincode.name,
        fcn='makeStatement',
        args=['hello!'],
    )
