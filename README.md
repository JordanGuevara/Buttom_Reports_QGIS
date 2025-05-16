Plugin para la automatización de datos en un layout QGIS
Este plugin permite automatizar la generación de reportes en QGIS a partir de la selección de uno o varios objetos espaciales. Incluye un botón que genera informes PDF con datos personalizados según las capas de entrada y las intersecciones espaciales.

Funcionalidad principal: Botón de reporte
El botón de reporte implementado realiza lo siguiente:

Generación de reporte individual o por grupo:
Permite generar un reporte para un solo objeto (usando el gid) o para todos los objetos que pertenecen al mismo caso, según un atributo común.

Extracción automática de atributos:
Extrae y muestra información como el nombre del lote (nom_predio) y otros atributos relevantes en el reporte.

Cálculo de intersecciones:
Calcula la intersección entre el objeto seleccionado y las capas clase_suelo e influencia, mostrando únicamente aquellas con un área mayor o igual a 1 ha. Si no se cumple este umbral, se muestra solo el área total del lote.

Formato dinámico del layout:
El diseño del layout se adapta al número de objetos y a los resultados obtenidos, incluyendo tablas separadas por categoría (clase de suelo e influencia).

Vista previa editable:
El campo observaciones del layout se puede editar antes de exportar el PDF.

Requisitos
QGIS 3.x

Capas con geometrías válidas y campos esperados (gid, nom_predio, etc.)

Uso
Selecciona uno o más objetos en la capa base.

Haz clic en el botón de reporte.

Elige entre generar un reporte individual o por caso.

Se genera un archivo PDF con los datos calculados automáticamente.

