"""
    Discovery models
"""

from dataclasses import dataclass, field
from collections import Counter
from typing import List, Map

from ..protos.msp.msp_config_pb2 import FabricMSPConfig
from ..protos.discovery.protocol_pb2 import Response, QueryResult
from ..protos.gossip.message_pb2 import GossipMessage

from . import Orderer, Peer, ChaincodeSpec
from ._base import BaseModel



@dataclass
class DiscoveryResult(BaseModel):
    """ The result of a discovery query """
    msps: List[FabricMSPConfig]
    orderers: List[Orderer]
    endorsing_peers: List[Peer]
    local_peers: List[Peer]
    chaincodes: List[ChaincodeSpec]

    @classmethod
    def from_response(cls, response: Response) -> 'DiscoveryResult':
        config_resp, peer_resp, cc_resp, local_peer_resp = response.results

        msps = config_resp.config_result.msps

        orderers = []
        for msp_id, endpoints in config_resp.config_result.orderers.items():
            msp = msps[msp_id]
            tls_ca_cert = _get_tls_cert(msp)
            for endpt_conf in endpoints.endpoint:
                endpoint = f'{endpt_conf.host}:{endpt_conf.port}'
                orderers.append(Orderer(
                    msp_id=msp_id,
                    endpoint=endpoint,
                    tls_ca_cert=tls_ca_cert
                ))

        endorsing_peers = []
        for msp_id, peers in peer_resp.members.peers_by_org.items():
            tls_ca_cert = _get_tls_cert(msp)
            for peer_conf in peers.peers:
                endpoint = GossipMessage.FromString(
                    peer_conf.membership_info.payload
                ).alive_msg.membership.endpoint
                endorsing_peers.append(Peer(
                    msp_id=msp_id,
                    endpoint=endpoint,
                    tls_ca_cert=tls_ca_cert
                ))

        local_peers = []
        for msp_id, peers in local_peer_resp.members.peers_by_org.items():
            tls_ca_cert = _get_tls_cert(msp)
            for peer_conf in peers.peers:
                endpoint = GossipMessage.FromString(
                    peer_conf.membership_info.payload
                ).alive_msg.membership.endpoint
                local_peers.append(Peer(
                    msp_id=msp_id,
                    endpoint=endpoint,
                    tls_ca_cert=tls_ca_cert
                ))

        endorsement_desc = cc_resp.cc_query_res.content[0]

        return cls(
            orderers=orderers,
            endorsing_peers=endorsing_peers,
            msps=list(msps.values()),
            chaincodes=[],
            local_peers=local_peers
        )


def _get_tls_cert(msp: FabricMSPConfig) -> bytes:
    for cert in msp.tls_root_certs:
        return cert
    for cert in msp.tls_intermediate_certs:
        return cert
    raise ValueError(f'No TLS certs found for msp {msp.name}')


def _get_peers_from_resp(resp: QueryResult, msps: Map[str, FabricMSPConfig]):
    for msp_id, peers in resp.members.peers_by_org.items():
        msp = msps[msp_id]
        tls_ca_cert = _get_tls_cert(msp)
        for peer_conf in peers.peers:
            endpoint = GossipMessage.FromString(
                peer_conf.membership_info.payload
            ).alive_msg.membership.endpoint
            yield Peer(
                msp_id=msp_id,
                endpoint=endpoint,
                tls_ca_cert=tls_ca_cert
            )
