#!/usr/bin/env python
'''Frame to display tensions plot and provide fitting facilities
'''
import wx

from numpy import pi

import matplotlib as mplt
mplt.use('WXAgg', warn=False)
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2
from matplotlib.figure import Figure

import vampy
from vampy import fitting, analysis, output

import libshch
from libshch import wxutil

class TensionsFrame(wx.Frame):
    def __init__(self, parent, id, *inputdata):
        wx.Frame.__init__(self, parent, id, title = 'Dilation vs Tension')
        self.panel = wx.Panel(self, -1)
        
        self.inputdata = inputdata
        
        self.MakeModelPanel()
        
        self.data = self.TensionModel(inputdata)
        
        self.statusbar = wxutil.PlotStatusBar(self)
        self.SetStatusBar(self.statusbar)
        
        self.toolbar = wxutil.SimpleToolbar(self, *self.ToolbarData())
        self.SetToolBar(self.toolbar)
        self.toolbar.Realize()
        
        self.MakeImagePanel()
        
        title = '%s : %s - %s'%(parent.imagedate, parent.imagedir, self.GetTitle())
        self.SetTitle(title)
        
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.imgbox, 1, wx.GROW)
        self.hbox.Add(self.modelpanel, 0, wx.GROW)
        
        self.panel.SetSizer(self.hbox)
        
        self.SetFrameIcons(libshch.WXPYTHON, (16,24,32))
        self.hbox.Fit(self)
        self.init_plot()
        self.Draw()
    
    def MakeImagePanel(self):
        self.figure = Figure(facecolor = wxutil.rgba_wx2mplt(self.panel.GetBackgroundColour()))
        self.canvas = FigureCanvas(self.panel, -1, self.figure)
        self.canvas.mpl_connect('motion_notify_event', self.statusbar.SetPosition)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_aspect('auto')

        self.dataplot, = self.axes.plot([], [], 'ro', label = 'Measured')
        self.fitplot, = self.axes.plot([],[])
        
        labelfont = {'fontsize':'large'}
        self.axes.set_xlabel(r'$\tau$', fontdict = labelfont)
        self.axes.set_ylabel(r'$\alpha$')
        
        navtoolbar = NavigationToolbar2(self.canvas)
        navtoolbar.Realize()
        
        dim = self.data['tension'].shape[-1]
        self.slider = wxutil.DoubleSlider(self.panel, -1, (0, dim), 0, dim, gap=2)
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.slider)
        
        self.imgbox = wx.BoxSizer(wx.VERTICAL)
        self.imgbox.Add(self.canvas, 1, wx.GROW)
        self.imgbox.Add(navtoolbar, 0, wx.GROW)
        self.imgbox.Add(self.slider, 0, wx.GROW)
    
    def init_plot(self):
        name = self.fitmodelchoice.GetStringSelection()
        self.fitmodel = vampy.TENSFITMODELS[name]
    
    def SetFrameIcons(self, artid, sizes):
        ib = wx.IconBundle()
        for size in sizes:
            ib.AddIcon(wx.ArtProvider.GetIcon(artid, size = (size,size)))
        self.SetIcons(ib)

    def ToolbarData(self):
        bmpsavetxt = wx.ArtProvider.GetBitmap(libshch.SAVETXT, wx.ART_TOOLBAR, (24,24))
        return ((
                (bmpsavetxt, 'Save Data File', 'Save Data File', False),
                 self.OnSave),
                )
        
    def MakeModelPanel(self):
        self.modelpanel = wx.Panel(self.panel, -1)
        
        labeltensmodel = wx.StaticText(self.modelpanel, -1, 'Tension')
        self.tensmodelchoice = wx.Choice(self.modelpanel, -1, choices = vampy.TENSMODELS.keys())
        self.tensmodelchoice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnTensionModel, self.tensmodelchoice)
        
        labelfit = wx.StaticText(self.modelpanel, -1, 'Fitting')
        self.fitmodelchoice = wx.Choice(self.modelpanel, -1, choices = vampy.TENSFITMODELS.keys())
        self.fitmodelchoice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnFitModel, self.fitmodelchoice)
        
        modelstbox = wx.StaticBox(self.modelpanel, -1, 'Model')
        modelbox = wx.StaticBoxSizer(modelstbox, wx.VERTICAL)
        
        flexsz = wx.FlexGridSizer(cols=2)
        
        flexsz.Add(labeltensmodel, 0, wx.GROW|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        flexsz.Add(self.tensmodelchoice, 1, wx.GROW)
        flexsz.Add(labelfit, 0, wx.GROW|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        flexsz.Add(self.fitmodelchoice, 1, wx.GROW)
        
        modelbox.Add(flexsz, 0)
        
        self.modelpanel.SetSizer(modelbox)
    
    def TensionModel(self, inputdata):
        modelname = self.tensmodelchoice.GetStringSelection()
        model = vampy.TENSMODELS[modelname]
        tensiondata = model(*inputdata)
        return tensiondata
    
    def OnFitModel(self, evt):
        name = self.fitmodelchoice.GetStringSelection()
        self.fitmodel = vampy.TENSFITMODELS[name]
        self.Draw()
        evt.Skip()
        
    def OnTensionModel(self, evt):
        self.data = self.TensionModel(self.inputdata)
        self.Draw()
        evt.Skip()
            
    def OnSlide(self, evt):
        self.Draw()
        evt.Skip()
        
    def OnSave(self, evt):
        savedlg = wx.FileDialog(self, 'Save data', self.GetParent().folder,
                            'tensions.dat', wildcard = vampy.DATWILDCARD, 
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if savedlg.ShowModal() == wx.ID_CANCEL:
            return
        datname = savedlg.GetPath()
        savedlg.Destroy()
        writer = output.DataWriter(self.data)
        mesg = writer.write_file(datname)
        if mesg:
            self.GetParent().OnError(mesg)
        
    def Draw(self):
        low, high = self.slider.GetValue()
        
        tau, tau_err = self.data['tension']
        alpha, alpha_err = self.data['dilation']
        
        x = tau[low:high+1]
        y = alpha[low:high+1]
        sx = tau_err[low:high+1]
        sy = alpha_err[low:high+1]
        
        self.dataplot.set_data(x, y)
                
        fitmodel = analysis.TensionFitModel((x,sx),(y,sy), self.fitmodel)
        result = fitmodel.fit()
        
        func = fitmodel.get_func()
        self.fitplot.set_data(x, func(result['fit'], x))
        self.fitplot.set_label(self.fitmodelchoice.GetStringSelection())
        
        fittedparams = dict(zip(result['params'], zip(result['fit'], result['sd_fit'])))
        
        title = ''
        for key in fittedparams.keys():
            paramname, texparamname = key
            value, error = fittedparams[key]
            title+='%s = %f $\\pm$ %f'%(texparamname, value, error)
            title += '\t'
        
        self.axes.set_title(title)
        self.axes.legend(loc=4)
        
        self.axes.relim()
        self.axes.autoscale_view(tight=True)
        self.canvas.draw()
