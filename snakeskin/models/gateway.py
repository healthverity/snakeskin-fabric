"""
    Gateways for interacting with the blockchain
"""

import asyncio
from dataclasses import dataclass, field, replace
from typing import List, Optional, Callable, NoReturn, Awaitable

from ..errors import BlockRetrievalError, BlockchainError
from ..models import (
    Peer, Channel, User, Orderer, ChaincodeSpec, EndorsementPolicy
)
from ..models.transaction import EndorsedTX, GeneratedTX, FilteredTX
from ..events import PeerFilteredEvents
from ..transact import (
    generate_cc_tx,
    propose_tx,
    commit_tx,
    raise_tx_proposal_error
)
from ..operations import (
    create_channel,
    join_channel,
    query_instantiated_chaincodes,
    install_chaincode,
    instantiate_chaincode
)


@dataclass()
class Gateway:
    """ A gateway for accessing the blockchain """

    endorsing_peers: List[Peer] = field(default_factory=list)
    orderers: List[Orderer] = field(default_factory=list)
    channel: Optional[Channel] = None
    requestor: Optional[User] = None
    chaincode: Optional[ChaincodeSpec] = None

    def transact(self,
                 fcn: str,
                 args: Optional[List[str]] = None,
                 transient_map: Optional[dict] = None) -> 'GatewayTXBuilder':
        """ Begins a transaction against the blockchain """
        if not self.endorsing_peers:
            raise ValueError('Must provided at least one endorsing peer')
        if not self.channel:
            raise ValueError('Must specify a channel')
        if not self.requestor:
            raise ValueError('Must specify a requestor')
        if not (self.chaincode and self.chaincode.name):
            raise ValueError('Must specify a chaincode name')

        generated_tx = generate_cc_tx(
            requestor=self.requestor,
            cc_name=self.chaincode.name,
            channel=self.channel,
            fcn=fcn,
            args=args,
            transient_map=transient_map
        )

        return GatewayTXBuilder(
            gateway=self,
            generated_tx=generated_tx
        )

    async def invoke(self,
                     fcn: str,
                     args: Optional[List[str]] = None,
                     transient_map: Optional[dict] = None,
                     timeout: int = 30):
        """ Invokes the chaincode"""

        return await (
            self.transact(
                fcn=fcn, args=args, transient_map=transient_map
            )
            .propose()
            .submit()
            .wait_for_commit(timeout=timeout)
        )

    async def query(self,
                    fcn: str,
                    args: Optional[List[str]] = None,
                    transient_map: Optional[dict] = None):
        """ Invokes the chaincode"""

        return await (
            self.transact(
                fcn=fcn, args=args, transient_map=transient_map
            )
            .propose()
        )

    async def create_channel(self, tx_file_path: str):
        """ Creates a channel from a transaction file that was generated
            using the HLF configtxgen tool
        """
        if not self.orderers:
            raise ValueError('Must provided at least one orderer')
        if not self.channel:
            raise ValueError('Must specify a channel')
        if not self.requestor:
            raise ValueError('Must specify a requestor')

        return await create_channel(
            requestor=self.requestor,
            orderers=self.orderers,
            channel=self.channel,
            tx_file_path=tx_file_path
        )

    async def join_channel(self, peers: List[Peer] = None):
        """
            Joins all provided peers the channel for this gateway.
            If no peers are provided, all endorsing peers are joined to the
            channel.
        """
        if not peers:
            peers = self.endorsing_peers

        if not self.channel:
            raise ValueError('Must specify a channel')
        if not self.requestor:
            raise ValueError('Must specify a requestor')

        for peer in peers:
            await join_channel(
                requestor=self.requestor,
                orderers=self.orderers,
                channel=self.channel,
                peer=peer
            )

    async def query_instantiated_chaincodes(self):
        """
            Queries for instantiated chaincodes across all endorsement peers
            using the channel for this gateway.
        """
        if not self.channel:
            raise ValueError('Must specify a channel')
        if not self.requestor:
            raise ValueError('Must specify a requestor')
        if not self.endorsing_peers:
            raise ValueError('Must specify at least one endorsing peer')

        return await query_instantiated_chaincodes(
            requestor=self.requestor,
            peers=self.endorsing_peers,
            channel=self.channel
        )

    async def install_chaincode(self, peers: Optional[List[Peer]] = None):
        """
            Installs chaincode on all peers for this gateway
        """

        if not peers:
            peers = self.endorsing_peers

        if not self.requestor:
            raise ValueError('Must specify a requestor')
        if not peers:
            raise ValueError('Must specify at least one peer')
        if not self.chaincode:
            raise ValueError('Must specify chaincode')

        return await install_chaincode(
            requestor=self.requestor,
            peers=peers,
            cc_spec=self.chaincode,
        )

    async def instantiate_chaincode(self,
                                    endorsement_policy: EndorsementPolicy = None,
                                    upgrade: bool = False,
                                    timeout: int = 30):
        """
            Installs chaincode on all peers for this gateway
        """
        if not self.requestor:
            raise ValueError('Must specify a requestor')
        if not self.channel:
            raise ValueError('Must specify a channel')
        if not self.endorsing_peers:
            raise ValueError('Must specify at least one endorsing peer')
        if not self.orderers:
            raise ValueError('Must specify at least one orderer')
        if not self.chaincode:
            raise ValueError('Must specify chaincode')

        return await instantiate_chaincode(
            requestor=self.requestor,
            peers=self.endorsing_peers,
            orderers=self.orderers,
            channel=self.channel,
            cc_spec=self.chaincode,
            upgrade=upgrade,
            endorsement_policy=endorsement_policy,
            timeout=timeout,
        )

    def update_chaincode_version(self, version: str):
        """ Updates the chaincode version and returns a new gateway """
        return replace(
            self,
            chaincode=replace(
                self.chaincode,
                version=version
            )
        )


