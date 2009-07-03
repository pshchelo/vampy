#!/usr/bin/env python
"""
wxPython GUI for VAMP project
TODO: create (or copy?) a wx.Frame subclass for holding a matplotlib plot,
probably with the toolbar and status bar
"""
import glob, sys, os
OWNPATH = os.path.dirname(sys.argv[0])

import wx

from numpy import pi, log, empty
import matplotlib as mplt
mplt.use('WXAgg', warn=False)
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg
from matplotlib.figure import Figure

import load as vload
import features as vfeat
import analysis as vanalys
import fitting as vfit
import output as vout

from myutils.wxutils import NumValidator, rgba_wx2mplt, DoubleSlider, GetResIconBundle, GetResBitmap
from myutils import utils

SIDES = ['left','right','top','bottom']
DATWILDCARD = "Data files (TXT, CSV, DAT)|*.txt;*.TXT;*.csv;*.CSV;*.dat;*.DAT | All files (*.*)|*.*"
DEFAULT_SCALE = '0.3225'  # micrometer/pixel, Teli CS3960DCL, 20x overall magnification
DEFAULT_PRESSACC = '0.00981'  # 1 micrometer of water stack
CFG_FILENAME = 'vampy.cfg'
FRAME_ICON = 'wxpython-multi.ico'
SAVETXT_ICON = 'savetxt24.png'

class VampyMenuBar(wx.MenuBar):
    '''Menu Bar for wxPython VAMP front-end'''
    def __init__(self, parent):
        wx.MenuBar.__init__(self)
        for eachMenuData in self.MenuData(parent):
            menuLabel, menuItems = eachMenuData
            self.Append(self.CreateMenu(menuItems, parent), menuLabel)

    def MenuData(self, parent):
        return [["&File", [
                ("&Open Folder...\tCtrl+O", "Open folder with images", parent.OnOpenFolder),
                ("", "", ""),
                ("&Exit", "Exit application", parent.OnExit)]],
                ["&Help", [
                ("&Help", "Display help", parent.OnHelp),
                ("&About...", "Show info about application", parent.OnAbout)]],
                ["Debug", [
                ("Reload GUI (careful!)", "Reload User Interface", parent.OnReloadGUI),
                ("Reload Math", "Reload all dependencies", parent.OnReloadMath),
                ("Debug image", " current", parent.OnDebugImage)]]]

    def CreateMenu(self, menuData, parent):
        menu = wx.Menu()
        for eachLabel, eachStatus, eachHandler in menuData:
            if not eachLabel:
                menu.AppendSeparator()
                continue
            menuItem = menu.Append(-1, eachLabel, eachStatus)
            parent.Bind(wx.EVT_MENU, eachHandler, menuItem)
        return menu

class VampyStatusBar(wx.StatusBar):
    '''Status Bar for wxPython VAMP frontend'''
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent)
        self.SetFieldsCount(2)
        
    def SetPosition(self, evt):
        if evt.inaxes:
            x = evt.xdata
            y = evt.ydata
            self.SetStatusText('x = %f, y = %f'%(x, y), 1)

class VampyToolbar(wx.ToolBar):
    def __init__(self, parent, *buttons):
        """
        
        @param buttons: tuple or list of ((Bitmap, shortName, longName, isToggle), Handler)
        """
        
        wx.ToolBar.__init__(self, parent)
        for button in buttons:
            buttonargs, handler = button
            tool = self.AddSimpleTool(-1, *buttonargs)
            self.Bind(wx.EVT_MENU, handler, tool)
        
