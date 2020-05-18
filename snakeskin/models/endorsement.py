"""
    Models related to endorsement
"""

from dataclasses import dataclass, field
from collections import Counter
from itertools import cycle
from typing import (
    List, Mapping, NewType, Iterator, Tuple, Set, AsyncIterator, Callable,
    Awaitable
)

from ..protos.peer.proposal_response_pb2 import ProposalResponse
from . import Orderer, Peer, ChaincodeSpec
from ._base import BaseModel


Layout = NewType('Layout', Mapping[str, int])

@dataclass
class PeerGroup(BaseModel):
    """ A named grouping of peers """
    name: str
    peers: List[Peer] = field(default_factory=list)


@dataclass
class EndormentPeerGroup(BaseModel):
    """ A group of peers that should be used to endorse a transaction.

        The `min_count` attribute indicates the minimum number of peers
        in this group that will be required to endorse the transaction.
    """

    min_count: int
    peers: Iterator[Peer]


@dataclass
class EndorsementPeerProvider(BaseModel):
    """ Endorsement configuration that provides groupings of peers that can be
        used for endorsement.

        This can be pre-configured, or retrieved from a peer using service
        discovery.
    """

    groups: List[PeerGroup] = field(default_factory=list)
    layouts: List[Layout] = field(default_factory=list)
    _group_iterators: Mapping[str, Iterator[Peer]] = field(default_factory=dict, init=False)
    _layouts_iterator: Iterator[Layout] = field(init=False)

    def __post_init__(self):
        self._validate_groups()
        self._group_iterators = {
            group.name: cycle(group.peers) for group in self.groups
        }
        self._validate_layouts()
        self._layouts_iterator = cycle(self.layouts)

    def provide_endorsing_groups(self) -> Iterator[Tuple[int, Iterator[Peer]]]:
        """ Provides groups of peers to use when endorsing
         """
        layout = next(self._layouts_iterator) # pylint: disable=stop-iteration-return
        for group_key, peer_count in layout.items():
            peer_iterator = _yield_unique_peers(
                self._group_iterators[group_key]
            )
            yield peer_count, peer_iterator


    def _validate_groups(self):
        counter = Counter([group.name for group in self.groups])
        dups = ''.join(
            name for name, count in counter.items() if count > 1
        )
        if dups:
            raise ValueError(
                f'Duplicate group names found in endorsement config: {dups}'
            )

    def _validate_layouts(self):
        missing_groups = set()
        if not self.layouts:
            raise ValueError('At least one layout required')
        for layout in self.layouts:
            for group in layout:
                if not group in self._group_iterators:
                    missing_groups.add(group)
        if missing_groups:
            raise KeyError(
                f'Missing groups in endorsement config: {missing_groups}'
            )

def _yield_unique_peers(peer_iterator: Iterator[Peer]):
    peers: Set[Peer] = set()
    for peer in peer_iterator:
        if peer not in peers:
            peers.add(peer)
            yield peer
        break
