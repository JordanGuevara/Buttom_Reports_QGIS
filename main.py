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

                    # --- CLASE SUELO ---
                    clase_layer = QgsProject.instance().mapLayersByName("clase_suelo")
                    if clase_layer:
                        clase_layer = clase_layer[0]
                        resumen_clase = {}
                        mostrar_area_total = False  # Flag para saber si alguna intersección es menor a 1 ha

                        for suelo in clase_layer.getFeatures():
                            inter = feature.geometry().intersection(suelo.geometry())
                            if not inter.isEmpty():
                                area = inter.area() / 10000  # Convertimos a hectáreas
                                clase = suelo["clase"]

                                # Si el área es menor a 1 ha, no sumar ni mostrar, solo el área total
                                if area < 1:
                                    mostrar_area_total = True
                                    break  # Salir si alguna intersección es menor a 1 ha

                                # Si el área es mayor o igual a 1 ha, acumulamos normalmente
                                if clase in resumen_clase:
                                    resumen_clase[clase] += area
                                else:
                                    resumen_clase[clase] = area

                        if mostrar_area_total:
                            texto += f"Área total del lote: {round(feature.geometry().area() / 10000, 4)} ha\n"
                        else:
                            if resumen_clase:
                                texto += "Distribución por clase de suelo:\n"
                                for c, a in resumen_clase.items():
                                    texto += f"  Clase {c}: {round(a, 4)} ha\n"
                            else:
                                texto += "No hay intersección con clase de suelo.\n"
                    else:
                        texto += "Capa 'clase_suelo' no encontrada.\n"

                    # --- INFLUENCIA ---
                    influencia_layer = QgsProject.instance().mapLayersByName("influencia")
                    if influencia_layer:
                        influencia_layer = influencia_layer[0]
                        resumen_influencia = {}
                        mostrar_area_total = False  # Flag para saber si alguna intersección es menor a 1 ha

                        for inf in influencia_layer.getFeatures():
                            inter = feature.geometry().intersection(inf.geometry())
                            if not inter.isEmpty():
                                area = inter.area() / 10000  # Convertimos a hectáreas
                                tipo = inf["influencia"]

                                # Si el área es menor a 1 ha, no sumar ni mostrar, solo el área total
                                if area < 1:
                                    mostrar_area_total = True
                                    break  # Salir si alguna intersección es menor a 1 ha

                                # Si el área es mayor o igual a 1 ha, acumulamos normalmente
                                if tipo in resumen_influencia:
                                    resumen_influencia[tipo] += area
                                else:
                                    resumen_influencia[tipo] = area

                        if mostrar_area_total:
                            texto += f"Área total del lote: {round(feature.geometry().area() / 10000, 4)} ha\n"
                        else:
                            if resumen_influencia:
                                texto += "\nDistribución por influencia:\n"
                                for t, a in resumen_influencia.items():
                                    texto += f"  {t}: {round(a, 4)} ha\n"
                            else:
                                texto += "\nNo hay intersección con influencia.\n"
                    else:
                        texto += "\nCapa 'influencia' no encontrada.\n"

                    QMessageBox.information(None, "Resumen de intersecciones", texto)

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Ocurrió un error: {str(e)}")