class VampyImageConfigPanel(wx.Panel):
    '''Sets parameters to configure the image properties'''
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        Nsides = len(SIDES)
        box = wx.StaticBox(self, -1, 'Image Config')
        boxsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        cropbox = wx.StaticBox(self, -1, 'Croppings')
        cropboxsizer = wx.StaticBoxSizer(cropbox, wx.VERTICAL)
        cropsizer = wx.FlexGridSizer(cols=2)
        
        for index,side in enumerate(SIDES):
            title = wx.StaticText(self, -1, side)
            cropping = wx.TextCtrl(self, -1, '0', 
                                    style = wx.TE_PROCESS_ENTER,
                                    name = side+'crop', validator = NumValidator('int', min=0))
            self.Bind(wx.EVT_TEXT_ENTER, parent.OnConfigImage, cropping)
            cropsizer.Add(title, 1, wx.GROW|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
            cropsizer.Add(cropping, 1, wx.ALIGN_LEFT|wx.GROW)
        cropsizer.AddGrowableCol(1)
        cropboxsizer.Add(cropsizer, 1, wx.GROW)
        boxsizer.Add(cropboxsizer, 1, wx.GROW)
        
        sizer = wx.FlexGridSizer(cols=2)
        for value in self.ChoiceParams():
            paramname, longName, choices = value
            label = wx.StaticText(self, -1, paramname)
            chbox = wx.Choice(self, -1, choices=choices, name=paramname)
            sizer.Add(label, 1, wx.GROW|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(chbox, 1, wx.GROW|wx.ALIGN_LEFT)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableCol(1)
        boxsizer.Add(sizer, 0, wx.GROW)
        self.Bind(wx.EVT_CHOICE, parent.OnConfigImage, wx.FindWindowByName('orient'))
        self.Bind(wx.EVT_CHOICE, self.OnModeChoice, wx.FindWindowByName('mode'))
        
        for boolparam in self.BoolParams():
            cb = wx.CheckBox(self, -1, boolparam+"?", style=wx.ALIGN_LEFT, name=boolparam)
            boxsizer.Add(cb, 0, wx.ALIGN_LEFT)

        self.SetSizer(boxsizer)
        self.Fit()
        for child in self.GetChildren():
            child.Enable(False)
    
    def ChoiceParams(self):
        return (
                ('orient', 'Pipette orientation', SIDES),
                ('mode', 'Image mode', ('phc', 'dic')),
                ('polar', 'DiC polarization', ('left', 'right'))
                )
    
    def BoolParams(self):
        return ('fromnames', 'darktip')
    
    def Initialize(self, imgcfg):
        for child in self.GetChildren():
            child.Enable(True)
        for side in SIDES:
            cropctrl = wx.FindWindowByName(side+'crop')
            cropctrl.SetValue(str(imgcfg.get(side, 0)))
        
        for value in self.ChoiceParams():
            paramname, LongName, choices = value
            ctrl = wx.FindWindowByName(paramname)
            ctrl.SetStringSelection(imgcfg.get(paramname, choices[0]))
        self.OnModeChoice(wx.EVT_CHOICE)
        
        for boolparam in self.BoolParams():
            cb = wx.FindWindowByName(boolparam)
            cb.SetValue(int(imgcfg.get(boolparam, 0)))
    
    def GetCrop(self):
        crops = {}
        for side in SIDES:
            ctrl = wx.FindWindowByName(side+'crop')
            crop = ctrl.GetValue()
            crops[side] = int(crop)
        return crops
    
    def GetOrient(self):
        return wx.FindWindowByName('orient').GetStringSelection()
        
    def GetChoices(self):
        params = {}
        for value in self.ChoiceParams():
            paramname, longName, choices = value
            params[paramname] = wx.FindWindowByName(paramname).GetStringSelection() #to convert from unicode
        return params
        
    def GetBools(self):
        params = {}
        for boolparam in self.BoolParams():
            params[boolparam] = wx.FindWindowByName(boolparam).GetValue()
        return params
    
    def GetParams(self):
        params = self.GetChoices()
        params.update(self.GetBools())
        params.update(self.GetCrop())
        return params
    
    def OnModeChoice(self, evt):
        modectrl = wx.FindWindowByName('mode')
        polarctrl = wx.FindWindowByName('polar')
        if modectrl.GetStringSelection() == 'dic':
            polarctrl.Enable(True)
        else:
            polarctrl.Enable(False)

class VampyAnalysisPanel(wx.Panel):
    """Shows other parameters needed for starting processing of images."""
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        box = wx.StaticBox(self, -1, 'Analysis Options')
        vsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        paramsizer = wx.FlexGridSizer(2,2)
        self.numparams = ('sigma','mismatch')
        self.boolparams = ('subpix','extra')
        
        for param in self.numparams:
            label = wx.StaticText(self, -1, param)
            val = wx.TextCtrl(self, -1, '0', name = param, validator = NumValidator('float', min = 0))
            paramsizer.AddMany([(label,0,0), (val,0,0)])
        
        for param in self.boolparams:
            cb = wx.CheckBox(self, -1, param+"?", style=wx.ALIGN_LEFT, name=param)
            paramsizer.Add(cb,0,0)
        
        vsizer.Add(paramsizer)
        
        btn = wx.Button(self, -1, 'Analyse')
        self.Bind(wx.EVT_BUTTON, parent.OnAnalyse, btn)
        vsizer.Add(btn)
        
        self.SetSizer(vsizer)
        self.Fit()
        self.SetState(False)
        
    def Initialize(self):
        self.SetState(True)
        for param in self.numparams:
            ctrl = wx.FindWindowByName(param)
            ctrl.SetValue('3')
            ctrl.Enable(False)
        ### temporarily disabled, since not well implemented yet
        for cb in self.boolparams:
            ctrl = wx.FindWindowByName(cb)
            ctrl.Enable(False)
        
    def SetState(self, state):
        for child in self.GetChildren():
            child.Enable(state)
    
    def GetParams(self):
        params = {}
        for param in self.numparams:
            ctrl = wx.FindWindowByName(param)
            params[param] = float(ctrl.GetValue())
        for param in self.boolparams:
            params[param] = wx.FindWindowByName(param).GetValue()  
        return params

class VampyImagePanel(wx.Panel):
    '''Shows image and sliders affecting image'''
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id, style = wx.BORDER_SUNKEN)
        
        self.Imgs = None
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = Figure(facecolor = rgba_wx2mplt(self.GetBackgroundColour()))
        
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.canvas.mpl_connect('motion_notify_event', parent.statusbar.SetPosition)
        vsizer.Add(self.canvas, 1, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.GROW)
        
        navtoolbar = NavigationToolbar2WxAgg(self.canvas)
        navtoolbar.Realize()
        vsizer.Add(navtoolbar, 0, wx.ALIGN_LEFT|wx.GROW)
        
        slidersizer = wx.FlexGridSizer(cols=2)
        self.ImgNoTxt = wx.TextCtrl(self, -1, "0", size=(50,20),
                                style = wx.TE_READONLY | wx.TE_CENTER)
        slidersizer.Add(self.ImgNoTxt, 0)
        self.ImgNoSlider = wx.Slider(self, -1, 1, 0, 1)
        self.Bind(wx.EVT_SCROLL, self.OnSlide, self.ImgNoSlider)        
        slidersizer.Add(self.ImgNoSlider, 1, wx.GROW)
        
        self.paramsliders = []
        
        regionlabel = wx.StaticText(self, -1, 'Aspirated\nVesicle')
        slidersizer.Add(regionlabel, 0, wx.ALIGN_RIGHT)
        self.regionslider = DoubleSlider(self, -1, (0,1), 0, 1, gap=2, name='aspves')
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.regionslider)
        self.paramsliders.append(self.regionslider)
        slidersizer.Add(self.regionslider, 1, wx.GROW|wx.ALIGN_LEFT)
        
        tiplabel = wx.StaticText(self, -1, 'Pipette Tip')
        slidersizer.Add(tiplabel, 0, wx.ALIGN_RIGHT)
        self.tipslider = DoubleSlider(self, -1, (0,1), 0, 1, gap=2, name='tip')
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.tipslider)
        self.paramsliders.append(self.tipslider)
        slidersizer.Add(self.tipslider, 1, wx.GROW|wx.ALIGN_LEFT)
        
        slidersizer.AddGrowableCol(1,1)
        vsizer.Add(slidersizer, 0, wx.GROW)
        
        hsizer = wx.BoxSizer()
        axslidersizer = wx.FlexGridSizer(rows=2)
        
        name = 'axis'
        label = wx.StaticText(self, -1, name)
        axslidersizer.Add(label)
        self.axisslider = DoubleSlider(self, -1, (0,1), 0, 1, style=wx.SL_VERTICAL, name=name)
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.axisslider)
        
        name = 'pipette'
        label = wx.StaticText(self, -1, name)
        self.pipetteslider = DoubleSlider(self, -1, (0,1), 0, 1, style=wx.SL_VERTICAL, name=name)
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.pipetteslider)
        axslidersizer.Add(label)
        
        axslidersizer.Add(self.axisslider, 1, wx.GROW|wx.ALIGN_TOP)
        axslidersizer.Add(self.pipetteslider, 1, wx.GROW|wx.ALIGN_TOP)
        
        self.paramsliders.append(self.axisslider)
        self.paramsliders.append(self.pipetteslider)
            
        axslidersizer.AddGrowableRow(1,1)
        hsizer.Add(axslidersizer, 0, wx.GROW)
        hsizer.Add(vsizer, 1, wx.GROW)
        for child in self.GetChildren():
            child.Enable(False)
        self.SetSizer(hsizer)
        self.Fit()
        
    def GetImgNo(self):
        return self.ImgNoSlider.GetValue()
        
    def SetImgNo(self):
        self.ImgNoTxt.SetValue(str(self.GetImgNo()))
