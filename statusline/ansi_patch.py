from ansi.colour.base import Graphic
from ansi.sequence import sequence


def patch(self):
    """Monkeypatch for Graphic.__str__ with non-printing character escapes added."""
    return f'\001{self.sequence}\002'


Graphic.__str__ = patch


def colour256(colour):
    """Generate a 256 colour escape.
    This method takes a 256 colour code rather than taking 'true colour' and estimating it.
    """
    seq = sequence('m', fields=3)(38, 5, colour)
    return f'\001{seq}\002'
