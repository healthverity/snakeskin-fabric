"""
    Tests for the models.gateway module
"""

from dataclasses import replace
from unittest.mock import Mock, call

import asynctest
import pytest


from snakeskin.models.gateway import Gateway, GatewayTXBuilder
from snakeskin.models import Peer, Orderer, Channel, ChaincodeSpec
from snakeskin.errors import BlockchainError

CHANNEL = Channel(name='notarealchannel')


class AwaitableMock(asynctest.CoroutineMock):
    """ Mocks out a class that implements an __await__ method """

    async def _do_await(self):
        return await self()

    def __await__(self):
        return self._do_await().__await__()


@pytest.fixture(name='tx_builder_mock', scope='function')
def _get_tx_builder_mock():
    mock = AwaitableMock()
    mock.propose.return_value = mock
    mock.submit.return_value = mock
    mock.wait_for_commit.return_value = mock

    with asynctest.patch(
            'snakeskin.models.gateway.GatewayTXBuilder',
            autospec=True,
            return_value=mock
    ) as builder_cls:
        yield builder_cls


@pytest.fixture(name='gateway')
def _build_gateway(peer, orderer, org1_user, cc_spec):
    yield Gateway(
        endorsing_peers=[peer],
        orderers=[orderer],
        requestor=org1_user,
        channel=CHANNEL,
        chaincode=cc_spec
    )

@pytest.fixture(name='peer')
def _build_peer():
    yield Peer(endpoint='peer.host.com')


@pytest.fixture(name='orderer')
def _build_orderer():
    yield Orderer(endpoint='orderer.host.com')


