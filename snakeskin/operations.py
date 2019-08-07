"""
    Blockchain operations
"""

import io
import os
import struct
import tarfile
from typing import List

from .protos.peer.query_pb2 import ChaincodeQueryResponse
from .protos.common.configtx_pb2 import ConfigUpdateEnvelope
from .protos.common.common_pb2 import Envelope, Payload

from .models.transaction import EndorsedTX
from .models import (
    Channel,
    Orderer,
    Peer,
    User,
    ChaincodeSpec,
    EndorsementPolicy,
)

from .events import OrdererEvents

from .errors import TrasactionCommitError

from .constants import (
    ChaincodeProposalType,
    ChaincodeLanguage
)

from .factories import (
    tx_context_from_user,
    encode_proto_bytes,
    build_cc_deployment_spec,
    build_config_update_envelope,
    build_generated_tx
)

from .tx_flow import (
    generate_instantiate_cc_tx,
    generate_cc_tx,
    propose_tx,
    raise_tx_proposal_error,
    commit_tx_and_wait,
)

from .connect import (
    broadcast_to_orderer
)


async def create_channel(requestor: User, orderer: Orderer, channel: Channel,
                         tx_file_path: str):
    """ A high-level operation that creates a channel from a transaction file
        that was generated using the HLF configtxgen tool

        :param requestor: The user who will sign all requests
        :param orderer: An orderer that the transaction will be sent to
        :param channel: The channel that is being created
        :param tx_file_path: The disk location of the transaction file
                             that configtxgen created
    """

    # Extract the channel config from the generated transaction file
    with open(tx_file_path, 'rb') as tx_file:
        payload = Payload.FromString(
            Envelope.FromString(tx_file.read()).payload
        )
        configtx = ConfigUpdateEnvelope.FromString(payload.data)
        config_update = configtx.config_update

    # convert envelope to config
    tx_context = tx_context_from_user(requestor)

    envelope = build_config_update_envelope(
        channel=channel,
        tx_context=tx_context,
        config_update=config_update,
        requestor=requestor,
    )
    resp = await broadcast_to_orderer(envelope=envelope,
                                      orderer=orderer)
    if resp.status != 200:
        raise TrasactionCommitError(
            'Failed to create channel',
            response=resp,
            tx_id=tx_context.tx_id
        )


async def join_channel(requestor: User,
                       orderer: Orderer,
                       channel: Channel,
                       peer: Peer):
    """
        A high-level operation that joins a peer to a channel, with the
        following transaction flow:

        - Generates a transaction proposal
        - Sends that proposal to each of the peers for endorsement
        - Validates that all endorsements succeeded

        :param requestor: The user who will sign all requests
        :param peer: A peer that will join the channel
        :param orderer: An orderer that will be used to find the origin block
                        for this channel
        :param channel: The channel that the peer will join
    """

    events = OrdererEvents(
        requestor=requestor,
        channel=channel,
        orderer=orderer
    )

    block = None
    async for block in events.stream_blocks(start=0, stop=0):
        break

    generated_tx = build_generated_tx(
        requestor=requestor,
        cc_name='cscc',
        args=[
            encode_proto_bytes("JoinChain"),
            block.as_proto().SerializeToString()
        ],
        # The channel isn't joined yet, so we don't pass one when generating
        # the transaction
        channel=None
    )

    raise_tx_proposal_error(
        endorsed_tx=await propose_tx(
            peers=[peer],
            generated_tx=generated_tx
        ),
        msg=f'Failed to join peer {peer.name} to channel {channel.name}'
    )


async def query_instantiated_chaincodes(requestor: User,
                                        peers: List[Peer],
                                        channel: Channel) -> ChaincodeQueryResponse:
    """
        Queries instantiated chaincodes on the provided peers, with the
        following transaction flow:

        - Generates a transaction proposal
        - Sends that proposal to each of the peers for endorsement
        - Validates that all endorsements succeeded
        - Returns the chaincode query response object

        :param requestor: The user who will sign all requests
        :param peers: A list of peers that will be sent the transaction
                      proposal for endorsement. This function will raise a
                      TransactionProposalError if one of those endorsement
                      fails
        :param channel: The channel to query for instantiated chaincodes

        :return: A chaincode query response object
    """
    generated_tx = build_generated_tx(
        requestor=requestor,
        cc_name='lscc',
        args=[
            encode_proto_bytes('getchaincodes')
        ],
        channel=channel,
    )

    endorsed_tx = await propose_tx(
        peers=peers,
        generated_tx=generated_tx,
    )
    raise_tx_proposal_error(
        endorsed_tx=endorsed_tx,
        msg=f'Failed query instantiated chaincodes for channel {channel.name}'
    )

    resp = endorsed_tx.peer_responses[0]
    return ChaincodeQueryResponse.FromString(resp.response.payload)