#    
    def SetRanges(self):
        imgno, ysize, xsize = self.Imgs.shape
        self.regionslider.SetRange(0,xsize-1)
        self.tipslider.SetRange(0,xsize-1)
        self.axisslider.SetRange(0, ysize-1)
        self.pipetteslider.SetRange(0, ysize/2)
    
    def Initialize(self):
        '''Draw the first image and initialise sliders'''
        for child in self.GetChildren():
            child.Enable(True)
        self.ImgNoSlider.SetRange(1, len(self.Imgs))
        self.ImgNoSlider.SetValue(1)
        self.SetImgNo()
        ImgsNo, ysize, xsize = self.Imgs.shape

        self.regionslider.SetRange(0, xsize-1)
        self.regionslider.SetValue((1, xsize-2))
        
        self.tipslider.SetRange(0, xsize-1)
        self.tipslider.SetValue((xsize/2, xsize/2+1))
        
        self.axisslider.SetRange(0, ysize-1)
        self.axisslider.SetValue((ysize/2, ysize/2))
        self.pipetteslider.SetRange(0, ysize/2)
        self.pipetteslider.SetValue((ysize/4, ysize/4))
        self.Draw()
    
    def GetParams(self):
        params = self.GetSlidersPos()
        params['images'] = self.Imgs
        return params
    
    def GetSlidersPos(self):
        params = {}
        for slider in self.paramsliders:
            key = str(slider.GetName())
            params[key] = slider.GetValue()
        return params
    
    def SetSlidersPos(self, imgcfg):
