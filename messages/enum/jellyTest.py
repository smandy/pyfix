
from   twisted.spread.jelly import jelly, unjelly
import pyfix.messages.enum.ExecType as ExecType

pn = ExecType.PENDING_NEW
print jelly(pn)


