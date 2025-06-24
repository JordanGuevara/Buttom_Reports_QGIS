import os
from itertools import combinations  # ya lo usas para extremos

from qgis.PyQt.QtWidgets import QAction, QMessageBox, QInputDialog
from qgis.PyQt.QtGui import QIcon

from qgis.core import (
    QgsProject,
    QgsLayoutItemAttributeTable,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsField,
    QgsPointXY,
    QgsRenderContext,
    QgsVectorLayerSimpleLabeling,
    QgsPalLayerSettings,
    QgsTextFormat
)

from qgis.PyQt.QtCore import QVariant
from qgis.utils import iface
from PyQt5.QtGui import QColor


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

            elif eleccion == opciones[1]:  # Reporte por casos (caso)
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

                # Filtro base por el campo "caso" y geometría
                filtro_geom = f"intersects($geometry, geom_from_wkt('{parroquia_geom.asWkt()}'))"
                filtro_base = f'"caso" = \'{caso_valor}\' AND {filtro_geom}'

                # Preguntar si se desea añadir un campo adicional
                respuesta = QMessageBox.question(
                    None,
                    "¿Agregar filtro adicional?",
                    "¿Deseas añadir un filtro por otro campo?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if respuesta == QMessageBox.Yes:
                    # Obtener campos disponibles, excluyendo 'caso'
                    campos = [f.name() for f in layer.fields() if f.name() != "caso"]
                    campo_extra, ok = QInputDialog.getItem(
                        self.iface.mainWindow(), "Campo adicional",
                        "Selecciona el campo adicional:", campos, editable=False
                    )
                    if not ok:
                        return

                    valor_extra, ok = QInputDialog.getText(
                        self.iface.mainWindow(), "Valor del campo",
                        f"Ingrese el valor exacto para el campo '{campo_extra}':"
                    )
                    if not ok or valor_extra.strip() == "":
                        return

                    # Detectar tipo para comillas o no
                    tipo_extra = layer.fields().lookupField(campo_extra)
                    tipo = layer.fields()[tipo_extra].type()
                    if tipo in (QVariant.Int, QVariant.Double):
                        filtro_extra = f'"{campo_extra}" = {valor_extra}'
                    else:
                        filtro_extra = f'"{campo_extra}" = \'{valor_extra}\''

                    filtro = f'{filtro_base} AND {filtro_extra}'
                else:
                    filtro = filtro_base

            elif eleccion == opciones[2]:  
                id_valor = feature["id"]  
                filtro = f'"id" = \'{id_valor}\'' if isinstance(id_valor, str) else f'"id" = {id_valor}'  
                campo_usado = "id"  
  
                crs = QgsProject.instance().crs()  
                crs_id = crs.authid()  
  
                geom_predio = feature.geometry()  
                vertices = list(geom_predio.vertices())  
  
                capas_ejes = QgsProject.instance().mapLayersByName("Ejes Viales")  
                if not capas_ejes:  
                    QMessageBox.critical(None, "Error", "No se encontró la capa 'Ejes Viales'.")  
                    return  
                capa_ejes = capas_ejes[0]  
  
                nombre_capa = "Extremos_Cercanos"  
                existente = None  
                for lyr in QgsProject.instance().mapLayers().values():  
                    if lyr.name() == nombre_capa:  
                        existente = lyr  
                        break  
  
                if existente:  
                    QgsProject.instance().removeMapLayer(existente)  
  
                capa_puntos = QgsVectorLayer(f"Point?crs={crs_id}", nombre_capa, "memory")  
                prov_puntos = capa_puntos.dataProvider()  
                prov_puntos.addAttributes([  
                    QgsField("Pts", QVariant.Int),  
                    QgsField("Este(X)", QVariant.Double),  
                    QgsField("Norte(Y)", QVariant.Double)  
                ])  
                capa_puntos.updateFields()  
  
                from itertools import combinations  
                distancias = []  
                for i, j in combinations(range(len(vertices)), 2):  
                    p1 = vertices[i]  
                    p2 = vertices[j]  
                    d = ((p1.x() - p2.x())**2 + (p1.y() - p2.y())**2)**0.5  
                    distancias.append((d, i, j))  
  
                distancias.sort(reverse=True)  
                indices_usados = set()  
                extremos = []  
  
                for _, i, j in distancias:  
                    if len(extremos) >= 4:  
                        break  
                    if i not in indices_usados:  
                        extremos.append(vertices[i])  
                        indices_usados.add(i)  
                    if len(extremos) >= 4:  
                        break  
                    if j not in indices_usados:  
                        extremos.append(vertices[j])  
                        indices_usados.add(j)  
  
                distancia_umbral = 3  # metros  
                contador = 1  
                for v in extremos:  
                    punto = QgsGeometry.fromPointXY(QgsPointXY(v.x(), v.y()))  
                    for eje in capa_ejes.getFeatures():  
                        if punto.distance(eje.geometry()) <= distancia_umbral:  
                            fet = QgsFeature()  
                            fet.setGeometry(punto)  
                            fet.setAttributes([  
                                contador,  
                                round(v.x(), 4),  
                                round(v.y(), 4)  
                            ])  
                            prov_puntos.addFeatures([fet])  
                            contador += 1  
                            break  
  
                capa_puntos.updateExtents()  
                QgsProject.instance().addMapLayer(capa_puntos)  
  
                etiqueta = QgsPalLayerSettings()  
                texto_format = QgsTextFormat()  
                texto_format.setSize(10)  
                texto_format.setNamedStyle("Bold")  
  
                etiqueta.fieldName = "Pts"  
                etiqueta.placement = QgsPalLayerSettings.OverPoint  
                etiqueta.enabled = True  
                etiqueta.setFormat(texto_format)  
  
                context = QgsRenderContext()  
                etiqueta_ref = QgsVectorLayerSimpleLabeling(etiqueta)  
                capa_puntos.setLabelsEnabled(True)  
                capa_puntos.setLabeling(etiqueta_ref)  
                capa_puntos.triggerRepaint()

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
