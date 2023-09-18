from pyfix.messages.enum.Side import Side
from pyfix.messages.Order     import Order
from pyfix.messages.Execution import Execution 
from pyfix.messages.enum      import ExecType

from pyfix.core.AccountManager  import AccountManager,  Account
from pyfix.core.SecurityManager import SecurityManager, Security
from StringIO import StringIO


class StringAttr:
    def set(self, target, name, persister):
        s = persister.readString()
        target.__dict__[name] = s

    def write(self, target, name, persister):
        s = target.__dict__[name]
        persister.writeString(s)


class FloatAttr:
    def set(self, target, name, persister):
        i = persister.readFloat()
        target.__dict__[name] = i

    def write(self, target, name, persister):
        f = target.__dict__[name]
        assert isinstance(f, float)
        persister.writeFloat(f)


class IntAttr:
    def set(self, target, name, persister):
        i = persister.readInt()
        target.__dict__[name] = i

    def write(self, target, name, persister):
        i = target.__dict__[name]
        assert isinstance(i, int)
        persister.writeInt(i)


class SecurityAttr:
    # The field in the class we will actually persist
    field = 'ticker'

    def set(self, target, name, persister):
        s = persister.readString()
        security = persister.securityManager.getByFields([self.field], s)
        assert security is not None, "Couldn't resolve security"
        target.__dict__[name] = security

    def write(self, target, name, persister):
        sec = target.__dict__[name]
        assert sec.__class__ == Security, \
            f"Couldn't resolve security from {sec} {type(sec)}"
        persister.writeInt(sec.__dict__[self.field])


class AccountAttr:
    # The field we will persist
    field = 'name'

    def set(self, target, name, persister):
        s = persister.readString()
        account = persister.accountManager.getByFields([self.field], s)
        assert account is not None, "Couldn't resolve account"
        target.__dict__[name] = account

    def write(self, target, name, persister):
        account = target.__dict__[name]
        assert account.__class__ == Account, "Couldn't resolve account"
        persister.writeString(account.__dict__[self.field])


class SideAttr:
    def set(self, target, name, persister):
        strSide = persister.readString()
        side = Side.lookup[strSide]
        target.__dict__[name] = side

    def write(self, target, name, persister):
        side = target.__dict__[name]
        persister.writeString(side.name)


class ExecTypeAttr:
    def set(self, target, name, persister):
        strExecType = persister.readString()
        execType = ExecType.lookup[strExecType]
        target.__dict__[name] = execType

    def write(self, target, name, persister):
        execType = target.__dict__[name]
        persister.writeString(execType.name)

# Are these what the C++ crowd would call exemplars


stringAttr = IntAttr()
sideAttr = SideAttr()
execTypeAttr = ExecTypeAttr()
floatAttr = FloatAttr()
securityAttr = SecurityAttr()
accountAttr = AccountAttr()


class CsvPersister:
    def __init__(self, myObjectStream, metaData):
        self.fields = []
        self.metaData = metaData
        self.objectStream = myObjectStream
        self.klassLookup = {}
        for q in metaData.keys():
            self.klassLookup[q.__name__] = q
        self.accountManager = AccountManager()
        self.securityManager = SecurityManager()

    def readFloat(self):
        x = self.getField()
        print(f"float -> {x}")
        return float(x)

    def writeFloat(self, f):
        self.objectStream.write(str(f))
        self.objectStream.write(',')

    def writeEndOfRecord(self):
        self.objectStream.write("\n")

    def writeString(self, s):
        self.objectStream.write(s)
        self.objectStream.write(',')

    def writeInt(self, i):
        self.objectStream.write(str(i))
        self.objectStream.write(',')

    def readString(self):
        return str(self.getField())

    def getField(self):
        return self.objectStream.get_field()

    def readInt(self):
        return int(self.getField())

    def writeObject(self, obj):
        klazz = obj.__class__
        objName = klazz.__name__
        self.writeString(objName)
        self.writeInt(klazz.version)
        assert self.metaData.has_key(klazz), f"Unregistered class {objName}"
        fields = self.metaData[klazz]
        for (functor, name, _) in fields:
            functor.write(obj, name, self)
        self.writeEndOfRecord()
        self.objectStream.flush()

    def readObject(self):
        objName = self.getField()
        if objName == END_OF_RECORD:
            return None
        if not objName:
            return None

        klass = self.klassLookup[objName]
        _ = self.readInt()
        target = klass()
        fields = self.metaData[klass]
        for (functor, name, _) in fields:
            functor.set(target, name, self)
            print(f"{name} -> {getattr(target,name)}")
        return target


persist2 = {
    Order: [
        (stringAttr, 'clOrdID', 1),
        (securityAttr, 'security', 1),
        (IntAttr, 'orderQty', 1),
        (sideAttr, 'side', 1),
        (accountAttr, 'account', 1)],
    Execution: [
        (stringAttr, 'execID', 1),
        (execTypeAttr, 'execType', 1),
        (stringAttr, 'clOrdID', 1),
        (sideAttr, 'side', 1),
        (IntAttr, 'lastShares', 1),
        (securityAttr, 'security', 1),
        (floatAttr, 'lastPx', 1)]}


# from pyfix.tx.ExecutionWrapper import ExecutionWrapper
# from pyfix.tx.OrderWrapper     import OrderWrapper
# persist2[ExecutionWrapper] = persist2[Execution]
# persist2[OrderWrapper]     = persist2[Order]


END_OF_RECORD = "END_OF_RECORD"


class TestSpooler:
    def __init__(self, f):
        self.f = f
        self.currentRecord = None

    def write(self, x):
        self.f.write(x)

    def flush(self):
        self.f.flush()

    def getField(self):
        if not self.currentRecord or \
           self.recordIndex >= len(self.currentRecord):
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
        return ret.split(',')


objectStream = """
Order,1,order1,MSFT,100,BUY,ANDY
Order,1,order2,MSFT,200,SELL,ANDY
Execution,1,exec1,PARTIAL_FILL,order1,BUY,100,MSFT,33.5
"""[1:]

if __name__ == '__main__':
    p = CsvPersister(TestSpooler(StringIO(objectStream)), persist2)
    outString = StringIO()
    p2 = CsvPersister(TestSpooler(outString), persist2)

    while 1:
        print("Reading")
        tmp = p.readObject()
        print(tmp)
        if not tmp:
            break
        print("Writing")
        p2.writeObject(tmp)
        o = tmp

    outString.seek(0)
    s2 = outString.read()
    print(s2)

    refeed = StringIO(s2)
    p3 = CsvPersister(TestSpooler(refeed), persist2)
    print("ReReading")
    while 1:
        o = p3.readObject()
        if not o:
            break
        print(o)

    ts = TestSpooler(StringIO(objectStream))
    while 0:
        r = ts.getField()
        if not r:
            break
        print(r)
