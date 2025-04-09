import os
from qgis.PyQt.QtWidgets import (
    QDialog, QLabel, QLineEdit, QVBoxLayout, QFormLayout, QPushButton, QMessageBox
)
from qgis.core import (
    QgsProject, QgsPrintLayout, QgsLayoutExporter,
    QgsReadWriteContext, QgsLayoutItemLabel
)
from qgis.PyQt.QtXml import QDomDocument

# Obtener nombre de usuario del sistema
usuario = os.getlogin()

# Rutas con nombre de usuario dinámico
ruta_plantilla = fr"C:\Users\{usuario}\Documents\Archivo_Python\plantilla.qpt"
carpeta_salida = fr"C:\Users\{usuario}\Documents\Archivo_Python"

# Crear carpeta si no existe
if not os.path.exists(carpeta_salida):
    os.makedirs(carpeta_salida)

# Capa activa y entidades seleccionadas
capa = iface.activeLayer()
seleccionados = capa.selectedFeatures()

if not seleccionados:
    QMessageBox.warning(None, "Reporte", "⚠️ No hay entidad seleccionada.")
else:
    QMessageBox.information(None, "Vista previa", "👀 Se puede visualizar el reporte del lote seleccionado.")
    """ # Crear formulario para editar observaciones
    class FormularioObservaciones(QDialog):
        def __init__(self, seleccionados):
            super().__init__()
            self.setWindowTitle("Vista previa de lote y observaciones")
            layout = QVBoxLayout()

            form = QFormLayout()
            self.campos = {}

            # Mostrar atributos (solo lectura excepto 'observaciones')
            for campo in seleccionados[0].fields().names():
                valor = str(seleccionados[0][campo])
                if campo == "observaciones":
                    entrada = QLineEdit(valor)
                else:
                    entrada = QLineEdit(valor)
                    entrada.setReadOnly(True)

                self.campos[campo] = entrada
                form.addRow(QLabel(campo), entrada)

            layout.addLayout(form)

            # Botón de generar PDF
            boton_generar = QPushButton("Generar PDF")
            boton_generar.clicked.connect(self.generar_pdf)
            layout.addWidget(boton_generar)

            self.setLayout(layout)

        def generar_pdf(self):
            observaciones = self.campos['observaciones'].text()

            # Cargar plantilla
            proyecto = QgsProject.instance()
            layout = QgsPrintLayout(proyecto)
            layout.initializeDefaults()

            doc = QDomDocument()
            with open(ruta_plantilla, 'r') as f:
                doc.setContent(f.read())
            context = QgsReadWriteContext()
            layout.loadFromTemplate(doc, context)

            # Insertar valor en etiqueta "observaciones"
            for item in layout.items():
                if isinstance(item, QgsLayoutItemLabel):
                    if "observaciones" in item.text():
                        item.setText(f"Observaciones: {observaciones}")

            # Exportar a PDF
            ruta_pdf = f"{carpeta_salida}\\reporte_final.pdf"
            exportador = QgsLayoutExporter(layout)
            resultado = exportador.exportToPdf(ruta_pdf, QgsLayoutExporter.PdfExportSettings())

            if resultado == QgsLayoutExporter.Success:
                QMessageBox.information(self, "Éxito", f"✅ Reporte generado en: {ruta_pdf}")
            else:
                QMessageBox.critical(self, "Error", "❌ No se pudo exportar.")
            self.accept()

    ventana = FormularioObservaciones(seleccionados)
    ventana.exec_() """
