from pprint import pprint as pp

class NotinitialisedException(Exception):
    pass

VERBOSE = True

class IOCC(object):
    def __init__(self):
        self.initialised = False
        self.d = None

    def getObject(self, objName):
        if not self.initialised:
            raise( NotinitialisedException)
        return self.d.get(objName, None)

    def dictForClass(self, klazz):
        d = {}
        for base in klazz.__bases__:
            d.update( self.dictForClass( base ) )
        d.update( klazz.__dict__)
        #print "Returing %s" % str(d)
        return d
        
    def crossWire(self, d):
        methodsCalled = []
        lookup = dict( [ (x.upper(), y) for x,y in d.items() ] )
        # first lookup by name
        # Candidate Objects
        for q,v in lookup.items():
            ciq = q.upper()
            potentialTarget = "SET%s" % ciq
            #print "Target is %s" % potentialTarget
            for q2, v2 in lookup.items():
                vcd = self.dictForClass( v2.__class__  )
                #vcd = v2.__class__.__dict__

                vcdLookup = dict( [ (x.upper(), y) for x,y in vcd.items() if callable(y) ] )
                #pp( vcdLookup )
                #for x,y in vcdLookup.items():
                #    print type(y)
                #print potentialTarget, vcdLookup
                if vcdLookup.has_key(potentialTarget):
                    targetMethod = vcdLookup[potentialTarget]
                    #print "Thinking about name injection %s %s" % ( targetMethod, methodsCalled ) 
                    if not (v2,targetMethod) in methodsCalled:
                        
                        #targetO = v2
                        targetObject = v2
                        obj    = v
                        print("Name injection  %s ( %s, %s )" % (targetMethod, targetObject, obj))
                        targetMethod( targetObject, obj )
                        methodsCalled.append( (targetObject, targetMethod) )

        for q,v in lookup.items():
            ciq = v.__class__.__name__.upper()
            potentialTarget = "SET%s" % ciq
            for q2, v2 in lookup.items():
                vcd = self.dictForClass( v2.__class__)
                #vcd = v2.__class__.__dict__
                vcdLookup = dict( [ (x.upper(), y) for x,y in vcd.items() ] )
                #print potentialTarget, vcdLookup.keys()

                if vcdLookup.has_key(potentialTarget):
                    target = vcdLookup[potentialTarget]
                    if not target in methodsCalled:
                        targetObject = v2
                        obj    = v
                        print "Class injection %s ( %s, %s )" % (targetObject, target, obj)
                        target( targetObject, obj)
                        methodsCalled.append(target)
        
        for v in d.values():
            if VERBOSE: print v.__class__.__dict__
            d = self.dictForClass( v.__class__);
            if d.has_key('onInit'):
                if VERBOSE: print type(v.onInit)
                if callable(v.onInit):
                    v.onInit()

class A_super:
    def setB(self, b):
        self.b = b
                    
class A(A_super):
    pass
class B:
    def setA(self, a):
        self.a = a

class OrderManager:
    def setPositionManager(self, pm):
        self.pm = pm

    def setFoo(self, foo):
        self.foo = foo

class Foo:
    pass

class PositionManager:
    def setA(self, a):
        self.a = a

    def setB(self, b):
        self.b = b
        
    def setOrderManager(self, om):
        self.om = om

    def setNamedObject(self, no):
        self.namedObject = no

    def onInit(self):
        print "onInit"
        for x in ['a','b','om']:
            assert self.__dict__.has_key(x)

if __name__=='__main__':
    ioc = IOCC( )
    om = OrderManager()
    pm = PositionManager()
    
    a = A()
    b= B()
    class ID:
        a = 0
        def next(self):
            ID.a += 1
            return str(ID.a)

    bd = { ID().next() : om,
           ID().next() : pm,
           ID().next() : a,
           ID().next() : b,
           'namedObject' : object(), 
           'Foo'   : Foo() }

    print pp(bd)

    ioc.crossWire( bd )
    assert( pm.om == om)
    assert( pm.a == a )
    assert( pm.b == b )
    assert( om.pm == pm)

    

    

        


        

        
        
