

def myCap(x):
    return x[0].upper() + x[1:]


def attr_set_func(attr):
    def setter(self, x):
        setattr(self, attr, x)
    return setter


class attr_setter(type):
    def __new__(mcs, name, bases, d):
        print(f"{mcs} {name} {bases} {d} New has been called")
        if 'attrs' in d:
            attrs = d.pop('attrs')
            d['__slots__'] = attrs
            for attr in attrs:
                methodName = f"set{myCap(attr)}"
                d[methodName] = attr_set_func(attr)
        return type(name, bases, d)


if __name__ == '__main__' or True:
    class A(metaclass=attr_setter):
        __metaclass__ = attr_setter
        attrs = ['orderManager', 'positionManager', 'clOrdIDGen']

        def normalMethod(self, x):
            self.norm = x

        @classmethod
        def doCls(cls):
            print(f"doCls {cls}")

    a = A()
    a.setOrderManager(1)
    a.setPositionManager(32)
