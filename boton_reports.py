from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.utils import iface

# Variable global para guardar la referencia al botón
accion = None

# Función que ejecutará el script
def ejecutar_reporte():
    try:
        # Ruta completa del archivo Python
        ruta_script = r"C:\Users\lady.angulo\Documents\Archivo_Python\reports.py"
        
        # Ejecutar el script Python
        exec(open(ruta_script).read())
        QMessageBox.information(None, "Éxito", "✅ El reporte se generó correctamente.")
    
    except Exception as e:
        QMessageBox.critical(None, "Error", f"❌ Error al generar el reporte: {str(e)}")

# Agregar un botón a la barra de herramientas
def agregar_boton():
    global accion  # Hacer que la variable 'accion' sea global
    # Crear la acción para el botón
    accion = QAction("Generar Reporte", iface.mainWindow())
    
    # Conectar la acción al evento de clic
    accion.triggered.connect(ejecutar_reporte)
    
    # Añadir el botón a la barra de herramientas de QGIS
    iface.addToolBarIcon(accion)

# Función para eliminar el botón de la barra de herramientas
def eliminar_boton():
    global accion
    if accion:
        iface.removeToolBarIcon(accion)
        print("Botón eliminado de la barra de herramientas.")
    else:
        print("No se ha encontrado el botón.")
