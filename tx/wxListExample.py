import sys

import  wx
import  wx.lib.mixins.listctrl  as  listmix

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame("HelloWorld", (50,60), (450,340))
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True
    
class TestListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.InsertColumn(0, "Name")
        self.InsertColumn(1, "SomethingElse")

        idx = self.InsertStringItem( sys.maxint, "Hello")
        print "Idx = %s" % idx
        self.SetStringItem(idx, 0, "HELLO")
        self.SetStringItem(idx, 1, "THERE")

class MyFrame(wx.Frame):
    def __init__(self, title, pos, size):
        wx.Frame.__init__(self, None, -1, title, pos, size)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.l = TestListCtrl( self, wx.NewId() , style=wx.LC_REPORT 
                                 #| wx.BORDER_SUNKEN
                                 | wx.BORDER_NONE
                                 | wx.LC_EDIT_LABELS
                                 | wx.LC_SORT_ASCENDING)
        sizer.Add(self.l, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def OnQuit(self):
        print "I'm melting"
        self.Close()

if __name__=='__main__':
    app = MyApp(False)
    app.MainLoop()
