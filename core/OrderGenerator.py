import random
from datetime import datetime
from pyfix.messages.Order import Order
from pyfix.messages.enum import Side

from pyfix.core.AccountManager  import AccountManager
from pyfix.core.SecurityManager import SecurityManager

class OrderGenerator:
    def __init__(self, prefix="TEST"):
        self.idBase = 0
        self.dt = datetime.now().strftime("%Y%m%d")
        self.prefix = prefix
        self.sideChoices = [Side.BUY, Side.SELL]
        self.accountManager = AccountManager()
        self.securityManager = SecurityManager()

    def orderWasDone(self, clOrdID):
        # persistence tells us about orders already done
        oldIdBase = int(clOrdID.split('_')[1])
        self.idBase = oldIdBase+1

    def onInit(self):
        print("OrderGenerator.onInit()")
        self.accountChoices = self.accountManager.items
        self.brokerChoices = self.brokerManager.items
        self.securityChoices = self.securityManager.items

    def setAccountManager(self, am):
        self.accountManager = am

    def setBrokerManager(self, bm):
        self.brokerManager = bm

    def setSecurityManager(self, sm):
        self.securityManager = sm

    def setClOrdIDGen(self, clOrdIDGen):
        self.clOrdIDGen = clOrdIDGen

    def makeOrder(self):
        side = random.choice(self.sideChoices)
        qty = 100
        px = 100
        security = random.choice(self.securityChoices)
        clOrdID = self.clOrdIDGen.makeClOrdID()
        account = random.choice(self.accountChoices)
        broker = random.choice(self.brokerChoices)
        ret = Order(clOrdID, security, qty, side, account, broker, px)
        return ret
