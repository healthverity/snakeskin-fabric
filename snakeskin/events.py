"""
    Peer event hub connection
"""

import asyncio
from typing import AsyncIterator, Generic, TypeVar

from .protos.common.common_pb2 import Envelope
from .protos.peer.transaction_pb2 import TxValidationCode

from .models import Channel, Peer, User, Orderer
from .models.transaction import FilteredTX, DecodedTX
from .models.block import RawBlock, FilteredBlock

from .errors import (
    BlockRetrievalError,
    TransactionValidationError,
    handle_conn_errors
)
from .factories import (
    tx_context_from_user,
    build_envelope,
    build_seek_info,
    build_envelope_stream
)
from .constants import SeekBehavior, INDEFINITE_STOP_POSITION


BlockType = TypeVar('BlockType')
TXType = TypeVar('TXType')

class _EventHub(Generic[BlockType, TXType]):
    """ An event hub attached to the provided peer """

    def __init__(self,
                 requestor: User,
                 channel: Channel):
        self.requestor = requestor
        self.channel = channel

    async def get_transaction(self,
                              tx_id: str,
                              start: int = None,
                              behavior: SeekBehavior = SeekBehavior.BlockUntilReady
                             ) -> TXType:
        """ Gets a transaction by it's ID from the event stream. Note that """
        async for block in self.stream_blocks(start=start, behavior=behavior):
            for transaction in block.trasactions:
                if transaction.tx_id == tx_id:
                    return transaction
        raise RuntimeError('Could not get transaction')

    @handle_conn_errors
    async def stream_blocks(self,
                            start: int = None,
                            stop: int = INDEFINITE_STOP_POSITION,
                            behavior: SeekBehavior = SeekBehavior.BlockUntilReady
                           ) -> AsyncIterator[BlockType]:
        """ Stream blocks from the peer """
        envelope = self._get_connection_envelope(
            start=start,
            stop=stop,
            behavior=behavior
        )

        stream = self._build_stream(build_envelope_stream(envelope))

        async for resp in await stream:
            if resp.status:
                raise BlockRetrievalError(
                    'Failed to retrieve block',
                    status=resp.status,
                )
            yield resp.block

    def _get_connection_envelope(self,
                                 behavior: SeekBehavior = SeekBehavior.BlockUntilReady,
                                 start: int = None,
                                 stop: int = INDEFINITE_STOP_POSITION
                                ) -> Envelope:
        """
            Builds an envelope that will be sent to the peer to initiate
            streaming events
        """
        seek_info = build_seek_info(start=start, stop=stop, behavior=behavior)

        return build_envelope(
            requestor=self.requestor,
            tx_context=tx_context_from_user(self.requestor),
            channel=self.channel,
            data=seek_info.SerializeToString(),
            tls_cert=self._client_cert,

        )

    @handle_conn_errors
    def _build_stream(self, envelope: Envelope):
        raise NotImplementedError

    @property
    def _client_cert(self):
        raise NotImplementedError


class _PeerEventHub(_EventHub[BlockType, TXType]):
    """ A generic event hub for peer events """

    def __init__(self,
                 requestor: User,
                 channel: Channel,
                 peer: Peer):
        self.peer = peer
        super().__init__(
            requestor=requestor,
            channel=channel,
        )

    @property
    def _client_cert(self):
        return self.peer.client_cert

    @handle_conn_errors
    def _build_stream(self, envelope: Envelope):
        raise NotImplementedError


class PeerEvents(_EventHub[RawBlock, DecodedTX]):
    """ Streams blocks from the peer """

    def __init__(self,
                 requestor: User,
                 channel: Channel,
                 peer: Peer):
        self.peer = peer
        super().__init__(
            requestor=requestor,
            channel=channel,
        )

    @property
    def _client_cert(self):
        return self.peer.client_cert

    @handle_conn_errors
    def _build_stream(self, envelope):
        return self.peer.deliver.Deliver(envelope)



class PeerFilteredEvents(_EventHub[FilteredBlock, FilteredTX]):
    """ Delivers a streams of blocks from the peer """

    def __init__(self,
                 requestor: User,
                 channel: Channel,
                 peer: Peer):
        self.peer = peer
        super().__init__(
            requestor=requestor,
            channel=channel,
        )

    async def check_transaction(self,
                                tx_id: str,
                                timeout: int = 30,
                                start: int = None,
                                behavior: SeekBehavior = SeekBehavior.BlockUntilReady
                               ) -> FilteredTX:
        """ Checks if the transaction completed successfully, otherwise throw
            an error.
        """
        transaction = await asyncio.wait_for(
            self.get_transaction(tx_id, start=start, behavior=behavior),
            timeout=timeout
        )
        if transaction.tx_validation_code != TxValidationCode.VALID:
            raise TransactionValidationError(transaction.tx_validation_code)
        return transaction

    @property
    def _client_cert(self):
        return self.peer.client_cert

    def _build_stream(self, envelope):
        return self.peer.deliver.DeliverFiltered(envelope)



class OrdererEvents(_EventHub[RawBlock, DecodedTX]):
    """ Delivers a streams of blocks from the orderer """

    def __init__(self,
                 requestor: User,
                 channel: Channel,
                 orderer: Orderer):
        self.orderer = orderer
        super().__init__(
            requestor=requestor,
            channel=channel
        )

    def _build_stream(self, envelope):
        return self.orderer.broadcaster.Deliver(envelope)

    @property
    def _client_cert(self):
        return self.orderer.client_cert
