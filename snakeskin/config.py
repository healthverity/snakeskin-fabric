"""
    Blockchain configuration
"""

import os
import json
from dataclasses import dataclass, field, replace
from typing import List, Mapping, Optional

import yaml
import dacite

from .models import Peer, Channel, User, Orderer, ChaincodeSpec
from .models.gateway import Gateway
from .constants import ChaincodeLanguage, PolicyExpression

@dataclass()
class GatewayConfig:
    """ A gateway config object """
    channel: str
    requestor: str
    endorsing_peers: List[str] = field(default_factory=list)
    orderers: List[str] = field(default_factory=list)
    chaincode: Optional[str] = None

@dataclass()
class BlockchainConfig:
    """ A gateway for accessing the blockchain """

    @classmethod
    def from_file(cls, file_path: str):
        """ Loads gateway config from a static file """
        ext = os.path.splitext(file_path)[1]

        with open(file_path) as inf:
            if ext == '.json':
                return cls.from_dict(json.load(inf))
            if ext in {'.yaml', '.yml'}:
                return cls.from_dict(yaml.load(inf, Loader=yaml.SafeLoader))

        raise ValueError(
            f'Unrecognized file extension for file {file_path}'
        )

    @classmethod
    def from_dict(cls, value: dict):
        """ Creates a gateway config from a dictionary """
        return dacite.from_dict(cls, value, config=dacite.Config(
            type_hooks={
                ChaincodeLanguage: ChaincodeLanguage,
                PolicyExpression: PolicyExpression
            }
        ))

    peers: Mapping[str, Peer] = field(default_factory=dict)
    orderers: Mapping[str, Orderer] = field(default_factory=dict)
    users: Mapping[str, User] = field(default_factory=dict)
    chaincodes: Mapping[str, ChaincodeSpec] = field(default_factory=dict)
    gateways: Mapping[str, GatewayConfig] = field(default_factory=dict)

    def __post_init__(self):
        # Set names to be the mapping key for all entities that weren't
        # provided names
        self.peers = {
            name: replace(peer, name=peer.name or name)
            for name, peer in self.peers.items()
        }
        self.orderers = {
            name: replace(orderer, name=orderer.name or name)
            for name, orderer in self.orderers.items()
        }
        self.users = {
            name: replace(user, name=user.name or name)
            for name, user in self.users.items()
        }
        self.chaincodes = {
            name: replace(chaincode, name=chaincode.name or name)
            for name, chaincode in self.chaincodes.items()
        }

    def get_gateway(self, name: str):
        """ Gets a gateway using the config name """
        if name not in self.gateways:
            raise KeyError(f'No gateway defined with name "{name}"')
        config = self.gateways[name]
        return Gateway(
            endorsing_peers=[
                self.get_peer(peer) for peer in config.endorsing_peers
            ],
            chaincode=self.get_chaincode(config.chaincode) if config.chaincode else None,
            requestor=self.get_user(config.requestor),
            orderers=[
                self.get_orderer(orderer) for orderer in config.orderers
            ],
            channel=Channel(name=config.channel)
        )

    def get_peer(self, name: str):
        """ Gets a peer using the config name """
        if not name in self.peers:
            raise KeyError(f'No peer defined with name "{name}"')
        return self.peers[name]

    def get_orderer(self, name: str):
        """ Gets a orderer using the config name """
        if not name in self.orderers:
            raise KeyError(f'No orderer defined with name "{name}"')
        return self.orderers[name]

    def get_user(self, name: str):
        """ Gets a user using the config name """
        if not name in self.users:
            raise KeyError(f'No user defined with name "{name}"')
        return self.users[name]

    def get_chaincode(self, name: str):
        """ Gets a chaincode spec using the config name """
        if not name in self.chaincodes:
            raise KeyError(f'No chaincode defined with name "{name}"')
        return self.chaincodes[name]