#===============================================================================
#        Here the actual names of parameters are referenced by hardcoding
#===============================================================================
        imgno, ysize, xsize = self.Imgs.shape
        
        strvalue = imgcfg.get('aspves', '')
        value, mesg = utils.split_to_int(strvalue, (0, xsize-1))
        if mesg:
            self.GetParent().OnError(mesg)
        self.regionslider.SetValue(value)
        
        strvalue = imgcfg.get('tip', '')
        value, mesg = utils.split_to_int(strvalue, (xsize/2, xsize/2+1))
        if mesg:
            self.GetParent().OnError(mesg)
        self.tipslider.SetValue(value)
        
        for key in ('axis','pipette'):
            strvalue = imgcfg.get(key, '')
            value, mesg = utils.split_to_int(strvalue, (0, ysize/4))
            if mesg:
                self.GetParent().OnError(mesg)
            wx.FindWindowByName(key).SetValue(value)
        
        self.Draw()
            
    def OnSlide(self, evt):
        self.SetImgNo()
        self.Draw()

    def Draw(self):
        '''refresh image pane'''
        ImgNo = self.GetImgNo()
        self.axes.clear()
        for value in self.regionslider.GetValue():
            self.axes.axvline(value)
        ydots = self.axisslider.GetValue()
        xdots = [0, self.regionslider.GetLow()]
        self.axes.plot(xdots, ydots, 'y--')
        
        tiplimleft, tiplimright = self.tipslider.GetValue()
        self.axes.axvspan(tiplimleft, tiplimright, fc='g', alpha=0.5)
        
        piprad, pipthick = self.pipetteslider.GetValue()
        
        line1 = [ydots[0]+piprad+pipthick, ydots[1]+piprad+pipthick]
        line2 = [ydots[0]+piprad, ydots[1]+piprad]
        line3 = [ydots[0]-piprad, ydots[1]-piprad]
        line4 = [ydots[0]-piprad-pipthick, ydots[1]-piprad-pipthick]
        
        self.axes.plot(xdots, line1, 'y-')
        self.axes.plot(xdots, line2, 'y-')
        self.axes.plot(xdots, line3, 'y-')
        self.axes.plot(xdots, line4, 'y-')
        
        self.axes.imshow(self.Imgs[ImgNo-1], aspect='equal', cmap=mplt.cm.gray)
        self.canvas.draw()
    
class VampyFrame(wx.Frame):
    '''wxPython VAMP frontend'''
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        
        self.folder = None
        self.OpenedImgs = None
        self.maintitle = title
        
        self.menubar = VampyMenuBar(self)
        self.SetMenuBar(self.menubar)
        
        self.toolbar = self.MakeToolbar()
        self.SetToolBar(self.toolbar)        
        self.toolbar.Realize()
        
        self.statusbar = VampyStatusBar(self)
        self.SetStatusBar(self.statusbar)
        
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.imgpanel = VampyImagePanel(self, -1)
        hsizer.Add(self.imgpanel, 1, wx.GROW)
        
        paramssizer = wx.BoxSizer(wx.VERTICAL)

        self.imgconfpanel = VampyImageConfigPanel(self)
        paramssizer.Add(self.imgconfpanel, 0, wx.ALL|wx.GROW)
        
        self.analysispanel = VampyAnalysisPanel(self, -1)
        paramssizer.Add(self.analysispanel, 0, wx.ALL|wx.GROW)
        
        
        emptypanel = wx.Panel(self, -1)
        paramssizer.Add(emptypanel, 1, wx.ALL|wx.GROW)
        hsizer.Add(paramssizer, 0, wx.GROW)
        self.SetSizer(hsizer)
        self.Fit()
        self.Centre()
        self.SetIcons(GetResIconBundle(FRAME_ICON))

    def MakeToolbar(self):
        buttons = self.ToolbarData()
        return VampyToolbar(self, *buttons)
    
    def ToolbarData(self):
        return ((
                (GetResBitmap(SAVETXT_ICON), 'Save Image Info', 'Save image info', False),
                 self.OnSave),
                )
         
    def OnOpenFolder(self, evt):
        """
        Open directory of files, load them and initialise GUI
        @param evt: incoming event from caller
        """
        if not self.folder:
            self.folder = OWNPATH
        dirDlg = wx.DirDialog(self, message="Choose a directory",
                                defaultPath = self.folder)
        if dirDlg.ShowModal() != wx.ID_OK:
            dirDlg.Destroy()
            return
        self.folder = dirDlg.GetPath()
        dirDlg.Destroy()
        
        os.chdir(self.folder)
        
        extensions = ['png','tif']
        extDlg = wx.SingleChoiceDialog(self, 'Choose image file type', 'File type', extensions)
        if extDlg.ShowModal() != wx.ID_OK:
            extDlg.Destroy()
            return
        fileext = extDlg.GetStringSelection()
        extDlg.Destroy()
        
        self.imgfilenames = glob.glob(self.folder+'/*.'+fileext)
        if len(self.imgfilenames) == 0:
            msg = "No such files in the selected folder!"
            self.OnError(msg)
            self.OnOpenFolder(evt)
        else:
            self.imgfilenames.sort()
            self.OpenedImgs, imgcfg, msg = self.LoadImages()
            if msg:
                self.OnError(msg)
                self.OnOpenFolder(evt)
            else:
                self.imgconfpanel.Initialize(imgcfg)
                self.analysispanel.Initialize()
                self.imgpanel.Imgs = self.OpenedImgs
                self.imgpanel.Initialize()
                self.OnConfigImage(evt)
                self.imgpanel.SetSlidersPos(imgcfg)
                title = '%s - %s'%(self.maintitle, os.path.split(self.folder)[1])
                self.SetTitle(title)
    
    def LoadImages(self):
        if self.OpenedImgs != None:
