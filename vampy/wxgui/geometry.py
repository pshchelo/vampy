#!/usr/bin/env python
'''Frame that displays vesicle geometry data
'''

import wx

import matplotlib as mplt
mplt.use('WXAgg', warn=False)
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2
from matplotlib.figure import Figure

import vampy
from vampy import output

from libshch.common import *
from libshch import util, wxutil

class GeometryFrame(wx.Frame):
    def __init__(self, parent, id, argsdict):
        wx.Frame.__init__(self, parent, id, size = (1024,768), title = 'Vesicle Geometry')
        
        self.data = argsdict
        
        self.statusbar = wxutil.PlotStatusBar(self)
        self.SetStatusBar(self.statusbar)
        
        self.toolbar = wxutil.SimpleToolbar(self, *self.ToolbarData())
        self.SetToolBar(self.toolbar)
        self.toolbar.Realize()
        
        panel = wx.Panel(self, -1)
        pansizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = Figure(facecolor = wxutil.rgba_wx2mplt(panel.GetBackgroundColour()))
        self.figure.suptitle('Pipette radius (px): %f +-%f'%tuple(self.data['piprad']))
        self.canvas = FigureCanvas(panel, -1, self.figure)
        self.canvas.mpl_connect('motion_notify_event', self.statusbar.SetPosition)
        pansizer.Add(self.canvas, 1, wx.GROW)
        titles = dict(aspl='Aspirated Length',
                      vesrad='Vesicle Radius',
                      area='Area',
                      vesl='Outer Radius',
                      volume='Volume',
                      angle = 'Axis angle',
                      metrics = 'metric')
        toplot = ['aspl', 'vesl', 'metrics', 'area']
        self.plots = {}
        x = range(1, len(argsdict[toplot[0]][0])+1)
        n,m = util.grid_size(len(toplot))
        for index, item in enumerate(toplot):
            y, y_err = self.data[item]
            plottitle = titles[item]
            plot = self.figure.add_subplot(n,m,index+1, title = plottitle)
            plot.errorbar(x, y, y_err, fmt='bo-', label=plottitle)
            self.plots[item] = plot
#       
        navtoolbar = NavigationToolbar2(self.canvas)
        navtoolbar.Realize()
        pansizer.Add(navtoolbar, 0, wx.GROW)
        
        panel.SetSizer(pansizer)
        panel.Fit()
        title = '%s : %s - %s'%(parent.imagedate, parent.imagedir, self.GetTitle())
        self.SetTitle(title)
        self.SetFrameIcons(WXPYTHON, (16,24,32))
        self.canvas.draw()
    
    def SetFrameIcons(self, artid, sizes):
        ib = wx.IconBundle()
        for size in sizes:
            ib.AddIcon(wx.ArtProvider.GetIcon(artid, size = (size,size)))
        self.SetIcons(ib)
        
    def ToolbarData(self):
        bmpsavetxt = wx.ArtProvider.GetBitmap(SAVETXT, wx.ART_TOOLBAR, (24,24))
        return ((
                (bmpsavetxt, 'Save Data File', 'Save Dat File', False),
                 self.OnSave),
                )
        
    def OnSave(self, evt):
        savedlg = wx.FileDialog(self, 'Save data', self.GetParent().folder,
                            'images.dat', wildcard = vampy.DATWILDCARD, 
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if savedlg.ShowModal() == wx.ID_CANCEL:
            return
        datname = savedlg.GetPath()
        savedlg.Destroy()
        writer = output.DataWriter(self.data)
        mesg = writer.write_file(datname)
        if mesg:
            self.GetParent().OnError(mesg)