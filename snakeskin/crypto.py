"""
    Cryptography logic
"""

from ._hfc.crypto import ecies


class CryptoSuite: # pylint: disable=too-few-public-methods
    """ A singleton that can be used to access cryptography suites """

    default = ecies()

    @classmethod
    def set_default(cls, default):
        """ Sets the default crypto suite """
        cls.default = default
