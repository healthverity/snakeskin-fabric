"""
    Tests for the models package
"""

from unittest.mock import patch

from snakeskin.models import (
    User, DEFAULT_CRYPTO_BACKEND, Orderer
)


@patch('snakeskin.models.load_pem_private_key')
def test_user_post_init(load_pem_mock):
    """ Tests user's post init """
    user = User(
        msp_id='MyOrg',
        name='AdminUser',
        cert_path='test/resources/certfile',
        key_path='test/resources/keyfile',
    )

    assert user.key == b'notactuallyakey'
    assert user.cert == b'notactuallyacert'

    load_pem_mock.assert_called_with(
        b'notactuallyakey', None, DEFAULT_CRYPTO_BACKEND
    )


@patch('aiogrpc.insecure_channel', autospec=True)
def test_orderer_no_certs(insecure_channel):
    """ Tests creates an insecure channel for an orderer if no certs
        provided
    """
    Orderer(endpoint='notactuallyahost:7050')
    insecure_channel.assert_called_with('notactuallyahost:7050', [])


@patch('aiogrpc.insecure_channel', autospec=True)
def test_orderer_ssl_target_name(insecure_channel):
    """ Instantiates connection with ssl target name override """
    Orderer(endpoint='notactuallyahost:7050', ssl_target_name='otherhostname')
    insecure_channel.assert_called_with(
        'notactuallyahost:7050',
        [('grpc.ssl_target_name_override', 'otherhostname')]
    )


@patch('aiogrpc.ssl_channel_credentials', autospec=True)
@patch('aiogrpc.secure_channel', autospec=True)
def test_orderer_tls_cert(secure_channel, ssl_creds):
    """ Tests creates an secure channel if a tls ca cert is provided
    """
    Orderer(
        endpoint='notactuallyahost:7050',
        tls_ca_cert_path='test/resources/certfile'
    )
    ssl_creds.assert_called_with(b'notactuallyacert')
    secure_channel.assert_called_with(
        'notactuallyahost:7050', ssl_creds.return_value, []
    )


@patch('aiogrpc.ssl_channel_credentials', autospec=True)
@patch('aiogrpc.secure_channel', autospec=True)
def test_orderer_client_auth(secure_channel, ssl_creds):
    """ Tests creates a client-authenticated channel if client creds provided
    """
    Orderer(
        endpoint='notactuallyahost:7050',
        tls_ca_cert_path='test/resources/certfile',
        client_cert_path='test/resources/client_certfile',
        client_key_path='test/resources/client_keyfile'
    )
    ssl_creds.assert_called_with(
        b'notactuallyacert',
        private_key=b'notactuallyaclientkey',
        certificate_chain=b'notactuallyaclientcert'
    )
    secure_channel.assert_called_with(
        'notactuallyahost:7050', ssl_creds.return_value, []
    )
