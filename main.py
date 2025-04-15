import os
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QInputDialog
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject
from qgis.utils import iface

class LayoutPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.accion = None
        self.icono_path = os.path.join(os.path.dirname(__file__), "icono_reporte.png")

    def initGui(self):
        icono = QIcon(self.icono_path) if os.path.exists(self.icono_path) else QIcon.fromTheme("document-print")
        self.accion = QAction(icono, "Abrir composición con Atlas", self.iface.mainWindow())
        self.accion.triggered.connect(self.mostrar_composiciones)
        self.iface.addToolBarIcon(self.accion)

    def unload(self):
        if self.accion:
            self.iface.removeToolBarIcon(self.accion)

    def mostrar_composiciones(self):
        try:
            layer = self.iface.activeLayer()
            if not layer or not layer.selectedFeatureCount():
                QMessageBox.warning(None, "Selecciona una entidad", "Selecciona una entidad en la capa activa.")
                return

            selected_features = layer.selectedFeatures()
            feature = selected_features[0]
            gid_valor = feature["gid"]

            if isinstance(gid_valor, str):
                filtro = f'"gid" = \'{gid_valor}\''
            else:
                filtro = f'"gid" = {gid_valor}'

            manager = QgsProject.instance().layoutManager()
            layouts = manager.printLayouts()

            if not layouts:
                QMessageBox.information(None, "Composiciones", "No hay composiciones en el proyecto.")
                return

            nombres = [layout.name() for layout in layouts]
            seleccionado, ok = QInputDialog.getItem(self.iface.mainWindow(), "Seleccionar composición", "Elige una:", nombres, editable=False)

            if ok and seleccionado:
                layout_obj = next((l for l in layouts if l.name() == seleccionado), None)
                if layout_obj:
                    atlas = layout_obj.atlas()
                    atlas.setCoverageLayer(layer)
                    atlas.setFilterFeatures(True)
                    atlas.setFilterExpression(filtro)
                    atlas.setEnabled(True)

                    self.iface.openLayoutDesigner(layout_obj)

                    # -----------------------------
                    # Cálculo del área e intersecciones
                    # -----------------------------
                    texto = ""
                    interseccion_hecha = False

                    # --- INFLUENCIA ---
                    influencia_layer = QgsProject.instance().mapLayersByName("influencia")
                    if influencia_layer:
                        influencia_layer = influencia_layer[0]
                        resumen_influencia = {}

                        for inf in influencia_layer.getFeatures():
                            inter = feature.geometry().intersection(inf.geometry())
                            if not inter.isEmpty():
                                area = inter.area() / 10000
                                tipo = inf["influencia"]
                                resumen_influencia[tipo] = resumen_influencia.get(tipo, 0) + area

                        if resumen_influencia:
                            texto += "Distribución por influencia:\n"
                            for t, a in resumen_influencia.items():
                                texto += f"  {t}: {round(a, 4)} ha\n"
                            interseccion_hecha = True

                    # Si no hubo intersección con influencia, se intenta con clase_suelo
                    if not interseccion_hecha:
                        clase_layer = QgsProject.instance().mapLayersByName("clase_suelo")
                        if clase_layer:
                            clase_layer = clase_layer[0]
                            resumen_clase = {}

                            for suelo in clase_layer.getFeatures():
                                inter = feature.geometry().intersection(suelo.geometry())
                                if not inter.isEmpty():
                                    area = inter.area() / 10000
                                    clase = suelo["clase"]
                                    resumen_clase[clase] = resumen_clase.get(clase, 0) + area

                            if resumen_clase:
                                texto += "Distribución por clase de suelo:\n"
                                for c, a in resumen_clase.items():
                                    texto += f"  Clase {c}: {round(a, 4)} ha\n"
                                interseccion_hecha = True

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Ocurrió un error: {str(e)}")

        # Guardar como variable de proyecto para mostrar en el reporte
        QgsProject.instance().setCustomVariable("resumen", texto)