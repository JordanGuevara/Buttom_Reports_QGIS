from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes
)
from qgis.PyQt.QtGui import QIcon
from PyQt5.QtCore import QVariant
from PyQt5.QtWidgets import QAction
from qgis.utils import iface

import os

class ExtremosPredio:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.icono_path = os.path.join(os.path.dirname(__file__), "icono_puntos.png")

    def initGui(self):
        icono = QIcon(self.icono_path) if os.path.exists(self.icono_path) else QIcon.fromTheme("document-print")
        self.action = QAction(icono,"Mostrar/Ocultar extremos predio", self.iface.mainWindow())
        self.action.triggered.connect(self.mostrar_ocultar_puntos_extremos)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Extremos Predio", self.action)

    def unload(self):
        self.iface.removePluginMenu("&Extremos Predio", self.action)
        self.iface.removeToolBarIcon(self.action)

    def mostrar_ocultar_puntos_extremos(self):
        nombre_capa = "extremos_predio"
        tolerancia = 10  # metros
        nombre_capa_calles = "Ejes Viales"

        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == nombre_capa:
                QgsProject.instance().removeMapLayer(layer)
                return

        layer_predios = self.iface.activeLayer()
        if not layer_predios or layer_predios.geometryType() != QgsWkbTypes.PolygonGeometry:
            self.iface.messageBar().pushWarning("Advertencia", "Selecciona una capa de polígonos.")
            return

        calles = QgsProject.instance().mapLayersByName(nombre_capa_calles)
        if not calles:
            self.iface.messageBar().pushWarning("Advertencia", "No se encontró la capa 'Ejes_viales'.")
            return
        layer_calles = calles[0]

        salida = QgsVectorLayer("Point?crs=" + layer_predios.crs().authid(), nombre_capa, "memory")
        prov = salida.dataProvider()
        prov.addAttributes([QgsField("gid_predio", QVariant.Int), QgsField("ubicacion", QVariant.String)])
        salida.updateFields()

        for f in layer_predios.getFeatures():
            geom = f.geometry()
            if not geom:
                continue

            vertices = [v for v in geom.vertices()]
            punto_sup = max(vertices, key=lambda p: p.y())
            punto_inf = min(vertices, key=lambda p: p.y())

            g_sup = QgsGeometry.fromPointXY(punto_sup)
            g_inf = QgsGeometry.fromPointXY(punto_inf)

            cerca_sup = any(calle.geometry().distance(g_sup) < tolerancia for calle in layer_calles.getFeatures())
            cerca_inf = any(calle.geometry().distance(g_inf) < tolerancia for calle in layer_calles.getFeatures())

            if cerca_sup:
                feat = QgsFeature(salida.fields())
                feat.setGeometry(g_sup)
                feat.setAttributes([f.id(), "superior"])
                prov.addFeature(feat)

            if cerca_inf:
                feat = QgsFeature(salida.fields())
                feat.setGeometry(g_inf)
                feat.setAttributes([f.id(), "inferior"])
                prov.addFeature(feat)

        salida.updateExtents()
        QgsProject.instance().addMapLayer(salida)
