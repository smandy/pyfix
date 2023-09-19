from twisted.spread import pb

from typing import Any


class OrdType(pb.Copyable, pb.RemoteCopy):
    lookup: dict[str, Any] = {}

    def __init__(self, name, isTerminal):
        self.name = name
        self.isTerminal = isTerminal
        OrdType.lookup[name] = self


MARKET = OrdType('MARKET', True)
LIMIT = OrdType('LIMIT', False)

pb.setUnjellyableForClass(OrdType, OrdType)
