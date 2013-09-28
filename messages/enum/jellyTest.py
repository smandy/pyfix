
from   twisted.spread.jelly import jelly, unjelly
import phroms.messages.enum.ExecType as ExecType

pn = ExecType.PENDING_NEW
print jelly(pn)