#            del(self.OpenedImgs)
            self.OpenedImgs = None
        imgcfgfilename = os.path.join(self.folder, CFG_FILENAME)
        imgcfg = vload.read_conf_file(imgcfgfilename)
        test, mesg = vload.read_grey_image(self.imgfilenames[0])
        if mesg:
            return None, imgcfg, mesg
        try:
            images = empty((len(self.imgfilenames), test.shape[0], test.shape[1]), test.dtype)
        except MemoryError:
            mesg = 'Memory Leak. Restart the application.'
            self.OnError(mesg)
#            images = None
            return
        progressdlg = wx.ProgressDialog('Loading images','Loading images',len(self.imgfilenames),
                                        style = wx.PD_AUTO_HIDE|wx.PD_CAN_ABORT|wx.PD_REMAINING_TIME)
        keepLoading = True
        for index, filename in enumerate(self.imgfilenames):
            ### open the image file
            keepLoading = progressdlg.Update(index+1)
            if not keepLoading:
                mesg = 'Progress cancelled! Not all images have been loaded.'
                break
            img, mesg = vload.read_grey_image(filename)
            if mesg:
                return None, imgcfg, mesg
            ### test that the image has the same shape as others
            if img.shape != test.shape:
                mesg = 'Error: Images have different dimensions!'
                return None, imgcfg, mesg
            images[index, :] = img
        progressdlg.Destroy()
        return images, imgcfg, mesg
        
    def OnError(self, msg):
        """
        Display an error dialog
        @param msg: error message to display (type = string)
        """
        errDlg = wx.MessageDialog(self, msg, "Error!", wx.ICON_ERROR)
        errDlg.ShowModal()
        errDlg.Destroy()
        
    def OnConfigImage(self, evt):
        """
        respond to preprocessing parameters
        @param evt: incoming event from caller
        """
        orient = self.imgconfpanel.GetOrient()
        if self.imgconfpanel.Validate():
            crop = self.imgconfpanel.GetCrop()
        else:
            return
        self.imgpanel.Imgs = vload.preproc_images(self.OpenedImgs, orient, crop)
        self.imgpanel.SetRanges()
        self.imgpanel.Draw()
        
    def OnAnalyse(self, evt):
        """
        starts actual image analysis 
        @param evt: incoming event from caller
        """
        if self.analysispanel.Validate():
            params = self.analysispanel.GetParams()
        else:
            return
        params.update(self.imgpanel.GetParams())
        params.update(self.imgconfpanel.GetParams())
        
        ### testing if 'cancel' was pressed somewhere or 
        ### errors when converting from string to float while loading (None is returned)
        try:
            pressures, pressacc, scale, aver = self.GetExtraUserData(params['fromnames'], len(params['images']))
        except(TypeError): # catching type error
            return
        out, extra_out = vfeat.locate(params)
        geometry, mesg = vanalys.get_geometry(out)
        if mesg:
            self.OnError(mesg)
            return
        avergeom = vanalys.averageImages(aver, **geometry)
        geometryframe = VampyGeometryFrame(self, -1, avergeom)
        geometryframe.Show()
        
        tensiondata = vanalys.tension_evans(pressures, pressacc, scale, avergeom)
        tensionframe = VampyTensionsFrame(self, -1, tensiondata)
        tensionframe.Show()
        evt.Skip()
        
    def GetExtraUserData(self, pressfromfilenames, imgsNo):
        if not pressfromfilenames:
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
        if pressfromfilenames:
            pressures, aver, mesg = vload.read_pressures_filenames(self.imgfilenames, stage)
        else:
            pressures, mesg = vload.read_pressures_file(pressfilename, stage)
            if imgsNo % len(pressures) != 0:
                self.OnError('Number of images is not multiple of number of pressures!')
                return
            else:
                aver = imgsNo/len(pressures)#number of images to average within
        if mesg:
            self.OnError(mesg)
            return None
        return pressures, pressacc, scale, aver
    
    def OnExit(self, evt):
        self.Close()
        
    def OnSave(self, evt):
        intparams = self.imgconfpanel.GetCrop()
        stringparams = self.imgconfpanel.GetChoices()
        intparams.update(self.imgconfpanel.GetBools())
        intparams.update(self.imgpanel.GetSlidersPos())
        lines = []
        for key in stringparams.keys():
            lines.append('%s\t%s\n'%(key, stringparams[key]))
        for key in intparams.keys():
            line = '%s'%key
            if type(intparams[key]) in (int, bool):
                line += '\t%i'%intparams[key]
            else:
                line += len(intparams[key])*'\t%i'%intparams[key]
            line += '\n'
            lines.append(line)
            
        try:
            conffile = open(CFG_FILENAME, 'w')
        except IOError:
            wx.MessageBox('An error occurred while saving image info', 'Error')
            evt.Skip()
            return
        conffile.writelines(lines)
        conffile.close()
        wx.MessageBox('Image info saved', 'Info')
        evt.Skip()
        
    def OnReloadMath(self, evt):
        """
        Explicitly reloads all imported modules from VAMPy projects.
        @param evt: incoming event from caller
        """
        reload(vload)
        reload(vanalys)
        reload(vfeat)
        reload(vout)
        reload(vfit)
        reload(utils)
        print '-'*20
        
    def OnReloadGUI(self, evt):
        """
        Reloads GUI
        FIXME: introduces a memory leak, old version is not discarded completely
        """