async def query_installed_chaincodes(requestor: User,
                                     peer: Peer,
                                    ) -> ChaincodeQueryResponse:
    """
        Queries installed chaincodes on the provided peer, with the
        following transaction flow:

        - Generates a transaction proposal
        - Sends that proposal to provided peer
        - Validates that the endorsement succeeded
        - Returns the chaincode query response object

        :param requestor: The user who will sign all requests
        :param peers: A list of peers that will be sent the transaction
                      proposal for endorsement. This function will raise a
                      TransactionProposalError if one of those endorsement
                      fails
        :return: A chaincode query response object
    """

    generated_tx = build_generated_tx(
        requestor=requestor,
        cc_name='lscc',
        args=[
            encode_proto_bytes('getchaincodes')
        ],
    )

    endorsed_tx = await propose_tx(
        peers=[peer],
        generated_tx=generated_tx
    )

    raise_tx_proposal_error(
        endorsed_tx=endorsed_tx,
        msg='Failed query installed chaincodes'
    )

    resp = endorsed_tx.peer_responses[0]
    return ChaincodeQueryResponse.FromString(resp.response.payload)


def package_chaincode(cc_spec: ChaincodeSpec):
    """ Package chaincode into a tar.gz file
        Returns: The chaincode pkg path or None
    """

    if cc_spec.language == ChaincodeLanguage.GOLANG:
        if not cc_spec.path:
            raise ValueError('Must specify path on chaincode spec')
        go_path = os.environ['GOPATH']
        proj_path = os.path.join(go_path, 'src', cc_spec.path)

        if not os.listdir(proj_path):
            raise ValueError(f'No chaincode file found at path {proj_path}')

        with io.BytesIO() as tar_stream:
            with tarfile.open(fileobj=tar_stream, mode='w|gz') as dist:
                for dir_path, _, file_names in os.walk(proj_path):
                    for filename in file_names:
                        file_path = os.path.join(dir_path, filename)

                        with open(file_path, mode='rb') as file_obj:
                            arcname = os.path.relpath(file_path, go_path)
                            tarinfo = dist.gettarinfo(file_path, arcname)
                            # standardizes the tar metadata so that is
                            # consistent across all files - this allows
                            # consistent fingerprinting regardless of the SDK
                            # used ton package chaincode
                            tarinfo.uid = tarinfo.gid = 500
                            tarinfo.mode = 100644
                            tarinfo.mtime = 0
                            tarinfo.pax_headers = {
                                'atime': '0',
                                'ctime': '0',
                            }
                            dist.addfile(tarinfo, file_obj)

            # Uses a timestamp of zero to allow for consistent fingerprinting
            tar_stream.seek(4)
            timestamp_bytes = struct.pack("<L", 0)
            tar_stream.write(timestamp_bytes)

            tar_stream.seek(0)
            return tar_stream.read()

    else:
        raise ValueError('Currently only support install GOLANG chaincode')



async def install_chaincode(requestor: User,
                            peers: List[Peer],
                            cc_spec: ChaincodeSpec) -> EndorsedTX:
    """
        A high-level operation that packages and installs chaincode onto the
        provided peers with the following transaction flow:

        - Generates a transaction proposal
        - Sends that proposal to each of the peers for endorsement
        - Validates that all endorsements succeeded
        - Returns the endorsed transaction

        :param requestor: The user who will sign all requests
        :param peers: A list of peers that will be sent the transaction
                      proposal for endorsement. This function will raise a
                      TransactionProposalError if one of those endorsement
                      fails
        :param cc_spec: A specification of the metadata needed to install
                        the chaincode

        :return: The endorsed transaction
    """

    cc_pkg = package_chaincode(cc_spec)

    cc_deployment_spec = build_cc_deployment_spec(
        language=cc_spec.language,
        name=cc_spec.name,
        version=cc_spec.version,
        path=cc_spec.path,
        code_package=cc_pkg,
    )

    args = [
        encode_proto_bytes(ChaincodeProposalType.Install.value),
        cc_deployment_spec.SerializeToString()
    ]

    generated_tx = build_generated_tx(
        requestor=requestor,
        cc_name='lscc',
        args=args
    )

    endorsed_tx = await propose_tx(
        peers=peers,
        generated_tx=generated_tx,
    )

    raise_tx_proposal_error(
        endorsed_tx=endorsed_tx,
        msg=f'Failed install chaincode {cc_spec.name} version {cc_spec.version}'
    )

    return endorsed_tx


