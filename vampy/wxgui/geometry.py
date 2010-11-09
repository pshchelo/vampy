#!/usr/bin/env python
'''Frame that displays vesicle geometry data

'''
import os.path

import wx

import matplotlib as mplt
mplt.use('WXAgg', warn=False)
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2
from matplotlib.figure import Figure

from vampy import load, output, analysis
from vampy.common import DATWILDCARD
from dialogs import VampyOtherUserDataDialog
from tension import TensionsFrame

from libshch.common import MEASURE, SAVETXT, OPENTXT, PLOT, PREFS
from libshch import util, wxutil

class GeometryFrame(wx.Frame):
    def __init__(self, parent, id, argsdict=None):
        wx.Frame.__init__(self, parent, id, size = (1024,768), title = 'Vesicle Geometry')
        
        self.statusbar = wxutil.PlotStatusBar(self)
        self.SetStatusBar(self.statusbar)
        
        self.toolbar = wxutil.SimpleToolbar(self, *self.ToolbarData())
        self.SetToolBar(self.toolbar)
        self.toolbar.Realize()
        
        panel = wx.Panel(self, -1)
        pansizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = Figure(facecolor = wxutil.rgba_wx2mplt(panel.GetBackgroundColour()))
        self.canvas = FigureCanvas(panel, -1, self.figure)
        self.canvas.mpl_connect('motion_notify_event', self.statusbar.SetPosition)
        pansizer.Add(self.canvas, 1, wx.GROW)
        
        navtoolbar = NavigationToolbar2(self.canvas)
        navtoolbar.Realize()
        pansizer.Add(navtoolbar, 0, wx.GROW)
        
        panel.SetSizer(pansizer)
        panel.Fit()
        self.SetFrameIcons(MEASURE, (16,24,32))
        self.title_tmpl = '%%s : %%s - %s'%self.GetTitle()
        
        self.data = {}
        self.folder=''
        if argsdict:
            self.data = argsdict
            self.SetWindowTitle(parent.imagedate, parent.imagedir)
            self.folder = self.GetParent().folder
        self.Draw()
        
    def SetFrameIcons(self, artid, sizes):
        ib = wx.IconBundle()
        for size in sizes:
            ib.AddIcon(wx.ArtProvider.GetIcon(artid, size = (size,size)))
        self.SetIcons(ib)
        
    def SetWindowTitle(self, *args):
        title = self.title_tmpl%args[0:2]
        self.SetTitle(title)
        
    def ToolbarData(self):
        bmpsavetxt = wx.ArtProvider.GetBitmap(SAVETXT, wx.ART_TOOLBAR, (32,32))
        bmpopentxt = wx.ArtProvider.GetBitmap(OPENTXT, wx.ART_TOOLBAR, (32,32))
        bmpprefs = wx.ArtProvider.GetBitmap(PREFS, wx.ART_TOOLBAR, (32,32))
        bmpplot = wx.ArtProvider.GetBitmap(PLOT, wx.ART_TOOLBAR, (32,32))
        return (
                (
                (bmpopentxt, 'Open Data file', 'Open geometry data file', False),
                self.OnOpen),
                ((bmpsavetxt, 'Save Data File', 'Save geometry data file', False),
                self.OnSave),
                ((bmpprefs, 'Choose plots', 'Choose what plots to draw', False),
                self.OnPlotChoice),
                ((bmpplot, 'Fit!', 'Open fitting window', False),
                self.OnFit),
                )
    
    def OnOpen(self, evt):
        fileDlg = wx.FileDialog(self, message='Choose hand-measured geometry file...',
                                 wildcard=DATWILDCARD, style=wx.FD_OPEN)
        
        if fileDlg.ShowModal() != wx.ID_OK:
            fileDlg.Destroy()
            return
        filename = fileDlg.GetPath()
        fileDlg.Destroy()
        self.folder = os.path.dirname(filename)
        self.SetWindowTitle(os.path.basename(self.folder), os.path.basename(filename))
        
        measured, mesg = load.read_geometry_simple(filename)
        if not measured:
            self.OnError(mesg)
            return
        geometrydata, mesg = analysis.get_geometry(measured)
        if mesg:
            self.OnError(mesg)
            return
        self.userdata = self.GetExtraUserData(len(measured['asps'][0]))
        aver = self.userdata[-1]
        self.data = analysis.averageImages(aver, **geometrydata)
        self.Draw()
        evt.Skip()
    
    def OnFit(self, evt):
        pressures, pressacc, scale = self.userdata[:3]
        tensionframe = TensionsFrame(self, -1, pressures, pressacc, scale, self.data)
        tensionframe.Show()
        evt.Skip()
    
    def OnPlotChoice(self, evt):
        evt.Skip()
    
    def GetExtraUserData(self, NofPoints):
        fileDlg = wx.FileDialog(self, message="Choose a pressure protocol file",
                                defaultDir = self.folder, style = wx.OPEN,
                                wildcard = DATWILDCARD)
        if fileDlg.ShowModal() != wx.ID_OK:
            fileDlg.Destroy()
            return
        pressfilename = fileDlg.GetPath()
        fileDlg.Destroy()
        
        dlg = VampyOtherUserDataDialog(self, -1)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        stage, scale, pressacc = dlg.GetData()
        dlg.Destroy()
        pressures, mesg = load.read_pressures_file(pressfilename, stage)
        if mesg:
            self.OnError(mesg)
            return None
        if NofPoints % len(pressures) != 0:
            self.OnError('Number of images is not multiple of number of pressures!')
            return
        else:
            aver = NofPoints/len(pressures)#number of images to average within

        return pressures, pressacc, scale, aver
        
    def OnSave(self, evt):
        """Save calculated geometry as text file."""
        savedlg = wx.FileDialog(self, 'Save data', self.folder,
                            'images.dat', wildcard = DATWILDCARD, 
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if savedlg.ShowModal() == wx.ID_CANCEL:
            return
        datname = savedlg.GetPath()
        savedlg.Destroy()
        writer = output.DataWriter(self.data, title='Vesicle geometry')
        mesg = writer.write_file(datname)
        if mesg:
            self.OnError(mesg)
    
    def OnError(self, msg):
        """Display an error dialog
        
        @param msg: error message to display (type = string)
        """
        errDlg = wx.MessageDialog(self, str(msg), "Error!", wx.ICON_ERROR|wx.OK)
        errDlg.ShowModal()
        errDlg.Destroy()
    
    def Draw(self):
        """Refresh the plot(s)"""
        titles = dict(aspl='Aspirated Length',
                      vesrad='Vesicle Radius',
                      area='Area',
                      vesl='Outer Radius',
                      volume='Volume',
                      angle = 'Axis angle',
                      metrics = 'metric')
        toplot = ['aspl', 'vesl', 'metrics', 'area']
        self.plots = {}
        x = range(1, len(self.data.get(toplot[0], [[],[]])[0])+1)
        n,m = util.grid_size(len(toplot))
        self.figure.clear()
        for index, item in enumerate(toplot):
            y, y_err = self.data.get(item, [[],[]])
            plottitle = titles[item]
            plot = self.figure.add_subplot(n,m,index+1, title = plottitle)
            if x:
                plot.errorbar(x, y, y_err, fmt='bo-', label=plottitle)
#            self.plots[item] = plot
        self.figure.suptitle('Pipette radius (px): %f +-%f'%tuple(self.data.get('piprad', (0,0))))
        self.canvas.draw()
