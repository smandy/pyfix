from phroms.messages.enum.Side import Side
from phroms.messages.Order     import Order
from phroms.messages.Execution import Execution 
from phroms.messages.enum      import ExecType

from phroms.core.AccountManager  import AccountManager,  Account
from phroms.core.SecurityManager import SecurityManager, Security

class StringAttr:
    def set( self, target, name, persister):
        s = persister.readString()
        target.__dict__[name] = s

    def write( self, target, name, persister):
        #print target.__dict__
        s = target.__dict__[name]
        persister.writeString( s )

class FloatAttr:
    def set( self, target, name, persister):
        i = persister.readFloat()
        target.__dict__[name] = i

    def write( self, target, name, persister):
        f = target.__dict__[name]
        assert type(f)==float
        persister.writeFloat( f )

class IntAttr:
    def set( self, target, name, persister):
        i = persister.readInt()
        target.__dict__[name] = i
        
    def write( self, target, name, persister):
        i = target.__dict__[name]
        assert type(i)==int
        persister.writeInt( i )

class SecurityAttr:
    # The field in the class we will actually persist
    field = 'ticker'
    def set(self, target, name, persister):
        s = persister.readString()
        security = persister.securityManager.getByFields( [ self.field], s )
        assert security is not None, "Couldn't resolve security"
        target.__dict__[name] = security

    def write( self, target,name, persister):
        sec = target.__dict__[name]
        assert sec.__class__==Security, "Couldn't resolve security from %s %s" % (sec, type(sec))
        persister.writeInt( sec.__dict__[self.field] )

class AccountAttr:
    # The field we will persist
    field = 'name'
    def set(self, target, name, persister):
        s = persister.readString()
        account = persister.accountManager.getByFields( [ self.field], s )
        assert account is not None, "Couldn't resolve account"
        target.__dict__[name] = account

    def write( self, target,name, persister):
        account = target.__dict__[name]
        assert account.__class__==Account, "Couldn't resolve account"
        persister.writeString( account.__dict__[self.field] )

class SideAttr:
    def set(self, target, name, persister):
        strSide = persister.readString()
        side = Side.lookup[strSide]
        target.__dict__[name] = side

    def write(self, target, name, persister):
        side = target.__dict__[name]
        persister.writeString( side.name )

class ExecTypeAttr:
    def set( self, target, name, persister):
        strExecType = persister.readString()
        execType = ExecType.lookup[strExecType]
        target.__dict__[name] = execType

    def write(self, target, name, persister):
        execType = target.__dict__[name]
        persister.writeString(execType.name)

# Are these what the C++ crowd would call exemplars
stringAttr   = StringAttr()
intAttr      = IntAttr()
sideAttr     = SideAttr()
execTypeAttr = ExecTypeAttr()
floatAttr    = FloatAttr()
securityAttr = SecurityAttr()
accountAttr  = AccountAttr()

