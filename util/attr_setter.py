

def myCap(x):
    return x[0].upper() + x[1:]

def attr_set_func(attr):
    def setter(self, x):
        setattr( self, attr, x)
    return setter

class attr_setter(type):
    def __new__(_, name, bases, d):
        if d.has_key('attrs'):
            attrs = d.pop('attrs')
            for attr in attrs:
                methodName = "set%s" % myCap(attr)
                d[methodName] = attr_set_func(attr)
        return type( name, bases, d)

if __name__=='__main__':
    class A:
        __metaclass__=attr_setter
        attrs = [ 'orderManager','positionManager','clOrdIDGen']
        def normalMethod(self, x):
            self.norm  = x

        @classmethod
        def doCls(cls):
            print "doCls %s" % cls 
            pass
        
    a = A()
    a.setOrderManager(1)
    a.setPositionManager(32)
    


    
