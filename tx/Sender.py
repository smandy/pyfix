
from twisted.internet import reactor

class Sender:
    def __init__(self, delay = 1):
        self.delay = delay
        self.running = True

    def setOrderManager(self, orderManager):
        self.orderManager = orderManager

    def setOrderGenerator(self, orderGenerator):
        self.orderGenerator = orderGenerator
        
    def start(self):
        if self.running:
            print "Already started"
            return

        if not self.orderGenerator or not self.orderManager:
            print "Can't start - need sender and manager"
        
        self.running = True
        self.send()

    def stop(self):
        self.running = False

    def send(self):
        localOrder = self.orderGenerator.makeOrder()
        self.orderManager.send_order(localOrder)
        if self.running:
            reactor.callLater(self.delay,self.send)