class CsvPersister:
    def __init__(self, myObjectStream, metaData):
        self.fields = []
        self.metaData = metaData
        self.objectStream = myObjectStream
        #lines = objectStream.split("\n")[1:-1]
        #for line in lines:
        #    self.fields = self.fields + line.split(",")
        #self.fields.reverse()

        self.klassLookup = {}
        for q in metaData.keys():
            self.klassLookup[q.__name__] = q

        self.accountManager  = AccountManager()
        self.securityManager = SecurityManager()


    def readFloat(self):
        x = self.getField()
        print "float -> " + `x`
        return float(x)

    def writeFloat(self, f):
        self.objectStream.write( str(f))
        self.objectStream.write(',')

    def writeEndOfRecord(self):
        self.objectStream.write("\n")

    def writeString(self, s):
        self.objectStream.write(s)
        self.objectStream.write(',')

    def writeInt( self, i):
        self.objectStream.write( str(i))
        self.objectStream.write(',')

    def readString(self):
        return str(self.getField())

    def getField(self):
        return self.objectStream.getField()

    def readInt(self):
        return int(self.getField() )

    def writeObject(self, obj):
        klazz = obj.__class__
        #print "Klazz is %s" % klazz
        objName = klazz.__name__
        self.writeString( objName )
        self.writeInt(klazz.version)
        assert self.metaData.has_key( klazz ) , "Unregistered class %s" % objName
        fields = self.metaData[klazz]
        for ( functor, name, version) in fields:
            #print name
            functor.write(obj, name, self)
        self.writeEndOfRecord()
        self.objectStream.flush()

    def readObject(self):
        objName = self.getField()
        if objName==END_OF_RECORD:
            return None
        #print objName
        if not objName:
            return None
        
        klass = self.klassLookup[objName]
        _ = self.readInt() # TODO  XXX Version, to be used at some point?!
        #print version
        target = klass()
        fields = self.metaData[klass]
        for ( functor, name, version) in fields:
            #print name
            functor.set( target, name, self)
            print "%s -> %s" % (name, getattr(target,name) )

        #gf = self.getField()
        #assert gf in [ None,  END_OF_RECORD], "%s vs %s" % ( gf, END_OF_RECORD  )
        return target
            
persist2 = \
{
    Order : [
    ( stringAttr,   'clOrdID'  , 1 ),
    ( securityAttr, 'security' , 1 ),
    ( intAttr,      'orderQty' , 1 ),
    ( sideAttr,     'side'     , 1 ),
    ( accountAttr,  'account'  , 1 ) ],
    Execution : [
    ( stringAttr,   'execID'         , 1),
    ( execTypeAttr, 'execType'       , 1),
    ( stringAttr,   'clOrdID'        , 1),
    ( sideAttr  ,   'side'           , 1),
    ( intAttr   ,   'lastShares'     , 1),
    ( securityAttr, 'security'       , 1),
    ( floatAttr ,   'lastPx'         , 1)
    ]
    }

#from phroms.tx.ExecutionWrapper import ExecutionWrapper
#from phroms.tx.OrderWrapper     import OrderWrapper
#persist2[ExecutionWrapper] = persist2[Execution]
#persist2[OrderWrapper]     = persist2[Order]

from StringIO import StringIO

END_OF_RECORD = "END_OF_RECORD"
  
class TestSpooler:
    def __init__(self, f):
        isinstance( f, file)
        self.f = f
        self.currentRecord = None

    def write(self, x):
        self.f.write(x)
        
    def flush(self):
        self.f.flush()

    def getField(self):
        if not self.currentRecord or self.recordIndex>=len(self.currentRecord):
            self.currentRecord = self.getRecord()
            if not self.currentRecord:
                return None
            
        ret = self.currentRecord[self.recordIndex]
        self.recordIndex += 1
        return ret
        
    def getRecord(self):
        self.recordIndex = 0
        ret = self.f.readline().strip()
        if not ret:
            return None
        else:
            return ret.split(',')

objectStream = """
Order,1,order1,MSFT,100,BUY,ANDY
Order,1,order2,MSFT,200,SELL,ANDY
Execution,1,exec1,PARTIAL_FILL,order1,BUY,100,MSFT,33.5
"""[1:]
                        
if __name__=='__main__':
    if 1:
        p = CsvPersister( TestSpooler(StringIO(objectStream)), persist2 )
        outString = StringIO()
        p2 = CsvPersister( TestSpooler( outString ), persist2 )
        
        while 1:
            print
            print "Reading"
            x = p.readObject()
            print x
            if not x:
                break
            print "Writing"
            p2.writeObject(x)
            obj = x

        outString.seek(0)
        s = outString.read()
        print s

        refeed = StringIO(s)
        p3 = CsvPersister( TestSpooler(refeed), persist2)
        print "ReReading"
        while 1:
            obj = p3.readObject()
            if not obj:
                break
            print obj

    if 0:
        ts = TestSpooler( StringIO(objectStream))
        while 0:
            r = ts.getField()
            if not r: break
            print r
        


                        
