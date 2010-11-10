#!/usr/bin/env python
"Only tensions analysis for VAMPy project"
import wx
from vampy.wxgui import tension, resources

class tensVamPyApp(wx.App):
    '''Actual wxPython application'''
    def OnInit(self):
        customartprovider = resources.CustomArtProvider()
        wx.ArtProvider.Push(customartprovider)
        frame = tension.TensionsFrame(parent=None, id=-1)
        frame.Show()
        return True   

app = tensVamPyApp(False)
app.MainLoop()