#        dlg = wx.MessageDialog(self, 'Are you sure to reload GUI?', 'Please confirm',
#                               style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_EXCLAMATION)
#        if dlg.ShowModal() == wx.ID_YES:
#            print '='*20
#            del(self.OpenedImgs)
#            wx.GetApp().Reload(self.folder)
        
        dlg = wx.MessageDialog(self, 'Not implemented (yet).\nClose the application, so that you can start it again?', 
                       'Confirmation', style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            self.OnExit(wx.EVT_WINDOW_DESTROY)
    
    def OnDebugImage(self, evt):
        """
        Process only the current image
        TODO:process set of images?
        and display more additional information on it
        """
        imgNo = self.imgpanel.GetImgNo()
        if self.analysispanel.Validate():
            params = self.analysispanel.GetParams()
        else:
            return
        params.update(self.imgpanel.GetParams())
        img = params['images'][imgNo-1]
        params['images'] = img.reshape(1, img.shape[0], img.shape[1])
        params['extra'] = True
        out, extra_out = vfeat.locate(params)
        extra_out = extra_out[0]
        ImageDebugFrame = VampyImageDebugFrame(self, -1, img, out, extra_out)
        ImageDebugFrame.Show()
        
    def OnAbout(self, evt):
        description = """Vesicle Aspiration with MicroPipettes made with Python
Short instructions:
Open folder with images, rotate so that pipette sticks from the left, crop if needed, set parameters and click start!"""
        info = wx.AboutDialogInfo()
        info.SetName('VAMPy')
        info.SetDescription(description)
        info.AddDeveloper('Pavlo Shchelokovskyy')
        wx.AboutBox(info)
        
    def OnHelp(self, evt):
        """
        TODO: write a (simple) online help
        @param evt:
        """
        self.OnAbout(evt)
    
class VampyOtherUserDataDialog(wx.Dialog):
    """
    Dialog to collect additional data from user
    """
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, 'Additional Parameters:')
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.stagerb=wx.RadioBox(self, -1, 'Stage No.', choices = ['1','2'], majorDimension=2)
        vsizer.Add(self.stagerb, 1, wx.GROW)
        
        flsz = wx.FlexGridSizer(-1,2)
        label = wx.StaticText(self, -1, 'Scale (um/pixel)')
        flsz.Add(label, 1)
        self.scale = wx.TextCtrl(self, -1, DEFAULT_SCALE, validator = NumValidator('float', min=0))
        flsz.Add(self.scale,1)
        
        label = wx.StaticText(self, -1, 'Pressure Accuracy (Pa)')
        flsz.Add(label)
        self.pressacc = wx.TextCtrl(self, -1, DEFAULT_PRESSACC, validator = NumValidator('float', min=0))
        flsz.Add(self.pressacc)
        
        vsizer.Add(flsz)
        btnbox = wx.StdDialogButtonSizer()
        okBtn = wx.Button(self, wx.ID_OK, 'OK')
        okBtn.SetDefault()
        closeBtn = wx.Button(self, wx.ID_CANCEL, 'Cancel')
        btnbox.AddButton(okBtn)
        btnbox.AddButton(closeBtn)
        btnbox.Realize()
        
        vsizer.Add(btnbox)
        
        self.SetSizer(vsizer)
        self.Layout()
        self.Fit()
    
    def GetData(self):
        scale = float(self.scale.GetValue())
        pressacc = float(self.pressacc.GetValue())
        stage = self.stagerb.GetSelection()        
        return stage, scale, pressacc

