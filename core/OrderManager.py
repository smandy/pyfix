from pyfix.messages.Order import Order
from pyfix.messages.Execution import Execution
from pyfix.util.OrderState import OrderState

FLUSH_CLOSED_ORDERS = True
import time


class CheckPointData:
    def __init__(self, secs, numOrders):
        self.secs = secs
        self.numOrders = numOrders


class OrderManager:
    def __init__(self):
        self.ordersByClOrdID = {}
        self.openOrdersByClOrdID = {}
        self.dispatch = {Order: self.onOrder,
                         Execution: self.onExecution}
        self.numOrders = 0
        self.oldCheckPoint = None
        self.orderStateListener = None
        self.fillListener = None

    def setClOrdIDGenerator(self, clOrdIDGenerator):
        self.clOrdIDGenerator = clOrdIDGenerator

    def setStateToCopyFor(self):
        pass

    def setPortfolioManager(self, pm):
        self.portfolioManager = pm

    def setFixApplication(self, fixApplication):
        self.fixApplication = fixApplication

    def doit(self):
        pass

    def checkPoint(self):
        newCheckPoint = CheckPointData(time.time(), self.numOrders)
        if self.oldCheckPoint:
            sentOrders = newCheckPoint.numOrders - self.oldCheckPoint.numOrders
            delay = newCheckPoint.secs - self.oldCheckPoint.secs
            orderRate = sentOrders / delay
            print(f"OrdersSent : {newCheckPoint.numOrders}=${self.oldCheckPoint.numorders}  Delay = {delay} -> {orderRate}")
        self.oldCheckPoint = newCheckPoint

    def setFillListener(self, fl):
        self.fillListener = fl
        print("setFillListener {fl}")
        print("Self on fill is {self.fillListener}")

    def setPersister(self, p):
        self.persister = p

    def setSecurityManager(self, sm):
        self.securityManager = sm

    def setAccountManager(self, am):
        self.accountManager = am

    def setOrderStateListener(self, ol):
        self.orderStateListener = ol

    def startOrderSender(self):
        pass

    def setRecoveryManager(self, rm):
        self.recoveryManager = rm

    def onRecoveredOrder(self, order):
        self.clOrdIDGenerator.recoveredOrder(order.clOrdID)
        self.onOrder(order)

    def onOrder(self, order):
        # print "onOrder"
        # order object contains names
        # orderstate object contains actual objects
        # XXX These assertions should be accept/rejects
        assert not self.ordersByClOrdID.has_key(order.clOrdID)
        assert not self.openOrdersByClOrdID.has_key(order.clOrdID)
        os = OrderState(order)
        print("Type of security is {type(order.security} {order.security}")
        os.setPortfolios(self.portfolioManager.portfoliosForOrder(os))
        self.ordersByClOrdID[order.clOrdID] = os
        self.openOrdersByClOrdID[order.clOrdID] = os
        self.numOrders += 1

        if not self.recoveryManager.inRecovery:
            self.fixApplication.send_order(order)
            self.persister.writeObject(order)
        if self.orderStateListener:
            self.orderStateListener.notify(os)

    def onExecution(self, execution):
        print("onExecution {execution}")
        clOrdID = execution.clOrdID
        if self.openOrdersByClOrdID.has_key(clOrdID):
            assert self.ordersByClOrdID.has_key(clOrdID)
            orderState = self.openOrdersByClOrdID[clOrdID]
            orderState.apply(execution)
            order = orderState.order
            if order.sender is not None:
                print("Sending execution to session {order.sender.d}")
                order.sender.sendExecution(orderState, execution)
            if orderState.isTerminal():
                del self.openOrdersByClOrdID[clOrdID]
                if FLUSH_CLOSED_ORDERS:
                    del self.ordersByClOrdID[clOrdID]

            # print "SHares : %s %s" % (execution.lastShares, self.onFill)
            if self.fillListener and execution.lastShares:
                self.fillListener.notify((orderState, execution))
        elif self.openOrdersByClOrdID.has_key(clOrdID):
            print("Exec on closed order")
        else:
            print("Async Execution : {execution}")
            if self.fillListener and execution.lastShares:
                # I guess I decided with myself at some point that a null order
                # indicates an asynchronous execution
                self.fillListener.notify((None, execution))

    def apply(self, obj):
        if not self.dispatch.has_key(obj.__class__):
            print("Unmapped class passed to OM")
        else:
            self.dispatch[obj.__class__](obj)

    def dump(self):
        for _, v in self.ordersByClOrdID.items():
            print(v)
