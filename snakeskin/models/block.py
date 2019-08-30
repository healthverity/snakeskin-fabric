"""
    Models to represent Hyperledger Fabric blocks
"""

from dataclasses import dataclass
from typing import List

from ..protos.common.common_pb2 import (
    Block as _Block,
    BlockHeader,
    BlockData,
    BlockMetadata
)
from ..protos.peer.events_pb2 import FilteredBlock as _FilteredBlock

from .transaction import FilteredTX
from ._decoded import DecodedBlock
from ._base import BaseModel


@dataclass()
class RawBlock(BaseModel):
    """
        A raw Hyperledger block object (not decoded), essentially an extension
        of the HyperledgerFabric Block protobuf
    """

    header: BlockHeader
    data: BlockData
    metadata: BlockMetadata

    @classmethod
    def from_proto(cls, block: _Block) -> 'RawBlock':
        """ Builds block from protobuf """
        return cls(
            header=block.header,
            data=block.data,
            metadata=block.metadata,
        )

    @property
    def transactions(self) -> List[bytes]:
        """ A list of transactions in this block as raw bytes """
        return list(self.data.data)

    def decode(self) -> DecodedBlock:
        """ Decodes the internal data of this block and returns a
            DecodeBlock
        """
        return DecodedBlock.decode(self)

    def as_proto(self) -> _Block:
        """ Returns the protobuf version of this block """
        return _Block(
            header=self.header, data=self.data, metadata=self.metadata
        )


@dataclass()
class FilteredBlock(BaseModel):
    """
        The filtered version of a Hyperledger Fabric block that gets returned
        by the peer's event hub, essentially an extension of the
        HyperledgerFabric FilteredBlock protobuf.
    """

    channel_id: str
    number: int
    transactions: List[FilteredTX]

    @classmethod
    def from_proto(cls, filtered_block: _FilteredBlock):
        """ Builds from protobuf """
        return cls(
            channel_id=filtered_block.channel_id,
            number=filtered_block.number,
            transactions=[
                FilteredTX.from_proto(tx)
                for tx in filtered_block.filtered_transactions
            ],
        )