class VampyTensionsFrame(wx.Frame):
    def __init__(self, parent, id, tensiondata):
        wx.Frame.__init__(self, parent, id, title = 'Dilation vs Tension')
        
        panel = wx.Panel(self, -1)
        pansizer = wx.BoxSizer(wx.VERTICAL)
        
        self.statusbar = VampyStatusBar(self)
        self.SetStatusBar(self.statusbar)
        
        self.toolbar = self.MakeToolbar()
        self.SetToolBar(self.toolbar)
        self.toolbar.Realize()
        
        self.figure = Figure(facecolor = rgba_wx2mplt(panel.GetBackgroundColour()))
        self.canvas = FigureCanvas(panel, -1, self.figure)
        self.canvas.mpl_connect('motion_notify_event', self.statusbar.SetPosition)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_aspect('auto')
        pansizer.Add(self.canvas, 1, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.GROW)
        
        navtoolbar = NavigationToolbar2WxAgg(self.canvas)
        navtoolbar.Realize()
        pansizer.Add(navtoolbar, 0, wx.GROW)
        
        self.data = tensiondata
        self.tau, self.tau_err = tensiondata['tension']
        self.alpha, self.alpha_err = tensiondata['dilation']
        
        if self.tau[0] == 0:
            init = 1
        else:
            init = 0
        self.slider = DoubleSlider(panel, -1, (init, len(self.tau)), 0, len(self.tau), gap=2)
        self.Bind(wx.EVT_SLIDER, self.OnSlide, self.slider)
        pansizer.Add(self.slider, 0, wx.GROW)
        panel.SetSizer(pansizer)
        
        panel.Fit()
        self.SetIcons(GetResIconBundle(FRAME_ICON))
        title = '%s - %s'%(self.GetTitle(), os.path.split(parent.folder)[1])
        self.SetTitle(title)
        self.Fit()
        self.Draw()

    def MakeToolbar(self):
        buttons = self.ToolbarData()
        return VampyToolbar(self, *buttons)

    def ToolbarData(self):
        return ((
                (GetResBitmap(SAVETXT_ICON), 'Save Data File', 'Save Data File', False),
                 self.OnSave),
                )
    
    def OnSlide(self, evt):
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
        writer = vout.DataWriter(self.data)
        mesg = writer.write_file(datname)
        if mesg:
            self.GetParent().OnError(mesg)
        
    def Draw(self):
        low, high = self.slider.GetValue()
        self.axes.clear()

        x = self.tau[low:high+1]
        y = self.alpha[low:high+1]
        sx = self.tau_err[low:high+1]
        sy = self.alpha_err[low:high+1]
        self.axes.semilogx(self.tau[low:high+1], self.alpha[low:high+1], 'ro', label = 'Measured')
        
#        x_b, y_b, sx_b, sy_b = self.tau[1:slider], self.alpha[1:slider], self.tau_err[1:slider], self.alpha_err[1:slider]
#        x_e, y_e, sx_e, sy_e = self.tau[slider:], self.alpha[slider:], self.tau_err[slider:], self.alpha_err[slider:]
#        slope_b, interc_b, bend, bend_sd = vanalys.bending_evans(x_b, y_b, sx_b, sy_b)
#        slope_e, interc_e, elas, elas_sd = vanalys.elastic_evans(x_e, y_e, sx_e, sy_e)
#
#        self.axes.plot(x_b, vanalys.dilation_bend_evans(x_b, slope_b, interc_b), label = 'Fit low-P')
#        self.axes.plot(x_e, vanalys.dilation_elas_evans(x_e, slope_e, interc_e), label = 'Fit high-P')
        
#        self.axes.axvline(self.tau[slider])

#        fit, fit_sd, mesg, success = vfit.nls_Fournier(x, y)
        fit = vfit.odrlinlog(x, y, sx, sy)
        bend, intercept = fit.beta
        
        bend_sd, intercept_sd = fit.sd_beta
        success = 1
        if success != 1:
            title = 'Fit Error: %s'%mesg
        else:
