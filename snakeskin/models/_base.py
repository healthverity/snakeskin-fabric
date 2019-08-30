"""
    Base model for snakeskin
"""

from dataclasses import dataclass, replace

@dataclass
class BaseModel:
    """ Base snakeskin model """

    def copy_with(self, **kwargs):
        """ Copies the model, replacing any existing properties with any
            listed in kwargs, returning the copy
        """
        return replace(self, **kwargs)
