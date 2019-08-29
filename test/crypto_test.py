"""
    Tests for the config module
"""

from unittest.mock import patch
from snakeskin.crypto import CryptoSuite

@patch.object(CryptoSuite, 'default')
def test_set_default_crypto(_):
    """ Tests CryptoSuite.set_default() """
    csuite = object()
    CryptoSuite.set_default(csuite)
    assert CryptoSuite.default is csuite
