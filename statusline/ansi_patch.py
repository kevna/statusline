from ansi.colour.base import Graphic
from ansi.sequence import sequence


def patch(self):
    return '\001%s\002' % self.sequence


Graphic.__str__ = patch


def colour256(colour):
    return '\001%s\002' % sequence('m', fields=3)(38, 5, colour)
