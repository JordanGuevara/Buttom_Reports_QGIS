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

            filtro = f'"gid" = \'{gid_valor}\'' if isinstance(gid_valor, str) else f'"gid" = {gid_valor}'

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
                    # Actualizar el atlas antes de abrir
                    atlas = layout_obj.atlas()
                    atlas.setCoverageLayer(layer)
                    atlas.setFilterFeatures(True)
                    atlas.setFilterExpression(filtro)
                    atlas.setEnabled(True)

                    # Abre el layout — esto "refresca" la ventana aunque esté abierta
                    self.iface.openLayoutDesigner(layout_obj)

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Ocurrió un error: {str(e)}")
