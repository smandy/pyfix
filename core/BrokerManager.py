from Manager import Manager

class Broker:
    pass

brokerDefaults = """
id,name
1,INTC
2,ARCA
3,NUFO
"""

class BrokerManager(Manager):
    def __init__(self, manageClass = Broker, defaults = brokerDefaults):
        Manager.__init__(self, manageClass, defaults)

if __name__=='__main__':
    bm = BrokerManager()
