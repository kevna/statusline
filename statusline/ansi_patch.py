from ansi.colour.base import Graphic
from ansi.sequence import sequence


def patch(self):
    return f'\001{self.sequence}\002'


Graphic.__str__ = patch


def colour256(colour):
    seq = sequence('m', fields=3)(38, 5, colour)
    return f'\001{seq}\002'
