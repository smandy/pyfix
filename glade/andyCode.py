import wx

#custData  = [ "Ble

from pprint import pprint as pp

#from ListCtrl import HashableListView, BTListColumn

orderData = [ [ "Order1", 100, "CSCO"],
              [ "Order2", 200, "MSFT"],
              [ "Order3", 300, "IBM" ],
              [ "Order4", 324, "GLW" ] ]

import sys
sys.path.insert(0, '/Users/andy')

import random

stocks   = [ "CSCO","MSFT", "IBM", "GLW", "A","T", "YHOO", "GOOG" ]
qtys     = [ 100, 200, 500, 500, 500, 1000, 200]
accounts = [ "CAP", "ANDY", "ANGIE", "ILANA" ]
sides = [ "BUY", "SELL"]
orders = []
for i in range( 300 ):
    id = "orderid-%s" % i
    stock   = random.choice( stocks   )
    qty     = random.choice( qtys     )
    side    = random.choice( sides    )
    account = random.choice( accounts )
    orders.append( (id, stock, qty, side, account) )


from AutoKeyDict import AutoKeyDict

ordersByClient = AutoKeyDict( factory = lambda: [] )
for order in orders:
    ordersByClient[ order[4] ].append(order)

pp(ordersByClient)
    
import sys

class AccountList( wx.ListCtrl):
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        self.InsertColumn( 0, "Account")
        self.InsertColumn( 1, "Orders")
        accounts = ordersByClient.items()

        self.idxToAccount = {}
        
        for ( idx, (account, orders)) in enumerate(ordersByClient.items()):
            self.idxToAccount[idx] = account
            index = self.InsertStringItem( sys.maxint, account)
            self.SetStringItem( index, 1, str(len(orders)) )


    def accountSelectionChanged(self):
        accounts = self.selectedAccounts()
        #self.myList.setOrderData(accounts)

    def selectedAccounts(self):
        self.ret = []
        idx = -1
        
        while True:
            idx=self.GetNextSelected(idx)
            if idx==-1:
                return self.ret
            assert self.idxToAccount.has_key(idx)
            self.ret.append( self.idxToAccount[idx] )
            
    def onSelectionChange(self, event):
        print vars(event)


        
        
class MyList( wx.ListCtrl ):
    def setOrderData(self, clients):
       self.DeleteAllItems()
       #for client in clients:
       #    orders = ordersByClient[client]
       #    for ( idx, (id, stock, qty, side, account ) )  in enumerate(orders):
       ##        index = self.InsertStringItem( sys.maxint, id)
       #        #index = self.InsertStringItem( sys.maxint, px)
       #        #index = self.InsertStringItem( sys.maxint, id)
       #        self.SetStringItem( index, 1, str(stock) )
       #        self.SetStringItem( index, 2, str(qty) )
       #        self.SetStringItem( index, 3, str(side) )
       #        self.SetStringItem( index, 4, str(account) )
       #        self.SetItemData( index, idx)

    def addExecution(self, ex):
        index = self.InsertStringItem( sys.maxint, ex.clOrdID)
        #        #index = self.InsertStringItem( sys.maxint, px)
        #        #index = self.InsertStringItem( sys.maxint, id)
        self.SetStringItem( index, 1, str(ex.security.ticker) )
        self.SetStringItem( index, 2, str(ex.lastShares) )
        self.SetStringItem( index, 3, str(ex.side) )
        #self.SetStringItem( index, 4, ex.account.name)
        self.SetItemData( index, self.idx)
        self.idx += 1
        #InsertRow( self.idx, BTListRow( None,  { 'clOrdID' : clOrdID } ) )
        
        
    def __init__(self, *args, **kwargs):
        #self.columns = {
        #'clOrdID': BTListColumn( "ClOrdId", "XYZ" )
        #}
        self.column_order    = [ 'clOrdID' ]
        self.enabled_columns = [ 'clOrdID' ]

        wx.ListCtrl.__init__(self, *args, **kwargs)
        
        #HashableListView.__init__(self, *args, **kwargs)

        #Hasht.__init__(self, *args, **kwargs)
        self.InsertColumn( 0, "OrderID")
        self.InsertColumn( 1, "Stock")
        self.InsertColumn( 2, "Qty")
        self.InsertColumn( 3, "Side")
        self.InsertColumn( 4, "Account")


        self.idx = 0
        #self.setOrderData( [ random.choice( ordersByClient.keys() ) ] )

from ListCtrl import BTListColumn, HashableListView, BTListRow

class MyList( HashableListView ):
    def __init__(self, parent, *args, **kwargs):
        self.column_order = ['execType']
        self.columns = {
            'execType' : BTListColumn( 'ExecType', "ACK" , enabled=True)
            }
        HashableListView.__init__(self, parent )
        self.set_default_widths()

    def setOrderData(self, clients):
       self.DeleteAllItems()
       #for client in clients:
       #    orders = ordersByClient[client]
       #    for ( idx, (id, stock, qty, side, account ) )  in enumerate(orders):
       ##        index = self.InsertStringItem( sys.maxint, id)
       #        #index = self.InsertStringItem( sys.maxint, px)
       #        #index = self.InsertStringItem( sys.maxint, id)
       #        self.SetStringItem( index, 1, str(stock) )
       #        self.SetStringItem( index, 2, str(qty) )
       #        self.SetStringItem( index, 3, str(side) )
       #        self.SetStringItem( index, 4, str(account) )
       #        self.SetItemData( index, idx)

    def addExecution(self, ex):
        print "MyList.addExecution"
        HashableListView.InsertRow( self, ex.execID, BTListRow(None, 
            {
                'execType' : ex.execType.name
                } ) )

        self.OnEraseBackground()
        if 0:
            index = self.InsertStringItem( sys.maxint, ex.clOrdID)
            #        #index = self.InsertStringItem( sys.maxint, px)
            #        #index = self.InsertStringItem( sys.maxint, id)
            self.SetStringItem( index, 1, str(ex.security.ticker) )
            self.SetStringItem( index, 2, str(ex.lastShares) )
            self.SetStringItem( index, 3, str(ex.side) )
            #self.SetStringItem( index, 4, ex.account.name)
            self.SetItemData( index, self.idx)
            self.idx += 1
            #InsertRow( self.idx, BTListRow( None,  { 'clOrdID' : clOrdID } ) )
