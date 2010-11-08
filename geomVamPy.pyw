#!/usr/bin/env python
"Only tensions analysis for VAMPy project"
import wx
from libshch import wxutil
import vampy.wxgui.geometry

class tensVamPyApp(wx.App):
    '''Actual wxPython application'''
    def OnInit(self):
        customartprovider = wxutil.CustomArtProvider()
        wx.ArtProvider.Push(customartprovider)
        frame = vampy.wxgui.geometry.GeometryFrame(parent=None, id=-1)
        frame.Show()
        return True   

app = tensVamPyApp(False)
app.MainLoop()