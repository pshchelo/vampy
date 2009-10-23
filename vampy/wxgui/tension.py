#!/usr/bin/env python
'''Frame to display dilation vs tension plot and provide fitting facilities
'''
import wx

import matplotlib as mplt
mplt.use('WXAgg', warn=False)
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2
from matplotlib.figure import Figure

from vampy.common import DATWILDCARD
from vampy import analysis, output
from vampy.fitting import TENSFITMODELS

from libshch.common import WXPYTHON, SAVETXT
from libshch import wxutil

class TensionsFrame(wx.Frame):
    def __init__(self, parent, id, *inputdata):
        wx.Frame.__init__(self, parent, id, title = 'Dilation vs Tension')
        self.panel = wx.Panel(self, -1)
        
        self.inputdata = inputdata
        
        self.MakeModelPanel()
        self.MakePlotOptPanel()
        
        self.data = self.TensionModel(inputdata)
        
        self.statusbar = wxutil.PlotStatusBar(self)
        self.SetStatusBar(self.statusbar)
        
        self.toolbar = wxutil.SimpleToolbar(self, *self.ToolbarData())
        self.SetToolBar(self.toolbar)
        self.toolbar.Realize()
        
        self.MakeImagePanel()
        
        title = '%s : %s - %s'%(parent.imagedate, parent.imagedir, self.GetTitle())
        self.SetTitle(title)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.imgbox, 1, wx.GROW)
        
        sidevbox = wx.BoxSizer(wx.VERTICAL)
        
        sidevbox.Add(self.modelpanel, 0, wx.GROW)
        sidevbox.Add(self.plotoptpanel, 0, wx.GROW)
        
        hbox.Add(sidevbox, 0, wx.GROW)
        
        self.panel.SetSizer(hbox)
        
        self.SetFrameIcons(WXPYTHON, (16,24,32))
        hbox.Fit(self)
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
        self.axes.set_xlabel('$\\tau$, %s'%self.data['tensdim'][1], fontdict = labelfont)
        self.axes.set_ylabel('$\\alpha$')
        
        navtoolbar = NavigationToolbar2(self.canvas)
        navtoolbar.Realize()
        
        dim = self.data['tension'].shape[-1]
        self.slider = wxutil.DoubleSlider(self.panel, -1, (1, dim), 1, dim, gap=2)
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.slider)
        self.lowlabel = wx.StaticText(self.panel, -1, '%i'%self.slider.GetLow(), style=wx.ALIGN_CENTER|wx.ST_NO_AUTORESIZE)
        self.highlabel = wx.StaticText(self.panel, -1, '%i'%self.slider.GetHigh(), style=wx.ALIGN_CENTER|wx.ST_NO_AUTORESIZE)
        
        self.imgbox = wx.BoxSizer(wx.VERTICAL)
        self.imgbox.Add(self.canvas, 1, wx.GROW)
        self.imgbox.Add(navtoolbar, 0, wx.GROW)
        
        labelbox = wx.BoxSizer(wx.VERTICAL)
        labelbox.Add(self.lowlabel, 1, wx.GROW)
        labelbox.Add(self.highlabel, 1, wx.GROW)
        
        sliderbox = wx.BoxSizer(wx.HORIZONTAL)
        sliderbox.Add(labelbox, 0, wx.GROW)
        sliderbox.Add(self.slider, 1, wx.GROW)
        
        self.imgbox.Add(sliderbox, 0, wx.GROW)
    
    def init_plot(self):
        name = self.fitmodelchoice.GetStringSelection()
        self.fitmodel = TENSFITMODELS[name]
        xscalemode = self.xscalechoice.GetStringSelection()
        self.axes.set_xscale(xscalemode)
    
    def SetFrameIcons(self, artid, sizes):
        ib = wx.IconBundle()
        for size in sizes:
            ib.AddIcon(wx.ArtProvider.GetIcon(artid, size = (size,size)))
        self.SetIcons(ib)

    def ToolbarData(self):
        bmpsavetxt = wx.ArtProvider.GetBitmap(SAVETXT, wx.ART_TOOLBAR, (24,24))
        return ((
                (bmpsavetxt, 'Save Data File', 'Save Data File', False),
                 self.OnSave),
                )
        
    def MakeModelPanel(self):
        self.modelpanel = wx.Panel(self.panel, -1)
        
        labeltensmodel = wx.StaticText(self.modelpanel, -1, 'Tension')
        self.tensmodelchoice = wx.Choice(self.modelpanel, -1, choices = analysis.TENSMODELS.keys())
        self.tensmodelchoice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnTensionModel, self.tensmodelchoice)
        
        labelfit = wx.StaticText(self.modelpanel, -1, 'Fitting')
        self.fitmodelchoice = wx.Choice(self.modelpanel, -1, choices = TENSFITMODELS.keys())
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
    
    def MakePlotOptPanel(self):
        self.plotoptpanel = wx.Panel(self.panel, -1)
        
        labelxscale = wx.StaticText(self.plotoptpanel, -1, 'X scale')
        self.xscalechoice = wx.Choice(self.plotoptpanel, -1, choices = ['linear','log'])
        self.xscalechoice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnXScale, self.xscalechoice)
        
        plotoptstbox = wx.StaticBox(self.plotoptpanel, -1, 'Plot options')
        plotoptbox = wx.StaticBoxSizer(plotoptstbox, wx.VERTICAL)
        
        flexsz = wx.FlexGridSizer(cols=2)
        
        flexsz.Add(labelxscale, 0, wx.GROW|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        flexsz.Add(self.xscalechoice, 1, wx.GROW)
        
        plotoptbox.Add(flexsz, 0)
        
        self.plotoptpanel.SetSizer(plotoptbox)
    
    def TensionModel(self, inputdata):
        modelname = self.tensmodelchoice.GetStringSelection()
        model = analysis.TENSMODELS[modelname]
        tensiondata = model(*inputdata)
        return tensiondata
    
    def OnFitModel(self, evt):
        name = self.fitmodelchoice.GetStringSelection()
        self.fitmodel = TENSFITMODELS[name]
        self.Draw()
        evt.Skip()
        
    def OnTensionModel(self, evt):
        self.data = self.TensionModel(self.inputdata)
        self.Draw()
        evt.Skip()
    
    def OnXScale(self, evt):
        xscalemode = self.xscalechoice.GetStringSelection()
        self.axes.set_xscale(xscalemode)
        self.Draw()
        evt.Skip()

    def OnSlide(self, evt):
        self.lowlabel.SetLabel('%i'%self.slider.GetLow())
        self.highlabel.SetLabel('%i'%self.slider.GetHigh())
        self.Draw()
        evt.Skip()
        
    def OnSave(self, evt):
        savedlg = wx.FileDialog(self, 'Save data', self.GetParent().folder,
                            'tensions.dat', wildcard = DATWILDCARD, 
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
        x, sx = self.data['tension'][:,low-1:high]
        y, sy = self.data['dilation'][:,low-1:high]
                
        self.dataplot.set_data(x, y)
                
        fitmodel = analysis.TensionFitModel((x,sx),(y,sy), self.fitmodel)
        result = fitmodel.fit()
        
        func = fitmodel.get_func()
        self.fitplot.set_data(x, func(result['fit'], x))
        self.fitplot.set_label(self.fitmodelchoice.GetStringSelection())
        
        fittedparams = dict(zip(result['params'], zip(result['fit'], result['sd_fit'])))
        
        title = ''
        for key in fittedparams.keys():
            paramname, texparamname, paramdim, texparamdim = key
            value, error = fittedparams[key]
            title+='%s = %f $\\pm$ %f %s'%(texparamname, value, error, texparamdim)
            title += '\t'
        
        self.axes.set_title(title)
        self.axes.legend(loc=4)
        
        self.axes.relim()
        self.axes.autoscale_view(tight=False)
        self.canvas.draw()
