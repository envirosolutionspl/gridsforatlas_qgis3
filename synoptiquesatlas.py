"""
/***************************************************************************
 GridsForAtlas
                                 A QGIS plugin
 Creation de synoptiques grille ou dynamique pour utiliser dans un atlas
                              -------------------
        begin                : 2012-02-22
        copyright            : (C) 2012 by Experts SIG / Biotope
        email                : dev-qgis@biotope.fr

 Version 0.4.0 (Adapted to QGIS 2.X API by Bertrand Chaussat - 12/2015)
 
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from synoptiquesatlasdialog import SynoptiquesAtlasDialog
from ui_help_window import Ui_help_window
from ui_about_window import Ui_About_window

class SynoptiquesAtlas:

  def __init__(self, iface):
    # Save reference to the QGIS interface
    self.iface = iface
    # a reference to our map canvas
    self.canvas = self.iface.mapCanvas()
    # Setup directory
    self.user_plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins"
    self.syn_atlas_plugin_dir = self.user_plugin_dir + "/synoptiquesatlas"
    # Translation to English    
    locale = QSettings().value("locale/userLocale")
    self.myLocale = locale[0:2]
    if QFileInfo(self.syn_atlas_plugin_dir).exists():
      localePath = self.syn_atlas_plugin_dir + "/i18n/synoptiquesatlas_" + self.myLocale + ".qm"
    if QFileInfo(localePath).exists():
      self.translator = QTranslator()
      self.translator.load(localePath)
      if qVersion() > '4.3.3':
            QCoreApplication.installTranslator(self.translator)  
    # create and show the dialog
    self.dlg = SynoptiquesAtlasDialog()

  def initGui(self):
    # Create action that will start plugin configuration
    self.action = QAction(QIcon(":/plugins/synoptiquesatlas/icon.png"), \
      QCoreApplication.translate("synoptiquesatlas", "&Grids for Atlas"), self.iface.mainWindow())
    # Create action for about dialog
    self.action_about = QAction("A&bout...", self.iface.mainWindow())
    # Create action for help dialog
    self.action_help = QAction(QIcon(":/plugins/synoptiquesatlas/about.png"), QCoreApplication.translate("synoptiquesatlas", "&Help..."), self.iface.mainWindow())
    # connect the action to the run method
    QObject.connect(self.action, SIGNAL("triggered()"), self.run)
    # connect about action to about dialog
    QObject.connect(self.action_about, SIGNAL("triggered()"), self.showAbout)    
    # connect help action to help dialog
    QObject.connect(self.action_help, SIGNAL("triggered()"), self.showHelp)
    # connect signals
    QObject.connect(self.dlg.ui.btnCreerSyno, SIGNAL("clicked()"), self.creerSyno)
    # composer changed, update maps
    QObject.connect(self.dlg.ui.cbbComp, SIGNAL('currentIndexChanged(int)'), self.updateMaps)    
    # refresh inLayer box
    QObject.connect(self.dlg.ui.cbbInLayer, SIGNAL('currentIndexChanged(int)'), self.onLayerChange)
    # browse button
    QObject.connect(self.dlg.ui.btnBrowse, SIGNAL('clicked()'), self.updateOutputDir)
    # refresh template button
    QObject.connect(self.dlg.ui.btnUpdate, SIGNAL('clicked()'), self.updateComposers)
    # show composer
    QObject.connect(self.dlg.ui.btnShow, SIGNAL('clicked()'), self.showComposer)
    # show about dialog
    QObject.connect(self.dlg.ui.aboutButton, SIGNAL('clicked()'), self.showAbout)
    # show help dialog
    QObject.connect(self.dlg.ui.helpButton, SIGNAL('clicked()'), self.showHelp)
    # Add toolbar button and menu item
    self.iface.addToolBarIcon(self.action)
    self.iface.addPluginToMenu("&Grids for Atlas", self.action)
    # Add about menu entry
    self.iface.addPluginToMenu("&Grids for Atlas", self.action_about)
    # add help menu entry
    self.iface.addPluginToMenu("&Grids for Atlas", self.action_help)

  def updateBoxes(self):
    self.updateLayers()
    self.updateComposers()
    self.updateMaps()

  def updateLayers(self):
    self.dlg.ui.cbbInLayer.clear()
    for layer in self.iface.mapCanvas().layers():
      self.dlg.ui.cbbInLayer.addItem(layer.name(), layer)

  # (c) Carson Farmer / fTools
  def getVectorLayerByName(self,myName):
    layermap = QgsMapLayerRegistry.instance().mapLayers()
    for name, layer in layermap.iteritems():
      if layer.type() == QgsMapLayer.VectorLayer and layer.name() == myName:
        if layer.isValid():
          return layer
        else:
          return None 

  def onLayerChange(self):
    self.cLayer = self.getVectorLayerByName(self.dlg.ui.cbbInLayer.currentText())

  def updateComposers(self):
    self.dlg.ui.cbbComp.clear()
    compos = self.iface.activeComposers()
    for cv in compos:
      self.dlg.ui.cbbComp.addItem(cv.composerWindow().windowTitle(), cv)
    self.composer = self.dlg.ui.cbbComp.itemData(self.dlg.ui.cbbComp.currentIndex())
 
  def updateMaps(self):
    self.dlg.ui.cbbMap.clear()
    if self.dlg.ui.cbbComp.currentIndex() != -1:
      self.composer = self.dlg.ui.cbbComp.itemData(self.dlg.ui.cbbComp.currentIndex())
      for item in self.composer.composition().items():
        if item.type() == QgsComposerItem.ComposerMap:
          self.dlg.ui.cbbMap.addItem(QCoreApplication.translate("synoptiquesatlas", "Map ") + "%s"% item.id(), item.id)
   
  def showComposer(self):
    self.composer.composerWindow().show()
    self.composer.composerWindow().activate() 

  def updateOutputDir(self):
    self.dlg.ui.lieOutDir.setText(QFileDialog.getExistingDirectory(self.dlg, \
      QCoreApplication.translate("synoptiquesatlas", "Choose output directory"))) 

  def unload(self):
    # Remove the plugin menu item and icon
    self.iface.removePluginMenu("&Grids for Atlas",self.action)
    self.iface.removeToolBarIcon(self.action)
    # Remove about menu entry
    self.iface.removePluginMenu("&Grids for Atlas", self.action_about)
    # Remove help menu entry
    self.iface.removePluginMenu("&Grids for Atlas", self.action_help)

  def creerSyno(self):               
    if os.path.exists(self.dlg.ui.lieOutDir.text()):
      self.gridSynopt = self.dlg.ui.chkGrille.isChecked()
      self.dynSynopt = self.dlg.ui.chkDyn.isChecked()
      if self.gridSynopt or self.dynSynopt:           
        compos = self.iface.activeComposers()
        if compos:         
          cview = compos[self.dlg.ui.cbbComp.currentIndex()]
          cmap = self.dlg.ui.cbbMap.itemData(self.dlg.ui.cbbMap.currentIndex())
          self.mapItem = cview.composition().getComposerMapById(cmap())
          self.ladderHeight = self.mapItem.extent().height()
          self.ladderWidth = self.mapItem.extent().width()        
          if self.cLayer:
            if self.cLayer.type() == 0:
              self.crs = self.cLayer.crs()
              self.URIcrs = "crs=" + self.crs.toWkt()
              self.doBuffer()
              self.extent = self.bcLayer.extent()                                     
              self.orig_ladders_list = []
              self.sLayer = self.addSynoFeatures(self.orig_ladders_list)
              self.synopt_shape_path = self.dlg.ui.lieOutDir.text() + QCoreApplication.translate("synoptiquesatlas","/classic_grid.shp")
              self.createPhysLayerFromList(self.synopt_shape_path, self.orig_ladders_list)
              if self.gridSynopt:  
                self.sLayer = self.loadQgsVectorLayer(self.synopt_shape_path, \
                  QCoreApplication.translate("synoptiquesatlas","classic grid"))
              else:
                self.sLayer = QgsVectorLayer(self.synopt_shape_path, QCoreApplication.translate("synoptiquesatlas","classic grid"), "ogr")                          
                # TODO                
                # Manage symbology
                #if not hasattr(self.sLayer, 'isUsingRendererV2'):
                #  QMessageBox.information(self.iface.mainWindow(),"Info", \
                #  "La symbologie ne peut etre affichee vous utilisez une version ancienne de QGIS")
                #elif layer.isUsingRendererV2():
                # new symbology - subclass of QgsFeatureRendererV2 class
                #  rendererV2 = layer.rendererV2()  
              # Grid layer was created, access to the second stage            
              if self.dynSynopt:
                self.finalSynopt_shape_path = self.dlg.ui.lieOutDir.text() + QCoreApplication.translate("synoptiquesatlas","/dyn_grid.shp")
                self.intersect(self.bcLayer,self.sLayer)    
                self.createIntersectionLayer()
                self.new_ladders_list = []                
                self.sLayer2 = self.centroidsToNewSyno(self.new_ladders_list)                
                self.parseSyno()
                self.final_ladders_list = []
                self.sLayer3 = self.centroidsToNewSyno(self.final_ladders_list)
                self.createPhysLayerFromList(self.finalSynopt_shape_path, self.final_ladders_list)
                self.sLayer3 = self.loadQgsVectorLayer(self.finalSynopt_shape_path, \
                  QCoreApplication.translate("synoptiquesatlas","dynamic grid"))
                   
            else:
              QMessageBox.information(self.iface.mainWindow(),"Info", \
                QCoreApplication.translate("synoptiquesatlas","Coverage layer is not vector type"))
          else:
            QMessageBox.information(self.iface.mainWindow(),"Info", \
              QCoreApplication.translate("synoptiquesatlas","Please select a coverage layer to generate grid"))
        else:
          QMessageBox.information(self.iface.mainWindow(),"Info", \
            QCoreApplication.translate("synoptiquesatlas","Please select a print composer, if none is active you have to create it"))
      else:
        QMessageBox.information(self.iface.mainWindow(),"Info", QCoreApplication.translate("synoptiquesatlas","Choose a grid type"))
    else:
      QMessageBox.information(self.iface.mainWindow(),"Info", QCoreApplication.translate("synoptiquesatlas","Please enter an existant directory name"))

  def doBuffer(self):
    maxDim = max(self.ladderHeight,self.ladderWidth)
    ratio = 1000./2970
    bufferLength = maxDim * ratio                
    self.bcLayer = QgsVectorLayer("Polygon?" + self.URIcrs, "buffer_layer", "memory")
    pr = self.bcLayer.dataProvider()
    pr.addAttributes([QgsField("ID_BUFFER", QVariant.Int)])    
    provider_perimetre = self.cLayer.dataProvider()
    iter = provider_perimetre.getFeatures()
    i = 0    
    for feature in iter:
      fet = QgsFeature()
      fet.setGeometry(feature.geometry().buffer(bufferLength,50))
      fet.setFeatureId(i)
      pr.addFeatures([fet])       
      i = i + 1
    self.bcLayer.updateExtents()    

  def addSynoFeatures(self, ladder_list):
    layer = QgsVectorLayer("Polygon?" + self.URIcrs, "grid_layer", "memory")
    pr = layer.dataProvider()
    pr.addAttributes([QgsField("ID_MAILLE", QVariant.Int)])
    # Initial settings
    provider_perimetre = self.cLayer.dataProvider()    
    ladderHeight = self.ladderHeight
    ladderWidth = self.ladderWidth            
    ladder_id = 0
    yMax = self.extent.yMaximum()            
    yMin = yMax - ladderHeight
    widthSum = 0
    heightSum = 0                                   
    # Build columns           
    while heightSum < self.extent.height():            
      widthSum = 0
      xMin = self.extent.xMinimum()
      xMax = xMin + ladderWidth
      # Build lines               
      while widthSum < self.extent.width():          
        # Create geometry
        ladder = QgsRectangle(xMin, yMin, xMax, yMax)
        request = QgsFeatureRequest()
        request.setFilterRect(ladder)         
        for f in provider_perimetre.getFeatures(request):
          ladder_id = ladder_id + 1
          # Add ladder to layer
          fet = QgsFeature()
          fet.setGeometry(QgsGeometry.fromRect(ladder))
          fet.setAttributes([ladder_id])
          pr.addFeatures([fet])
          ladder_list.append(fet)
        # Settings for next ladder
        xMin = xMin + ladderWidth
        xMax = xMax + ladderWidth
        widthSum = widthSum + ladderWidth
      heightSum = heightSum + ladderHeight
      yMin = yMin - ladderHeight
      yMax = yMax - ladderHeight
    layer.updateExtents()
    return layer

  def createPhysLayerFromList(self, shapePath, fetList):
    # Create shapefile writer
    fields = QgsFields()
    fields.append(QgsField("ID_MAILLE", QVariant.Int))                
    self.writer = QgsVectorFileWriter(shapePath, "CP1250", fields, \
      QGis.WKBPolygon, self.cLayer.crs(), "ESRI Shapefile")
    if self.writer.hasError() != QgsVectorFileWriter.NoError:
      QMessageBox.information(self.iface.mainWindow(),"Info", \
        QCoreApplication.translate("synoptiquesatlas","Error when creating shapefile:\n") + shapePath + QCoreApplication.translate("synoptiquesatlas","\nPlease delete or rename the former grid layers"))           
    # Add features
    for fet in fetList:         
      self.writer.addFeature(fet)
    # Stop writing           
    del self.writer  

  def createGridLayer(self):
    # Create shapefile writer    
    fields = { 0 : QgsField("ID_MAILLE", QVariant.Int)}                
    self.writer = QgsVectorFileWriter(self.finalSynopt_shape_path, "CP1250", fields, \
      QGis.WKBPolygon, self.cLayer.crs(), "ESRI Shapefile")
    if self.writer.hasError() != QgsVectorFileWriter.NoError:
      QMessageBox.information(self.iface.mainWindow(),"Info", \
        QCoreApplication.translate("synoptiquesatlas","Error when creating shapefile:\n") + self.finalSynopt_shape_path + QCoreApplication.translate("synoptiquesatlas","\nPlease delete or rename the former grid layers"))           
    # Add features
    for fet in self.orig_ladders_list:         
      self.writer.addFeature(fet)
    # Stop writing           
    del self.writer

  def intersect(self, perimetre, calepinage):
  # Intersect between coverage and grid
    self.centroid_list = []      
    self.splitted_fet_list = []
    i = 0    
    if perimetre and calepinage:
      provider_perimetre = perimetre.dataProvider()
      provider_calepinage = calepinage.dataProvider()
      # create the select statement
      request = QgsFeatureRequest()
      request.setFilterRect(self.extent)
      #provider_perimetre.select([])
      #provider_calepinage.select([],self.extent)
      # the arguments mean no attributes returned, and do a bbox filter with our buffered
      # rectangle to limit the amount of features
      for feat_perimetre in provider_perimetre.getFeatures():
        # if the feat geom returned from the selection intersects our point then put it in a list
        for feat_calepinage in provider_calepinage.getFeatures(request):
          # if the feat geom returned from the selection intersects our point then put it in a list
          if feat_perimetre.geometry().intersects(feat_calepinage.geometry()):
            a = feat_perimetre.geometry().intersection(feat_calepinage.geometry())
            self.centroid_list.append(a.centroid())
            fet = QgsFeature()
            fet.setGeometry(a)
            fet.setAttributes([i])          
            self.splitted_fet_list.append(fet)
            i = i + 1

  def createIntersectionLayer(self):
    self.interLayer = QgsVectorLayer("Polygon?" + self.URIcrs, "inter_layer", "memory")
    pr = self.interLayer.dataProvider()
    pr.addAttributes([QgsField("ID_INTER", QVariant.Int)])          
    # Add features
    for fet in self.splitted_fet_list:         
      pr.addFeatures([fet])      
    self.interLayer.updateExtents()

  def centroidsToNewSyno(self, ladder_list):
    layer = QgsVectorLayer("Polygon?" + self.URIcrs, "layer", "memory")
    pr = layer.dataProvider()
    pr.addAttributes([QgsField("ID_MAILLE", QVariant.Int)])    
    ladderHeight = self.ladderHeight
    ladderWidth = self.ladderWidth
    ladder_id = 0           
    for centr in self.centroid_list: 
      pt = centr.asPoint()      
      xMin = pt.x() - ladderWidth/2.
      xMax = pt.x() + ladderWidth/2.
      yMin = pt.y() - ladderHeight/2.
      yMax = pt.y() + ladderHeight/2.
      # Create geometry
      ladder = QgsRectangle(xMin, yMin, xMax, yMax)
      # Add ladder to layer
      fet = QgsFeature()
      fet.setGeometry(QgsGeometry.fromRect(ladder))
      fet.setAttributes([ladder_id])
      ladder_list.append(fet)  
      pr.addFeatures([fet])      
      ladder_id = ladder_id + 1
    layer.updateExtents()
    return layer

  def loadQgsVectorLayer(self, shapePath, layerName):
    layerToLoad = QgsVectorLayer(shapePath, layerName, "ogr")
    if not layerToLoad.isValid():               
      QMessageBox.information(self.iface.mainWindow(),"Info", \
        QCoreApplication.translate("synoptiquesatlas","Error while loading layer ") + layerName + " !")  
    else:    
      QgsMapLayerRegistry.instance().addMapLayer(layerToLoad)
      return layerToLoad      

  def parseSyno(self):    
    i = 0    
    while i <= len(self.new_ladders_list) - 1:
      fet = self.splitted_fet_list[i]      
      overlapped = False      
      j = 0      
      while j <= i - 1 and not overlapped:
        fet2 = self.new_ladders_list[j]
        # if geom is entirely overlapped by geom2, pop it from list, pop its centroid
        if fet2.geometry().contains(fet.geometry()):
          overlapped = True
        j = j + 1
      j = i + 1
      while j <= len(self.new_ladders_list) - 2 and not overlapped:
        fet2 = self.new_ladders_list[j]
        # if geom is entirely overlapped by geom2, pop it from list, pop its centroid
        if fet2.geometry().contains(fet.geometry()):
          overlapped = True
        j = j + 1
      if overlapped:
        self.splitted_fet_list.pop(i)
        self.new_ladders_list.pop(i)
        self.centroid_list.pop(i)   
      else:
        i = i + 1

  def showHelp(self):
    """Show help dialog box"""
    # Create a dialog and setup UI
    hdialog = QDialog()
    hdialog.ui = Ui_help_window()
    hdialog.ui.setupUi(hdialog)
    # load help file
    if self.myLocale == 'fr':
      hdialog.ui.webView.setUrl(QUrl(self.syn_atlas_plugin_dir + '/help/syn_atlas.html'))
    else:
      hdialog.ui.webView.setUrl(QUrl(self.syn_atlas_plugin_dir + '/help/syn_atlas_en.html'))
    hdialog.show()
    result = hdialog.exec_()
    del hdialog

  def showAbout(self):
    """Show Synoptiques Atlas about dialog box"""
    adialog = QDialog()
    adialog.ui = Ui_About_window()
    adialog.ui.setupUi(adialog)
    adialog.show()
    result = adialog.exec_()
    del adialog

  # run method that performs all the real work
  def run(self):

    self.updateBoxes()
    # show the dialog
    self.dlg.show()
    result = self.dlg.exec_()
    # See if OK was pressed
    if result == 1:
      # do something useful (delete the line containing pass and
      # substitute with your code
      pass
