# $Header: /Users/andy/cvs/dev/python/pyfix/fix/BerkeleyPersister.py,v 1.16 2009-02-24 17:01:00 andy Exp $

fileRoot = "/Users/andy/persist"

from datetime import datetime
import os

try:
    from bsddb3 import db as _db
    db = _db
except:
    from bsddb import db

class BerkeleyPersister:
    def __init__(self, root, sender, target, dt = datetime.now()):
        strToday = dt.strftime("%Y%m%d")
        self.sender = sender
        self.target = target
        self.todayRoot = "%s/%s" % (root, strToday)
        self.persistCache = {}
        try:
            os.makedirs( self.todayRoot)
        except OSError: # Exists already?
            pass
        self.createPersister()

    def getNextSeq(self, db):
        c = db.cursor()
        q_v = c.last()
        if q_v:
            q,v = q_v
            return q+1
        else:
            return 1

    def dump(self):
        self.report(self.inDb)
        self.report(self.outDb)
        self.report(self.ledger)

    def report(self, db):
        print "="* 80
        c = db.cursor()
        while True:
            d = c.next()
            if not d:
                break
                #print d
            print d

    def persistLedgerObject( self, s ):
        self.ledger[self.ledgerIdx] = s
        self.ledgerIdx.sync()
        self.ledgerIdx += 1

    def persistInMsg( self, seqNum, txt):
        self.inDb[ seqNum ] = txt
        self.ledger[self.ledgerIdx] = txt
        self.ledgerIdx += 1
        self.inDb.sync()
        self.ledger.sync()

    def persistOutMsg( self, seqNum, txt):
        self.outDb[ seqNum ] = txt
        self.ledger[self.ledgerIdx] = txt
        self.ledgerIdx += 1
        self.outDb.sync()
        self.ledger.sync()
        
    def deleteLastNFromDb(self, n, db):
        for _ in range(n):
            c = db.cursor()
            s_d = c.last()
            if not s_d:
                # No data! Och well
                break
            seq, data = s_d
            print "Deleting %s %s" % (seq, data)
            del db[seq]
        db.sync()

    def __repr__(self):
        return "BerkeleyPersister(%s,%s)" % ( self.inFile, self.outFile)
        
    def getTodayPersister(self):
        return ( self.inDb, self.outDb)
    
    def createPersister(self):
        print "GetPersister %s %s" % (self.sender,
                                      self.target)
        quay = "%s_%s" % (self.sender, self.target)
        self.inFile  = "%s/%s_in.db"  % (self.todayRoot, str( quay ) )
        self.outFile = "%s/%s_out.db" % (self.todayRoot, str( quay ) )
        self.ledgerFile = "%s/%s_ledger.db" % (self.todayRoot, str( quay ) )
        print self.inFile, self.outFile, self.ledgerFile
        self.inDb  = db.DB()
        self.outDb = db.DB()
        self.ledger = db.DB()
        print self.inFile, self.outFile, self.ledgerFile

        self.inDb.open(self.inFile  , db.DB_RECNO, db.DB_CREATE)
        self.outDb.open(self.outFile, db.DB_RECNO, db.DB_CREATE)
        self.ledger.open(self.ledgerFile, db.DB_RECNO, db.DB_CREATE)
        self.ledgerIdx = self.getNextSeq( self.ledger )
        
        # This will blow away the last few messages
        #self.deleteLastNFromDb( 10 , self.inDb)
        # Dump out contents
        ret = ( self.inDb,
                self.outDb)
        return ret

if __name__=='__main__':
    fr = "/Users/andy/persist/send/20090112"
    bp = BerkeleyPersister(fileRoot, "SENDER", "PHROMS", dt = datetime( 2009, 1, 12) )
    (inDb,outDb) = bp.getTodayPersister()
    #p = BerkeleyPersister( fileRoot, dt = datetime(2009, 11,1) )
