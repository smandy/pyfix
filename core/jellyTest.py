# Having trouble jellying the executions - try using the spooler

import persistence
from StringIO import StringIO

from twisted.spread.jelly import jelly, unjelly

if __name__=='__main__':
    p = persistence.CsvPersister( persistence.TestSpooler(StringIO(persistence.objectStream)), persistence.persist2)
    while True:
        e = p.readObject()
        j = jelly(e)
        e2 = unjelly(j)
        print j
        print e, e2
        if not e:
            break
        
    