async def instantiate_chaincode(requestor: User,
                                peers: List[Peer],
                                orderers: List[Orderer],
                                channel: Channel,
                                cc_spec: ChaincodeSpec,
                                endorsement_policy: EndorsementPolicy = None,
                                upgrade: bool = False,
                                timeout: int = 60) -> EndorsedTX:
    """
        A high-level operation that instantiates or upgrades a chaincode on
        a channel with the following transaction flow:

        - Generates a transaction proposal
        - Sends that proposal to each of the peers for endorsement
        - Validates that all endorsements succeeded
        - Sends the endorsements to the orderer for committing
        - Checks to make sure the transaction successfully committed
          on the first peer in the list

        :param requestor: The user who will sign all requests
        :param peers: A list of peers that will be sent the transaction
                      proposal for endorsement. This function will raise a
                      TransactionProposalError if one of those endorsement
                      fails
        :param orderers: A list of orderers that will be sent the peer
                         endorsements. This function will try each orderer in
                         the list in orderer before finally raising a
                         TransactionCommitError.
        :param channel: The channel that the chaincode will be instantiated
                        onto
        :param cc_spec: A specification of the metadata needed to instantiate
                        the chaincode
        :param endorsement_policy: The endorsement policy that will define
                                   which entities must endorse chaincode
                                   transactions
        :param upgrade: Whether to upgrade existing chaincode or instantiate
                        a new chaincode
        :param timeout: The max number of second to wait for the transaction
                        to successfully commit to the first peer node

        :return: The endorsed transaction
    """

    generated_tx = generate_instantiate_cc_tx(
        requestor=requestor,
        cc_spec=cc_spec,
        channel=channel,
        endorsement_policy=endorsement_policy,
        upgrade=upgrade
    )

    method = 'upgrade' if upgrade else 'instantiate'

    endorsed_tx = await propose_tx(
        peers=peers,
        generated_tx=generated_tx,
    )

    raise_tx_proposal_error(
        endorsed_tx=endorsed_tx,
        msg=(
            f'Failed to {method} chaincode {cc_spec.name} version '
            f' {cc_spec.version} on channel {channel.name}'
        )
    )

    await commit_tx_and_wait(
        requestor=requestor,
        orderers=orderers,
        channel=channel,
        peers=peers,
        endorsed_tx=endorsed_tx,
        timeout=timeout,
    )

    return endorsed_tx


async def invoke(requestor: User,
                 peers: List[Peer],
                 orderers: List[Orderer],
                 channel: Channel,
                 cc_name: str,
                 fcn: str,
                 args: List[str] = None,
                 timeout: int = 30,
                 transient_map: dict = None) -> EndorsedTX:
    """
        A high-level operation that invokes the chaincode with the following
        transaction flow:

        - Generates a transaction proposal
        - Sends that proposal to each of the peers for endorsement
        - Validates that all endorsements succeeded
        - Sends the endorsements to the orderer for committing
        - Checks to make sure the transaction successfully committed
          on the first peer in the list

        :param requestor: The user who will sign all requests
        :param peers: A list of peers that will be sent the transaction
                      proposal for endorsement. This function will raise a
                      TransactionProposalError if one of those endorsement
                      fails
        :param orderers: A list of orderers that will be sent the peer
                         endorsements. This function will try each orderer in
                         the list in orderer before finally raising a
                         TransactionCommitError.
        :param channel: The channel where the chaincode is instantiated
        :param cc_name: The name of the chaincode to invoke
        :param fcn: The name of the chaincode function to invoke
        :param args: The arguments to pass into the function
        :param timeout: The max number of second to wait for the transaction
                        to successfully commit to the first peer node
        :param transient_map: A mapping of transient variables that will be passed to
                              the chaincode, but will not appear in the endorsed
                              transaction

        :return: The endorsed transaction
    """

    generated_tx = generate_cc_tx(
        requestor=requestor,
        cc_name=cc_name,
        channel=channel,
        fcn=fcn,
        args=args,
        transient_map=transient_map,
    )

    endorsed_tx = await propose_tx(
        peers=peers,
        generated_tx=generated_tx,
    )

    raise_tx_proposal_error(
        endorsed_tx=endorsed_tx,
        msg=(
            f'Failed to invoke chaincode {cc_name} with function {fcn}'
        )
    )

    await commit_tx_and_wait(
        requestor=requestor,
        orderers=orderers,
        channel=channel,
        peers=peers,
        endorsed_tx=endorsed_tx,
        timeout=timeout,
    )
    return endorsed_tx


async def query(requestor: User,
                peers: List[Peer],
                channel: Channel,
                cc_name: str,
                fcn: str,
                args: List[str] = None,
                transient_map: dict = None) -> EndorsedTX:
    """
        A high-level operation that queries the chaincode with the following
        transaction flow:

        - Generates a transaction proposal
        - Sends that proposal to each of the peers for endorsement
        - Validates that all endorsements succeeded
        - Returns the endorsed transaction

        :param requestor: The user who will sign all requests
        :param peers: A list of peers that will be sent the transaction
                      proposal for endorsement. This function will raise a
                      TransactionProposalError if one of those endorsement
                      fails
        :param channel: The channel where the chaincode is instantiated
        :param cc_name: The name of the chaincode to invoke
        :param fcn: The name of the chaincode function to invoke
        :param args: The arguments to pass into the function
        :param transient_map: A mapping of transient variables that will be passed to
                              the chaincode, but will not appear in the endorsed
                              transaction

        :return: The endorsed transaction
    """

    generated_tx = generate_cc_tx(
        requestor=requestor,
        cc_name=cc_name,
        channel=channel,
        fcn=fcn,
        args=args,
        transient_map=transient_map,
    )


    endorsed_tx = await propose_tx(
        peers=peers,
        generated_tx=generated_tx,
    )

    raise_tx_proposal_error(
        endorsed_tx=endorsed_tx,
        msg=(
            f'Failed to query chaincode {cc_name} with function {fcn}'
        )
    )

    return endorsed_tx
