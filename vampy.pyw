#!/usr/bin/env python
"Main file for VAMPy project"
import wx
from libshch import wxutil
import vampy.wxgui.uimain

class VamPyApp(wx.App):
    '''Actual wxPython application'''
    def OnInit(self):
        customartprovider = wxutil.CustomArtProvider()
        wx.ArtProvider.Push(customartprovider)
        frame = vampy.wxgui.uimain.VampyFrame(parent=None, id=-1)
        frame.Show()
        return True   

app = VamPyApp(False)
app.MainLoop()