"""
    Gateways for interacting with the blockchain
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from functools import wraps
from typing import List, Optional, Callable, NoReturn, Awaitable

import yaml
from dacite import from_dict

from ..errors import BlockRetrievalError, BlockchainError
from ..models import Peer, Channel, User, Orderer
from ..models.transaction import EndorsedTX, GeneratedTX, FilteredTX
from ..events import PeerFilteredEvents
from ..tx_flow import (
    generate_cc_tx,
    propose_tx,
    commit_tx,
    raise_tx_proposal_error
)

def _chain_await(await_func):
    @wraps(await_func)
    def _wrapper():
        return await_func().__await__()
    return _wrapper

@dataclass()
class Gateway:
    """ A gateway for accessing the blockchain """

    @classmethod
    def from_file(cls, file_path: str):
        """ Loads gateway config from a static file """
        ext = os.path.splitext(file_path)

        with open(file_path) as inf:
            if ext == '.json':
                return cls.from_dict(**json.load(inf))
            if ext in {'.yaml', '.yml'}:
                return cls.from_dict(yaml.load(inf, Loader=yaml.SafeLoader))

        raise ValueError(
            f'Unrecognized file extension for file {file_path}'
        )

    @classmethod
    def from_dict(cls, value: dict):
        """ Creates a gateway config from a dictionary """
        return from_dict(cls, value)


    endorsing_peers: List[Peer] = field(default_factory=list)
    orderers: List[Orderer] = field(default_factory=list)
    channel: Optional[Channel] = None
    requestor: Optional[User] = None
    cc_name: Optional[str] = None

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
        if not self.cc_name:
            raise ValueError('Must specify name of the chaincode')

        generated_tx = generate_cc_tx(
            requestor=self.requestor,
            cc_name=self.cc_name,
            channel=self.channel,
            fcn=fcn,
            args=args,
            transient_map=transient_map
        )

        return GatewayTXBuilder(
            gateway=self,
            generated_tx=generated_tx
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

    def wait_for_commit(self, raise_errors=True):
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
                            self._endorsed_tx.tx_id
                        )
                    else:
                        self._filtered_tx = await event_hub.get_transaction(
                            self._endorsed_tx.tx_id
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

            if self._endorsed_tx:
                return self._endorsed_tx

        raise BlockchainError(
            'Transaction never proposed'
        )

    def __await__(self) -> EndorsedTX:
        return self._run_operations().__await__()