_Operation = Callable[[], Awaitable[NoReturn]]

class GatewayTXBuilder:
    """ A transaction object that was generated from a gateway """


    def __init__(self,
                 gateway: Gateway,
                 generated_tx: GeneratedTX):
        self.transaction = generated_tx
        self._gateway = gateway
        self._endorsed_tx: Optional[EndorsedTX] = None
        self._filtered_tx: Optional[FilteredTX] = None
        self._committed = False
        self._operations: Optional[List[_Operation]] = None

    def propose(self, raise_errors=True):
        """ Send the transaction to all endorsing peers for endorsement """
        async def _operate():
            self._endorsed_tx = await propose_tx(
                peers=self._gateway.endorsing_peers,
                generated_tx=self.transaction,
            )
            if raise_errors:
                raise_tx_proposal_error(
                    self._endorsed_tx,
                    'A peer failed to endorse the transaction'
                )
        self._add_operation(_operate)
        return self

    def submit(self):
        """ Submits the transaction to the orderer for committing """
        async def _operate():
            if not self._endorsed_tx:
                raise ValueError(
                    'Must propose transaction before committing it'
                )
            await commit_tx(
                requestor=self._gateway.requestor,
                orderers=self._gateway.orderers,
                endorsed_tx=self._endorsed_tx
            )
            self._committed = True
        self._add_operation(_operate)
        return self

    def wait_for_commit(self, raise_errors=True, timeout: int = 30):
        """ Waits for the transaction to be committed to the peers """

        async def _operate():
            if not self._committed:
                raise ValueError(
                    'Must commit transaction before waiting'
                )

            error = BlockchainError('Failed waiting for committed transaction')
            for peer in self._gateway.endorsing_peers:
                try:
                    event_hub = PeerFilteredEvents(
                        requestor=self._gateway.requestor,
                        channel=self._gateway.channel,
                        peer=peer
                    )
                    if raise_errors:
                        self._filtered_tx = await event_hub.check_transaction(
                            self._endorsed_tx.tx_id,
                            timeout=timeout
                        )
                    else:
                        self._filtered_tx = await asyncio.wait_for(
                            event_hub.get_transaction(self._endorsed_tx.tx_id),
                            timeout=timeout
                        )
                    return
                # Try all peers unless the connection fails
                except (ConnectionError, BlockRetrievalError) as err:
                    error = err

            # Raise the last error
            raise error

        self._add_operation(_operate)
        return self

    def _add_operation(self, operation: _Operation):
        if self._operations:
            self._operations.append(operation)
        else:
            self._operations = [operation]

    async def _run_operations(self):
        if self._operations:
            for operation in self._operations:
                await operation()

            self._operations.clear()

            if self._endorsed_tx:
                return self._endorsed_tx

        raise BlockchainError(
            'Transaction never proposed'
        )

    def __await__(self) -> EndorsedTX:
        return self._run_operations().__await__()
