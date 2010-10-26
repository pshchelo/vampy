#!/usr/bin/env python
"Only tensions analysis for VAMPy project"
import wx
from libshch import wxutil
import vampy.wxgui.tension

class tensVamPyApp(wx.App):
    '''Actual wxPython application'''
    def OnInit(self):
        customartprovider = wxutil.CustomArtProvider()
        wx.ArtProvider.Push(customartprovider)
        frame = vampy.wxgui.tension.TensionsFrame(parent=None, id=-1)
        frame.Show()
        return True   

app = tensVamPyApp(False)
app.MainLoop()