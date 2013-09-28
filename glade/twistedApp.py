# Looks like this has to be the very first thing our application sees
from twisted.internet import wxreactor
wxreactor.install()
import wx
from twisted.internet import reactor
from PhromsFrame import PhromsFrame

from phroms.util.WireObjects import *

# Need to 'know' about these since if the jelly code doesn't 

if __name__=='__main__':
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = PhromsFrame(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    #app.MainLoop()
    reactor.registerWxApp(app)
    reactor.run()
