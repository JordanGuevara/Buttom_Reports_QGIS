import os
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QInputDialog
from qgis.PyQt.QtGui import QIcon
from qgis.core import (
    QgsProject,
    QgsLayoutItemAttributeTable,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
)
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

            opciones = ["Reporte del Lote (gid)", "Reporte por casos (caso)", "Reporte por ID (id)"]
            eleccion, ok = QInputDialog.getItem(self.iface.mainWindow(), "Tipo de reporte", "¿Qué deseas generar?", opciones, editable=False)

            if not ok:
                return

            campo_usado = ""
            filtro = ""

            if eleccion == opciones[0]:
                gid_valor = feature["gid"]
                filtro = f'"gid" = \'{gid_valor}\'' if isinstance(gid_valor, str) else f'"gid" = {gid_valor}'
                campo_usado = "gid"

            elif eleccion == opciones[1]:
                caso_valor = feature["caso"]
                campo_usado = "caso"

                geom_lote = feature.geometry()
                capas_parroquias = QgsProject.instance().mapLayersByName("parroquias")
                if not capas_parroquias:
                    QMessageBox.critical(None, "Error", "No se encontró la capa 'parroquias' en el proyecto.")
                    return
                capa_parroquias = capas_parroquias[0]

                parroquia_geom = None
                for parroquia in capa_parroquias.getFeatures():
                    if parroquia.geometry().contains(geom_lote):
                        parroquia_geom = parroquia.geometry()
                        break

                if not parroquia_geom:
                    QMessageBox.warning(None, "Error", "No se encontró la parroquia correspondiente al lote seleccionado.")
                    return

                filtro_geom = f"intersects($geometry, geom_from_wkt('{parroquia_geom.asWkt()}'))"
                filtro = f'"caso" = \'{caso_valor}\' AND {filtro_geom}'

                # Mostrar solo etiquetas del mismo caso
                if layer.labelsEnabled():
                    etiquetas = layer.labeling()
                    provider = etiquetas.settings().clone()
                    provider.fieldName = "nom_predio"  # Asegúrate que es el campo correcto
                    provider.setDataDefinedProperty(
                        QgsVectorLayer.SimpleLabeling.ShowLabel,
                        True,
                        True,
                        f'"caso" = \'{caso_valor}\''
                    )
                    layer.setLabeling(QgsVectorLayer.SimpleLabeling(provider))
                    layer.triggerRepaint()


            elif eleccion == opciones[2]:
                id_valor = feature["id"]
                filtro = f'"id" = \'{id_valor}\'' if isinstance(id_valor, str) else f'"id" = {id_valor}'
                campo_usado = "id"

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
                    atlas.setFilterFeatures(bool(filtro))
                    atlas.setFilterExpression(filtro)
                    atlas.setEnabled(True)

                    for item in layout_obj.items():
                        if isinstance(item, QgsLayoutItemAttributeTable):
                            item.setFilterFeatures(True)
                            item.setFilterExpression(f'"{campo_usado}" = @atlas_feature[\'{campo_usado}\']')

                    self.iface.openLayoutDesigner(layout_obj)

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Ocurrió un error: {str(e)}")
