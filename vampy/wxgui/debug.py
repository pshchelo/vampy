#!/usr/bin/env python
'''Frame for single image debugging
'''

import wx

import matplotlib as mplt
mplt.use('WXAgg', warn=False)
from matplotlib import cm as colormaps
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2
from matplotlib.figure import Figure

from scipy import ndimage

from libshch.common import WXPYTHON
from libshch import wxutil

class ImageDebugFrame(wx.Frame):
    def __init__(self, parent, id, img, out, extra_out):
        wx.Frame.__init__(self, parent, id, size=(800,600), title = 'Single Image Debug')
        
        self.statusbar = wxutil.PlotStatusBar(self)
        self.SetStatusBar(self.statusbar)
        
        panel = wx.Panel(self, -1)
        pansizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = Figure(facecolor = wxutil.rgba_wx2mplt(panel.GetBackgroundColour()))
        self.canvas = FigureCanvas(panel, -1, self.figure)
        self.canvas.mpl_connect('motion_notify_event', self.statusbar.SetPosition)
        pansizer.Add(self.canvas, 1, wx.GROW)
        
        navtoolbar = NavigationToolbar2(self.canvas)
        navtoolbar.Realize()
        pansizer.Add(navtoolbar, 0, wx.GROW)
        
        profile = extra_out['profile']
        self.profileplot = self.figure.add_subplot(221, title = 'Axis brightness profile')
        self.profileplot.plot(profile)
        sigma=parent.analysispanel.GetParams()['sigma']
        grad=ndimage.gaussian_gradient_magnitude(ndimage.gaussian_filter1d(profile,sigma) , sigma)
        multiplier = profile.max()/grad.max()/2
        grad *= multiplier
        self.profileplot.plot(grad)
        self.profileplot.axvline(extra_out['pip'], color = 'blue')
        self.profileplot.axvline(extra_out['asp'], color = 'yellow')
        self.profileplot.axvline(extra_out['ves'], color = 'green')
        
        self.imgplot = self.figure.add_subplot(222, title = 'Image')
        refs = extra_out['refs']
        for ref in refs:
            self.imgplot.plot([ref[0][1]], [ref[0][0]], 'yo') # due to format of refs
            
        self.imgplot.imshow(img, aspect = 'equal', extent = None, cmap = colormaps.gray)

        self.pipprofile1 = self.figure.add_subplot(223, title = 'Left pipette section')
        xleft = refs[0][0][1]
        pipprofile1 = img[:,xleft]
        self.pipprofile1.plot(pipprofile1)
        
        self.pipprofile2 = self.figure.add_subplot(224, title = 'Right pipette section')
        xright = refs[-1][0][1]
        pipprofile2 = img[:,xright]
        self.pipprofile2.plot(pipprofile2)
        
#        self.gradpipprofile1 = self.figure.add_subplot(325, title = 'Left pipette section gradient')
#        self.gradpipprofile1.plot(utils.get_gradient(pipprofile1, 3))
#        
#        self.gradpipprofile2 = self.figure.add_subplot(326, title = 'Right pipette section gradient')
#        self.gradpipprofile2.plot(utils.get_gradient(pipprofile2, 3))
#        
        panel.SetSizer(pansizer)
        panel.Fit()
        title = '%s : %s - Image %s - %s'%(parent.imagedate, parent.imagedir, parent.imgpanel.GetImgNo(), self.GetTitle())
        self.SetTitle(title)
        self.SetFrameIcons(WXPYTHON, (16,24,32))
        self.canvas.draw()
        
    def SetFrameIcons(self, artid, sizes):
        ib = wx.IconBundle()
        for size in sizes:
            ib.AddIcon(wx.ArtProvider.GetIcon(artid, size = (size,size)))
        self.SetIcons(ib)