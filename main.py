import os
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QInputDialog
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject, QgsExpressionContextUtils
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
            gid_valor = feature["gid"]  # Cambia "gid" si usas otro campo

            # Crear expresión de filtro
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

                    # -----------------------------------------
                    # CÁLCULO DEL ÁREA Y GUARDADO EN VARIABLE
                    # -----------------------------------------
                    area_total_m2 = feature.geometry().area()
                    area_total_ha = area_total_m2 / 10000

                    if area_total_ha > 1:
                        resumen = f"Área total: {round(area_total_ha, 4)} ha"
                        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), "resumen_clases", resumen)
                    else:
                        # Buscar capa 'clase_suelo'
                        suelo_layer = QgsProject.instance().mapLayersByName("clase_suelo")
                        if suelo_layer:
                            suelo_layer = suelo_layer[0]
                            resumen_dict = {}

                            for suelo in suelo_layer.getFeatures():
                                interseccion = feature.geometry().intersection(suelo.geometry())
                                if not interseccion.isEmpty():
                                    area_ha = interseccion.area() / 10000
                                    clase = suelo["clase"]  # Cambia si tu campo tiene otro nombre
                                    if clase in resumen_dict:
                                        resumen_dict[clase] += area_ha
                                    else:
                                        resumen_dict[clase] = area_ha

                            if resumen_dict:
                                texto = f"Área total: {round(area_total_ha, 4)} ha\n\nDistribución por clase de suelo:\n"
                                for clase, area in resumen_dict.items():
                                    texto += f"Clase {clase}: {round(area, 4)} ha\n"
                                QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), "resumen_clases", texto)
                            else:
                                QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), "resumen_clases", "Sin intersección con clases de suelo.")
                        else:
                            QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), "resumen_clases", "Capa 'clase_suelo' no encontrada.")

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Ocurrió un error: {str(e)}")