@pytest.fixture(name='cc_spec')
def _build_cc_spec():
    yield ChaincodeSpec(name='notarealcc')


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.generate_cc_tx', autospec=True)
async def test_gw_transact(generate_tx, tx_builder_mock, gateway, org1_user, cc_spec):
    """ Tests Gateway().transact """
    await _assert_gw_required(
        gateway,
        lambda gw: gw.transact(fcn='abc'),
        ['channel', 'endorsing_peers', 'requestor', 'chaincode']
    )

    res = gateway.transact(fcn='abc', args=['1', '2'])
    generate_tx.assert_called_with(
        requestor=org1_user,
        cc_name=cc_spec.name,
        channel=CHANNEL,
        fcn='abc',
        args=['1', '2'],
        transient_map=None
    )
    assert res == tx_builder_mock.return_value

    tx_builder_mock.assert_called_with(
        gateway=gateway,
        generated_tx=generate_tx.return_value
    )


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.generate_cc_tx', autospec=True)
async def test_gw_invoke(generate_tx, tx_builder_mock, gateway, org1_user, cc_spec):
    """ Tests Gateway().invoke """

    tx_builder = tx_builder_mock.return_value

    res = await gateway.invoke(fcn='abc', args=['1', '2'], timeout=100)
    generate_tx.assert_called_with(
        requestor=org1_user,
        cc_name=cc_spec.name,
        channel=CHANNEL,
        fcn='abc',
        args=['1', '2'],
        transient_map=None
    )
    assert res == tx_builder.return_value

    tx_builder_mock.assert_called_with(
        gateway=gateway,
        generated_tx=generate_tx.return_value
    )
    tx_builder.propose.assert_called_with()
    tx_builder.submit.assert_called_with()
    tx_builder.wait_for_commit.assert_called_with(timeout=100)
    tx_builder.assert_awaited_once()


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.generate_cc_tx', autospec=True)
async def test_gw_query(generate_tx, tx_builder_mock, gateway, org1_user, cc_spec):
    """ Tests Gateway().query """

    tx_builder = tx_builder_mock.return_value

    res = await gateway.query(fcn='abc', args=['1', '2'])
    generate_tx.assert_called_with(
        requestor=org1_user,
        cc_name=cc_spec.name,
        channel=CHANNEL,
        fcn='abc',
        args=['1', '2'],
        transient_map=None
    )
    assert res == tx_builder.return_value

    tx_builder_mock.assert_called_with(
        gateway=gateway,
        generated_tx=generate_tx.return_value
    )
    tx_builder.propose.assert_called_with()
    tx_builder.submit.assert_not_called()
    tx_builder.assert_awaited_once()


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.create_channel', autospec=True)
async def test_gw_create_channel(create_channel, gateway, org1_user, orderer):
    """ Tests Gateway().create_channel """

    await _assert_gw_required(
        gateway,
        lambda gw: gw.create_channel(tx_file_path='mychannel.tx'),
        ['orderers', 'channel', 'requestor']
    )

    res = await gateway.create_channel(tx_file_path='mychannel.tx')
    create_channel.assert_called_with(
        requestor=org1_user,
        orderers=[orderer],
        channel=CHANNEL,
        tx_file_path='mychannel.tx',
    )
    assert res == create_channel.return_value


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.join_channel', autospec=True)
async def test_gw_join_channel(join_channel, gateway, org1_user, orderer, peer):
    """ Tests Gateway().join_channel """

    await _assert_gw_required(
        gateway, lambda gw: gw.join_channel(), ['channel', 'requestor']
    )

    res = await gateway.join_channel()
    join_channel.assert_called_with(
        requestor=org1_user,
        orderers=[orderer],
        channel=CHANNEL,
        peer=peer
    )
    assert res is None


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.join_channel', autospec=True)
async def test_gw_join_channel_mult(join_channel, gateway, org1_user, orderer, peer):
    """ Tests Gateway().join_channel for multiple peers """

    peer2 = Peer(endpoint='org2peer.com')

    res = await gateway.join_channel(peers=[peer, peer2])
    join_channel.assert_has_calls([
        call(
            requestor=org1_user,
            orderers=[orderer],
            channel=CHANNEL,
            peer=peer
        ),
        call(
            requestor=org1_user,
            orderers=[orderer],
            channel=CHANNEL,
            peer=peer2
        ),
    ])
    assert res is None


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.query_instantiated_chaincodes', autospec=True)
async def test_gw_query_inst_cc(query_cc, gateway, org1_user, peer):
    """ Tests Gateway().query_instantiated_chaincodes """

    await _assert_gw_required(
        gateway, lambda gw: gw.query_instantiated_chaincodes(),
        ['channel', 'requestor', 'endorsing_peers']
    )

    res = await gateway.query_instantiated_chaincodes()
    query_cc.assert_called_with(
        requestor=org1_user,
        channel=CHANNEL,
        peers=[peer]
    )
    assert res == query_cc.return_value


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.install_chaincode', autospec=True)
async def test_gw_install_cc(install_cc, gateway, org1_user, cc_spec, peer):
    """ Tests Gateway().install_chaincode """

    await _assert_gw_required(
        gateway,
        lambda gw: gw.install_chaincode(),
        ['endorsing_peers', 'requestor']
    )

    res = await gateway.install_chaincode()
    install_cc.assert_called_with(
        requestor=org1_user,
        peers=[peer],
        cc_spec=cc_spec
    )
    assert res == install_cc.return_value


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.instantiate_chaincode', autospec=True)
async def test_gw_inst_cc(inst_cc, gateway, org1_user, cc_spec, peer, orderer):
    """ Tests Gateway().instantiate_chaincode """

    await _assert_gw_required(
        gateway,
        lambda gw: gw.instantiate_chaincode(),
        ['requestor', 'chaincode', 'channel', 'endorsing_peers', 'orderers']
    )

    res = await gateway.instantiate_chaincode()
    inst_cc.assert_called_with(
        requestor=org1_user,
        peers=[peer],
        channel=CHANNEL,
        orderers=[orderer],
        cc_spec=cc_spec,
        upgrade=False,
        endorsement_policy=None,
        timeout=30,
    )
    assert res == inst_cc.return_value


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.propose_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.commit_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.PeerFilteredEvents', autospec=True)
async def test_txbuild_chain(event_hub, commit, propose, peer, gateway):
    """ Tests GatewayTxBuilder method chaining """
    generated_tx = Mock()
    tx_builder = GatewayTXBuilder(gateway=gateway, generated_tx=generated_tx)

    res = await tx_builder.propose().submit().wait_for_commit()

    assert res == propose.return_value
    propose.assert_called_with(
        peers=gateway.endorsing_peers,
        generated_tx=generated_tx
    )

    commit.assert_called_with(
        orderers=gateway.orderers,
        endorsed_tx=res,
        requestor=gateway.requestor
    )

    event_hub.assert_called_with(
        requestor=gateway.requestor,
        channel=gateway.channel,
        peer=peer
    )
    event_hub.return_value.check_transaction.assert_called_with(
        res.tx_id, timeout=30
    )


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.propose_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.commit_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.PeerFilteredEvents', autospec=True)
async def test_txbuild_awaits(event_hub, commit, propose, peer, gateway):
    """ Tests GatewayTxBuilder individual method awaits """
    generated_tx = Mock()
    tx_builder = GatewayTXBuilder(gateway=gateway, generated_tx=generated_tx)

    res = await tx_builder.propose()
    assert res == propose.return_value
    propose.assert_called_with(
        peers=gateway.endorsing_peers,
        generated_tx=generated_tx
    )

    await tx_builder.submit()
    commit.assert_called_with(
        orderers=gateway.orderers,
        endorsed_tx=res,
        requestor=gateway.requestor
    )

    await tx_builder.wait_for_commit()
    event_hub.assert_called_with(
        requestor=gateway.requestor,
        channel=gateway.channel,
        peer=peer
    )
    event_hub.return_value.check_transaction.assert_called_with(
        res.tx_id, timeout=30
    )


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.propose_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.commit_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.PeerFilteredEvents', autospec=True)
async def test_txbuild_wait_error_false(event_hub, _, propose, gateway):
    """ Tests GatewayTxBuilder().wait_for_commit(raise_errors=False) """
    generated_tx = Mock()
    tx_builder = GatewayTXBuilder(gateway=gateway, generated_tx=generated_tx)

    res = await tx_builder.propose().submit().wait_for_commit(raise_errors=False)
    assert res == propose.return_value

    event_hub.return_value.get_transaction.assert_called_with(res.tx_id)


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.propose_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.commit_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.PeerFilteredEvents', autospec=True)
async def test_txbuild_bad_chains(_, __, ___, gateway):
    """ Tests GatewayTxBuilder bad chaining """
    generated_tx = Mock()

    # Submit before propose
    with pytest.raises(ValueError, match='Must propose'):
        tx_builder = GatewayTXBuilder(
            gateway=gateway, generated_tx=generated_tx
        )
        await tx_builder.submit().propose().wait_for_commit()

    # Wait for commit before submit
    with pytest.raises(ValueError, match='Must commit'):
        tx_builder = GatewayTXBuilder(
            gateway=gateway, generated_tx=generated_tx
        )
        await tx_builder.wait_for_commit()

    # No operations
    with pytest.raises(BlockchainError, match='Transaction never proposed'):
        tx_builder = GatewayTXBuilder(
            gateway=gateway, generated_tx=generated_tx
        )
        await tx_builder


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.propose_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.commit_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.PeerFilteredEvents', autospec=True)
async def test_txbuild_fail(event_hub, _, __, gateway):
    """ Tests GatewayTxBuilder wait_for_commit raises a connection error if all
        peers fail to receive transaction
    """
    generated_tx = Mock()
    tx_builder = GatewayTXBuilder(gateway=gateway, generated_tx=generated_tx)

    event_hub.return_value.check_transaction.side_effect = ConnectionError(
        'Peer not found'
    )
    with pytest.raises(ConnectionError, match='Peer not found'):
        await tx_builder.propose().submit().wait_for_commit()


@pytest.mark.asyncio
@asynctest.patch('snakeskin.models.gateway.propose_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.commit_tx', autospec=True)
@asynctest.patch('snakeskin.models.gateway.PeerFilteredEvents', autospec=True)
async def test_txbuild_retry_wait(event_hub, _, __, gateway, peer):
    """ Tests GatewayTxBuilder wait_for_commit tries on multiple peers """
    generated_tx = Mock()
    gateway = replace(gateway, endorsing_peers=[peer, peer])
    tx_builder = GatewayTXBuilder(gateway=gateway, generated_tx=generated_tx)

    event_hub.return_value.check_transaction.side_effect = [
        ConnectionError('Peer not found'),
        Mock()
    ]
    await tx_builder.propose().submit().wait_for_commit()



async def _assert_gw_required(gateway, func, fields):
    for field in fields:
        with pytest.raises(ValueError):
            await func(replace(gateway, **{field: None}))