#            a0_T, bend, elas = fit
#            bend_sd, a0_T_sd, elas_sd = fit_sd
#            title = 'kappa = %f +- %f kT; K = %f +- %f mN/m'%(bend, bend_sd, elas/1000., elas_sd/1000.)
#            title = 'kappa = %f kT; K = %f mN/m'%(bend, elas/1000.)
#            f = vfit.alpha_Fournier()
#            self.axes.plot(x, f(fit, x), label = 'Fournier fit')
            title = 'kappa = %f +- %f kT'%(1/(8*pi*bend), bend_sd/(8*pi*bend))
            f = vanalys.dilation_bend_evans
            self.axes.plot(x, f(x, bend, intercept), label = 'Evans fit')
        self.axes.set_title(title)
        self.axes.legend(loc=4)
        labelfont = {'fontsize':'large'}
        self.axes.set_xlabel(r'$\tau$', fontdict = labelfont)
        self.axes.set_ylabel(r'$\alpha$')
        self.canvas.draw()

class VampyGeometryFrame(wx.Frame):
    def __init__(self, parent, id, argsdict):
        wx.Frame.__init__(self, parent, id, size = (1024,768), title = 'Vesicle Geometry')
        
        self.data = argsdict
        
        self.statusbar = VampyStatusBar(self)
        self.SetStatusBar(self.statusbar)
        
        self.toolbar = self.MakeToolbar()
        self.SetToolBar(self.toolbar)
        self.toolbar.Realize()
        
        panel = wx.Panel(self, -1)
        pansizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = Figure(facecolor = rgba_wx2mplt(panel.GetBackgroundColour()))
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
        n,m = utils.grid_size(len(toplot))
        for index, item in enumerate(toplot):
            y, y_err = self.data[item]
            plottitle = titles[item]
            plot = self.figure.add_subplot(n,m,index+1, title = plottitle)
            plot.errorbar(x, y, y_err, fmt='bo-', label=plottitle)
            self.plots[item] = plot
#       
        navtoolbar = NavigationToolbar2WxAgg(self.canvas)
        navtoolbar.Realize()
        pansizer.Add(navtoolbar, 0, wx.GROW)
        
        self.SetIcons(GetResIconBundle(FRAME_ICON))
        panel.SetSizer(pansizer)
        panel.Fit()
        title = '%s - %s'%(self.GetTitle(), os.path.split(parent.folder)[1])
        self.SetTitle(title)
        self.canvas.draw()
    
    def MakeToolbar(self):
        buttons = self.ToolbarData()
        return VampyToolbar(self, *buttons)
    
    def ToolbarData(self):
        return ((
                (GetResBitmap(SAVETXT_ICON), 'Save Data File', 'Save Dat File', False),
                 self.OnSave),
                )
        
    def OnSave(self, evt):
        savedlg = wx.FileDialog(self, 'Save data', self.GetParent().folder,
                            'images.dat', wildcard = DATWILDCARD, 
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if savedlg.ShowModal() == wx.ID_CANCEL:
            return
        datname = savedlg.GetPath()
        savedlg.Destroy()
        writer = vout.DataWriter(self.data)
        mesg = writer.write_file(datname)
        if mesg:
            self.GetParent().OnError(mesg)
            
class VampyImageDebugFrame(wx.Frame):
    def __init__(self, parent, id, img, out, extra_out):
        wx.Frame.__init__(self, parent, id, size=(800,600), title = 'Single Image Debug')
        
        self.statusbar = VampyStatusBar(self)
        self.SetStatusBar(self.statusbar)
        
        panel = wx.Panel(self, -1)
        pansizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = Figure(facecolor = rgba_wx2mplt(panel.GetBackgroundColour()))
        self.canvas = FigureCanvas(panel, -1, self.figure)
        self.canvas.mpl_connect('motion_notify_event', self.statusbar.SetPosition)
        pansizer.Add(self.canvas, 1, wx.GROW)
        
        navtoolbar = NavigationToolbar2WxAgg(self.canvas)
        navtoolbar.Realize()
        pansizer.Add(navtoolbar, 0, wx.GROW)
        
        profile = extra_out['profile']
        self.profileplot = self.figure.add_subplot(221, title = 'Axis brightness profile')
        self.profileplot.plot(profile)
        self.profileplot.axvline(extra_out['pip'], color = 'blue')
        self.profileplot.axvline(extra_out['asp'], color = 'yellow')
        self.profileplot.axvline(extra_out['ves'], color = 'green')
        
        self.imgplot = self.figure.add_subplot(222, title = 'Image')
        refs = extra_out['refs']
        for ref in refs:
            self.imgplot.plot([ref[0][1]], [ref[0][0]], 'yo') # due to format of refs
        self.imgplot.imshow(img, aspect = 'equal', extent = None, cmap = mplt.cm.gray)

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
        self.SetIcons(GetResIconBundle(FRAME_ICON))
        panel.SetSizer(pansizer)
        panel.Fit()
        title = '%s - %s - Image %i'%(self.GetTitle(), os.path.split(parent.folder)[1], parent.imgpanel.GetImgNo())
        self.SetTitle(title)
        self.canvas.draw()
    
if __name__ == "__main__":
    print __doc__