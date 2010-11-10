#!/usr/bin/env python
'''Frame to display dilation vs tension plot and provide fitting facilities
'''
import wx

import numpy as np
import matplotlib as mplt
mplt.use('WXAgg', warn=False)
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2
from matplotlib.figure import Figure

from calc.common import DATWILDCARD
from calc import analysis, load, output
from calc.fitting import TENSFITMODELS

from resources import PLOT, SAVETXT, OPENTXT
import widgets

class TensionsFrame(wx.Frame):
    def __init__(self, parent, id, *inputdata):
        wx.Frame.__init__(self, parent, id, title = 'Dilation vs Tension')
        
        self.panel = wx.Panel(self, -1)

        self.toolbar = widgets.SimpleToolbar(self, *self.ToolbarData())
        self.SetToolBar(self.toolbar)
        self.toolbar.Realize()
        
        self.statusbar = widgets.PlotStatusBar(self)
        self.SetStatusBar(self.statusbar)
               
        self.MakeModelPanel()
        self.MakePlotOptPanel()
        
        if inputdata:
            self.inputdata = inputdata
            self.data = self.TensionData(inputdata)
        else:
            self.data={}
            self.data['tensdim'] = ('tension units','tension units')
            self.data['tension']=np.array(((),()))
            self.data['dilation']=np.array(((),()))
        
        self.MakeImagePanel()
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.imgbox, 1, wx.GROW)
        
        sidevbox = wx.BoxSizer(wx.VERTICAL)
        
        sidevbox.Add(self.modelpanel, 0, wx.GROW)
        sidevbox.Add(self.plotoptpanel, 0, wx.GROW)
        
        hbox.Add(sidevbox, 0, wx.GROW)
        
        self.panel.SetSizer(hbox)
        
        self.SetFrameIcons(PLOT, (16,24,32))
        hbox.Fit(self)
        self.init_plot()
        
        self.Draw()
        
    def MakeImagePanel(self):
        self.figure = Figure(facecolor = widgets.rgba_wx2mplt(self.panel.GetBackgroundColour()))
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
        self.slider = widgets.DoubleSlider(self.panel, -1, (1, dim), 1, dim, gap=2)
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.slider)
        self.lowlabel = wx.StaticText(self.panel, -1, '  %i'%self.slider.GetLow(), style=wx.ALIGN_CENTER|wx.ST_NO_AUTORESIZE)
        self.highlabel = wx.StaticText(self.panel, -1, '  %i'%self.slider.GetHigh(), style=wx.ALIGN_CENTER|wx.ST_NO_AUTORESIZE)
        
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
        bmpsavetxt = wx.ArtProvider.GetBitmap(SAVETXT, wx.ART_TOOLBAR, (32,32))
        bmpopentxt = wx.ArtProvider.GetBitmap(OPENTXT, wx.ART_TOOLBAR, (32,32))
        return (
                ((bmpopentxt, 'Open Data file', 'Open tensions data file', False),
                 self.OnOpen),
                ((bmpsavetxt, 'Save Data File', 'Save tensions data file', False),
                 self.OnSave),
                )
        
    def MakeModelPanel(self):
        self.modelpanel = wx.Panel(self.panel, -1)
        
        labeltensmodel = wx.StaticText(self.modelpanel, -1, 'Tension')
        self.tensmodelchoice = wx.Choice(self.modelpanel, -1, choices = analysis.TENSMODELS.keys())
        self.tensmodelchoice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnChangeTensionModel, self.tensmodelchoice)
        
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
    
    def TensionData(self, inputdata):
        modelname = self.tensmodelchoice.GetStringSelection()
        model = analysis.TENSMODELS[modelname]
        tensiondata = model(*inputdata)
        return tensiondata
    
    def OnFitModel(self, evt):
        name = self.fitmodelchoice.GetStringSelection()
        self.fitmodel = TENSFITMODELS[name]
        self.Draw()
        evt.Skip()
        
    def OnChangeTensionModel(self, evt):
        self.data = self.TensionData(self.inputdata)
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
            evt.Skip()
            return
        datname = savedlg.GetPath()
        savedlg.Destroy()
        header = 'Vesicle tensions, %s model\n'%self.tensmodelchoice.GetStringSelection()
        for key in self.fittedparams:
            paramname, texparamname, paramdim, texparamdim = key
            value, error = self.fittedparams[key]
            header += '#%s = %f +- %f %s\n'%(paramname, value, error, paramdim)
        header +='#'
        writer = output.DataWriter(self.data, title=header)
        mesg = writer.write_file(datname)
        if mesg:
            self.GetParent().OnError(mesg)
        evt.Skip()
    
    def OnOpen(self, evt):
        fileDlg = wx.FileDialog(self, message='Choose Dilations/Tensions file...',
                                 wildcard=DATWILDCARD, style=wx.FD_OPEN)
        if fileDlg.ShowModal() != wx.ID_OK:
            fileDlg.Destroy()
            return
        filename = fileDlg.GetPath()
        fileDlg.Destroy()
        
        self.data, msg = load.read_tensions(filename)
        if msg:
            self.OnError(msg)
            return
        else:
            dim = self.data['tension'].shape[-1]
            self.slider.SetRange(1, dim)
            self.slider.SetValue((1,dim))
            self.axes.set_xlabel('$\\tau$, %s'%self.data['tensdim'][1])
            self.OnSlide(evt)
            self.Draw()
        evt.Skip()
        
    def OnError(self, msg):
        """
        Display an error dialog
        @param msg: error message to display (type = string)
        """
        errDlg = wx.MessageDialog(self, msg, "Error!", wx.ICON_ERROR)
        errDlg.ShowModal()
        errDlg.Destroy()
    
    def Draw(self):
        low, high = self.slider.GetValue()
        x, sx = self.data['tension'][:,low-1:high]
        y, sy = self.data['dilation'][:,low-1:high]
        
        self.dataplot.set_data(x, y)
                
        fitmodel = analysis.TensionFitModel((x,sx),(y,sy), self.fitmodel, self.data['tensdim'])
        result = fitmodel.fit()
        
        func = fitmodel.get_func()
        self.fitplot.set_data(x, func(result['fit'], x))
        self.fitplot.set_label(self.fitmodelchoice.GetStringSelection())
        
        self.fittedparams = dict(zip(result['params'], zip(result['fit'], result['sd_fit'])))
        
        title = ''
        for key in self.fittedparams.keys():
            paramname, texparamname, paramdim, texparamdim = key
            value, error = self.fittedparams[key]
            title+='%s = %.2f $\\pm$ %.2f %s'%(texparamname, value, error, texparamdim)
            title += '\t'
        
        self.axes.set_title(title)
        self.axes.legend(loc=4)
        
        self.axes.relim()
        if mplt.__version__ >= '0.99': #  to fight strange bug under Fedora8 linux matplotlib 0.98.3
            self.axes.autoscale_view(tight=False)
        else:
            self.axes.set_xlim(x.min()-x.ptp()*0.05, x.max()+x.ptp()*0.05)
            self.axes.set_ylim(y.min()-y.ptp()*0.05, y.max()+y.ptp()*0.05)

        self.canvas.draw()
