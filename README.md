# Snakeskin

```
Python + Fabric == snakeskin
```

This library is a re-implementation of the official Hyperledger Fabric Python SDK, intended for building Python interfaces with HLF that require more fine-grained control over interaction with a blockchain network.

With snakeskin you can manage transaction lifecycles, request retries, and complex network gateways with a high degree of specificity and control, while still leveraging higher-level operations when the control is not needed or desired.

## Installation

```console
$ [sudo] pip install snakeskin-fabric
```

## Config

Snakeskin can be configured using a static file, or dynamically in Python, and is relatively flexible, as the requirements for a configuration depend largely on the use case.

See the example configuration in `examples/config-files/example-blockchain-config.yaml` for example configuraiton structure. Note that configuration files can also be provided in the `.json` file format.

To load a configuration into the framework, simply do:

```python
from snakeskin.config import BlockchainConfig

# Or load from a static file
blockchain = BlockchainConfig.from_file('/path/to/config/file.yaml')

# Or load from a dictionary
blockchain = BlockchainConfig.from_dict({
    # ...
})
```

## Interacting with the Blockchain

To run transactions against the blockchain, it's easiest to use gateways,
which are configured with the requisite peers, orderers, channel, and chaincode
specifications. See the `gateways` section of the example config for
configuration options. Once configured, you can pull your gateway from the
blockchain config with:

```python
gateway = blockchain.get_gateway('my-gateway')
```


### Transactions

Once configured, performing transactions against the chaincode is relatively
straight-forward. Gateways expose the same high-level abstracts
- `invoke` and `query` - as the Hyperledger `peer` CLI command.

```python

# query the chaincode to retrieve data
transaction = await gateway.query(
    fcn='doSomething',
    args=['arg1', 'arg2']
)

# invoke the chaincode to persist data
transaction = await gateway.invoke(
    fcn='doSomething',
    args=['arg1', 'arg2'],
    timeout=50
)

transaction.response_payload #=> b'<chaincode response>'
```

However, if you want more control over the transaction flow, you can use the
`transact` method:

```python
# A step-by-step transaction flow
transaction = await (
    gateway.transact(
        fcn='doSomething',
        args=['arg1', 'arg2']
    )
    # Sends the transaction to the peers for endorsement
    .propose()
    # Optionally sends the transaction to the orderers for committing
    .submit()
    # Optionally wait (up to 50 seconds) for the transaction to be successfully
    # committed to the peer
    .wait_for_commit(timeout=50)
)

transaction.response_payload #=> b'<chaincode response>'
```


### Network Administration

Most administrative operations are also available through the Gateway:

```python
# Creates the channel, via the orderer
await gateway.create_channel(tx_file_path='/path/to/channel.tx')
# Joins the gateway's endorsing peers to the channel
await gateway.join_channel()
# Query instantiated chaincode for the channel
resp = await gateway.query_instantiated_chaincodes()
resp.chaincodes[0].name # => 'my-chaincode'
# Installs the chaincode
await gateway.install_chaincode()
# Instantiates the chaincode
await gateway.instantiate_chaincode(timeout=60)
# Upgrades the chaincode
await gateway.instantiate_chaincode(timeout=60, upgrade=True)
```

Note that not all assets on the Gateway are required for each administrative operation. `create_channel`, for instance, doesn't require any endorsing peers defined on the Gateway.


### Stand-alone Operations

A Gateway definition is not required to perform any operation against the blockchain, it is simply a helpful tool in configuring groupings of assets. To perform operations without a Gateway, import them from the `snakeskin.operations` module. For example:

```python
from snakeskin.operations import create_channel

await create_channel(
    requestor=config.get_user('my-user'),
    orderers=[config.get_orderer('my-orderer')],
    channel=config.get_channel('my-channel'),
    tx_file_path='/path/to/channel.tx'
)
```

Similarly, fine-grained transaction management is available from `snakeskin.transact`:

```python
from snakeskin.transact import generate_cc_tx, propose_tx, commit_tx

requestor = config.get_user('my-user')
generated_tx = await generate_cc_tx(
    requestor=requestor,
    cc_name=config.get_chaincode('mycc').name,
    channel=config.get_channel('my-channel'),
    fcn='doSomething',
    args=['arg1', 'arg2']
)

endorsed_tx = await propose_tx(
    peers=[config.get_peer('my-peer')],
    generated_tx=generated_tx
)

committed_transaction = await commit_tx(
    requestor=requestor,
    orderers=[config.get_orderer('my-orderer')],
    endorsed_tx=endorsed_tx,
)
```

## Contributing

Coming soon

## License

This software uses the Apache License Version 2.0 software license.