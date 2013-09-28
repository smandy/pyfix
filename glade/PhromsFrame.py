# -*- coding: us-ascii -*-
# generated by wxGlade 0.6.3 on Sun Jul 13 20:19:10 2008

import wx

from andyCode import AccountList, MyList
from twisted.spread   import pb
from twisted.internet import reactor

# begin wxGlade: dependencies
from GLCanvas import ConeCanvas, DotsCanvas
# end wxGlade

# begin wxGlade: extracode

# end wxGlade

class PhromsFrame(wx.Frame, pb.Referenceable):
    def __init__(self, *args, **kwds):
        # begin wxGlade: PhromsFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.sizer_2_staticbox = wx.StaticBox(self.panel_1, -1, "")
        self.button_1 = wx.Button(self.panel_1, -1, "StartSender")
        self.button_2 = wx.Button(self.panel_1, -1, "Die")
        self.button_3 = wx.Button(self.panel_1, -1, "button_3")
        self.button_4 = wx.Button(self.panel_1, -1, "button_4")
        self.txtCommand = wx.TextCtrl(self.panel_1, -1, "", style=wx.TE_PROCESS_ENTER)
        self.panel_2 = ConeCanvas(self.panel_1, -1)
        self.panel_3 = DotsCanvas(self.panel_1, -1)
        self.accountList = AccountList(self.panel_1, -1, style=wx.LC_REPORT|wx.LC_NO_HEADER|wx.SUNKEN_BORDER)
        self.myList = MyList(self.panel_1, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.text_ctrl_1 = wx.TextCtrl(self.panel_1, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onButton1, self.button_1)
        self.Bind(wx.EVT_BUTTON, self.onButtonTwo, self.button_2)
        self.Bind(wx.EVT_BUTTON, self.onButtonThree, self.button_3)
        self.Bind(wx.EVT_TEXT_ENTER, self.onEnter, self.txtCommand)
        self.Bind(wx.EVT_TEXT, self.onText, self.txtCommand)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.accountSelectionChanged, self.accountList)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.accountSelectionChanged, self.accountList)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.itemSelected, self.myList)
        # end wxGlade
        
        self.accountList.myList = self.myList
        self.connected = None
        self.idx = 0
        self.getConnected()
        
        # XXX wire this a little better maybe?
        self.panel_3.perspective = self
        self.prices = {}
        self.deltas = {}

    def getConnected(self):
        """Test to see if this mehtod survives a glade save"""
        assert not self.connected
        factory = pb.PBClientFactory()
        x = reactor.connectTCP("localhost", 2224, factory)
        print "result of connectTCP is  is %s" % x
        return factory.getRootObject().addCallback( self._connected)

    def _connected(self, rootObj):
        print "Connected"
        self.root = rootObj
        self.root.callRemote('registerFillListener', self ).addCallback( self._callComplete, ['registerFill'] ).addCallback( self._callComplete, ['Wayhey'] )
        self.root.callRemote( 'addGui' , self ).addCallback( self._callComplete, ['registerGui'] ).addErrback( self.registerFailed )
        self.root.callRemote('registerOrderStateListener', self).addCallback(self._callComplete, 'resisterStateListener' )

    def registerFailed(self):
        # PANIC HERE - get disconnected - clear all guis
        print "COULDN'T REGISTR GUI!!!!"
        pass

    def logToGui(self,txt):
        self.text_ctrl_1.AppendText( txt + "\n")
        
    def remote_onLog(self, txt):
        self.logToGui( txt)

    def remote_onTick(self, sec_px):
        self.logToGui( "OnTick : %s" % str(sec_px))
        sec, px = sec_px
        if self.deltas.has_key( sec):
            self.deltas[sec] = px - self.deltas[sec]
        else:
            self.deltas[sec] = 0.0
        self.prices[sec] = px
        reactor.callLater(0, self.panel_3.OnDraw )
        
    def remote_onFill(self, *args): #   [ (ord,exec) ]
        print "onFill was passed %s" % str(args)
        clOrdID = args[0][1].clOrdID
        self.myList.addExecution( args[0][1])
        self.idx += 1

    def remote_onOrderState(self, *args):
        print "onOrderState = %s" % str(args)

    def _callComplete(self, *args):
        print "call is complete %s" % str(args)
        self.connected = True

    def __set_properties(self):
        # begin wxGlade: PhromsFrame.__set_properties
        self.SetTitle("Phroms")
        self.SetSize((1200, 1155))
        self.myList.SetToolTipString("Your Order List")
        self.panel_1.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.panel_1.SetForegroundColour(wx.Colour(0, 238, 238))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: PhromsFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.StaticBoxSizer(self.sizer_2_staticbox, wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5.Add(self.button_1, 1, 0, 0)
        sizer_5.Add(self.button_2, 1, 0, 0)
        sizer_5.Add(self.button_3, 1, 0, 0)
        sizer_5.Add(self.button_4, 1, 0, 0)
        sizer_5.Add(self.txtCommand, 2, 0, 0)
        sizer_2.Add(sizer_5, 0, 0, 0)
        sizer_3.Add(self.panel_2, 1, wx.EXPAND, 0)
        sizer_3.Add(self.panel_3, 1, wx.EXPAND, 0)
        sizer_2.Add(sizer_3, 1, wx.EXPAND, 0)
        sizer_2.Add(self.accountList, 1, wx.EXPAND, 0)
        sizer_2.Add(self.myList, 1, wx.EXPAND, 0)
        sizer_2.Add(self.text_ctrl_1, 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def onButton1(self, event): # wxGlade: PhromsFrame.<event_handler>
        if self.connected:
            self.root.callRemote('startOrderSender' ).addCallback( self._callComplete, ['startOrderSender'] )
        #event.Skip()

    def onButtonTwo(self, event): # wxGlade: PhromsFrame.<event_handler>
        if self.connected:
            self.root.callRemote('die')

    def onButtonThree(self, event): # wxGlade: PhromsFrame.<event_handler>
        print "Event handler `onButtonThree' not implemented!"
        event.Skip()

    def itemSelected(self, event): # wxGlade: PhromsFrame.<event_handler>
        print "Event handler `itemSelected' not implemented!"
        event.Skip()

    def accountSelectionChanged(self, event): # wxGlade: PhromsFrame.<event_handler>
        #print "Event handler `onSelectionChange' not implemented"
        print self.accountList.accountSelectionChanged()
        event.Skip()

    def onSelectionChange(self, event): # wxGlade: PhromsFrame.<event_handler>
        print "Event handler `onSelectionChange' not implemented"
        event.Skip()

    def onEnter(self, event): # wxGlade: PhromsFrame.<event_handler>
        #print "onTextEnter"
        if self.connected:
            self.root.callRemote( "onGuiTextCommand" , self.txtCommand.GetValue() )
        print self.txtCommand.GetValue()

    def onText(self, event): # wxGlade: PhromsFrame.<event_handler>
        #print "Event handler `onText' not implemented"
        event.Skip()

# end of class PhromsFrame

