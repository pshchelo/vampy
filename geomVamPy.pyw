#!/usr/bin/env python
"Only tensions analysis for VAMPy project"
import wx
from wxgui import geometry, resources

class tensVamPyApp(wx.App):
    '''Actual wxPython application'''
    def OnInit(self):
        customartprovider = resources.CustomArtProvider()
        wx.ArtProvider.Push(customartprovider)
        frame = geometry.GeometryFrame(parent=None, id=-1)
        frame.Show()
        return True   

app = tensVamPyApp(False)
app.MainLoop()