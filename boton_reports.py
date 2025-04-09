import os
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface

# Variable global para el botón
accion = None

# Usuario actual
usuario = os.getlogin()

# Rutas
ruta_icono = fr"C:\Users\{usuario}\Documents\Archivo_Python\icono_reporte.png"
ruta_script = fr"C:\Users\{usuario}\Documents\Archivo_Python\reports.py"  # Aquí se evalúa correctamente el usuario

# Función para ejecutar el script del reporte
def ejecutar_reporte():
    try:
        # Asegúrate de usar la ruta con el usuario correctamente evaluado
        exec(open(ruta_script).read())
        QMessageBox.information(None, "Éxito", "✅ El reporte se generó correctamente.")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"❌ Error al generar el reporte: {str(e)}")

# Agregar botón con ícono predeterminado
def agregar_boton():
    global accion
    # Si ya existe un botón, lo eliminamos antes de agregar el nuevo
    if accion:
        iface.removeToolBarIcon(accion)
        print("🧹 Botón anterior eliminado.")
    
    # Usar un ícono predeterminado
    icono = QIcon.fromTheme("dialog-information")  # Ícono estándar
    accion = QAction(icono, "Reporte", iface.mainWindow())  # Título para el botón
    accion.triggered.connect(ejecutar_reporte)
    iface.addToolBarIcon(accion)
    print("➕ Nuevo botón agregado.")

# Eliminar botón
def eliminar_boton():
    global accion
    if accion:
        iface.removeToolBarIcon(accion)
        print("🧹 Botón eliminado.")
        accion = None  # Resetear la variable
    else:
        print("❗ Botón no encontrado.")
