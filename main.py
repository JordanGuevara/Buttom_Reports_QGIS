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
                    total_area = round(feature.geometry().area() / 10000, 4)

                    # Variables para el layout
                    valores_clase_suelo = ""
                    valores_influencia = ""
                    mostrar_area_total = False

                    # --- CLASE SUELO ---
                    clase_layer = QgsProject.instance().mapLayersByName("clase_suelo")
                    if clase_layer:
                        clase_layer = clase_layer[0]
                        valores_tmp = []

                        for suelo in clase_layer.getFeatures():
                            inter = feature.geometry().intersection(suelo.geometry())
                            if not inter.isEmpty():
                                area = inter.area() / 10000
                                if area < 1:
                                    mostrar_area_total = True
                                    valores_tmp = []
                                    break
                                valores_tmp.append(f"{round(area, 4)} ha")

                        if not mostrar_area_total and valores_tmp:
                            valores_clase_suelo = "\n".join(valores_tmp) + "\n------"
                        elif mostrar_area_total:
                            valores_clase_suelo = f"{total_area} ha"
                    else:
                        valores_clase_suelo = "Capa 'clase_suelo' no encontrada."

                    # --- INFLUENCIA ---
                    influencia_layer = QgsProject.instance().mapLayersByName("influencia")
                    mostrar_area_total = False
                    if influencia_layer:
                        influencia_layer = influencia_layer[0]
                        valores_tmp = []

                        for inf in influencia_layer.getFeatures():
                            inter = feature.geometry().intersection(inf.geometry())
                            if not inter.isEmpty():
                                area = inter.area() / 10000
                                if area < 1:
                                    mostrar_area_total = True
                                    valores_tmp = []
                                    break
                                valores_tmp.append(f"{round(area, 4)} ha")

                        if not mostrar_area_total and valores_tmp:
                            valores_influencia = "\n".join(valores_tmp) + "\n------"
                        elif mostrar_area_total:
                            valores_influencia = f"{total_area} ha"
                    else:
                        valores_influencia = "Capa 'influencia' no encontrada."

                    # Guardar variables globales para usar en Layout
                    exp_context = QgsExpressionContextUtils.projectScope(QgsProject.instance())
                    exp_context.setVariable("valores_clase_suelo", valores_clase_suelo)
                    exp_context.setVariable("valores_influencia", valores_influencia)

                    # Mensaje informativo
                    texto = f"Valores guardados para el layout:\n\n"
                    texto += f"Clase suelo:\n{valores_clase_suelo}\n"
                    texto += f"Influencia:\n{valores_influencia}"
                    QMessageBox.information(None, "Resumen de intersecciones", texto)

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Ocurrió un error: {str(e)}")
