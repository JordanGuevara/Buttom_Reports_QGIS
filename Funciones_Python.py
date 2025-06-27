from qgis.core import *
from qgis.gui import *
import math

# --------------------- escala_optima ---------------------
# Calcula una escala de visualización óptima para una geometría, basada en su ancho o alto.
# Compara la escala estimada con un conjunto de escalas estándar y devuelve la más cercana.
@qgsfunction(group='Custom', referenced_columns=[])
def escala_optima(geom, feature, parent):
    if geom is None or geom.isEmpty():
        return 1000  

    bounds = geom.boundingBox()
    ancho = bounds.width()
    alto = bounds.height()

    max_dimension = max(ancho, alto)
    escala = max_dimension * 12
    escalas_estandar = [1000, 1600, 2600, 6000, 10000, 26000, 60000, 1060000]
    escala_final = min(escalas_estandar, key=lambda x: abs(x - escala))

    return escala_final

# --------------------- resumen_intersecciones ---------------------
# Calcula el área de intersección entre una geometría y las capas 'clase_suelo' e 'influencia'.
# Devuelve un resumen de áreas (en hectáreas) o el área total si es muy pequeña.
@qgsfunction(group='Custom', referenced_columns=['geometry'])
def resumen_intersecciones(geometry, feature, parent):
    try:
        clase_layer = QgsProject.instance().mapLayersByName("clase_suelo")
        influencia_layer = QgsProject.instance().mapLayersByName("influencia")
        
        if not clase_layer and not influencia_layer:
            return "Capas 'clase_suelo' o 'influencia' no encontradas."

        clase_layer = clase_layer[0] if clase_layer else None
        influencia_layer = influencia_layer[0] if influencia_layer else None

        resumen_clase = []
        resumen_influencia = []
        mostrar_area_total = False  

        # Intersección con clase_suelo
        if clase_layer:
            for suelo in clase_layer.getFeatures():
                inter = geometry.intersection(suelo.geometry())
                if not inter.isEmpty():
                    area = inter.area() / 10000  # ha
                    if area >= 1:
                        resumen_clase.append(round(area, 4))
                    else:
                        mostrar_area_total = True  

        # Intersección con influencia
        if influencia_layer:
            for inf in influencia_layer.getFeatures():
                inter = geometry.intersection(inf.geometry())
                if not inter.isEmpty():
                    area = inter.area() / 10000  # ha
                    if area >= 1:
                        resumen_influencia.append(round(area, 4))
                    else:
                        mostrar_area_total = True  

        # Elegir el resumen más representativo
        if len(resumen_clase) >= len(resumen_influencia) and resumen_clase:
            resumen_clase.reverse()
            resumen = [f"{a} ha" for a in resumen_clase]
        elif resumen_influencia:
            resumen_influencia.reverse()
            resumen = [f"{a} ha" for a in resumen_influencia]
        else:
            resumen = [f"{round(geometry.area() / 10000, 4)} ha"]

        if mostrar_area_total:
            return f"{round(geometry.area() / 10000, 4)} ha"

        return "\n────────────\n".join(resumen)

    except Exception as e:
        return f"Error: {str(e)}"

# --------------------- geom_caso ---------------------
# Une todas las geometrías de una capa cuyo campo 'caso' coincida con el valor dado.
# Devuelve una geometría múltiple (MultiPolygon).
@qgsfunction(group='Custom', referenced_columns=['caso'])
def geom_caso(capa_nombre, feature_caso, feature_id, feature_geom, parent):
    layer = QgsProject.instance().mapLayersByName(capa_nombre)
    if not layer:
        return None
    layer = layer[0]

    geometries = []
    for f in layer.getFeatures():
        if f["caso"] == feature_caso:
            geometries.append(f.geometry())

    if not geometries:
        return None

    combined = QgsGeometry.collectGeometry(geometries)
    return combined

# --------------------- interseccion_suelo ---------------------
# Determina la(s) clase(s) de suelo que intersectan con una geometría.
# Si el área intersectada es menor, intenta determinarlo por el centroide.
@qgsfunction(group='Custom', referenced_columns=['geometry'])
def interseccion_suelo(value, feature, parent):
    if value is None or value.isEmpty():
        return "Sin intersección"

    layers = QgsProject.instance().mapLayersByName('clase_suelo')
    if not layers:
        return "Capa 'clase_suelo' no encontrada"
    capa = layers[0]

    area_por_clase = {}

    for suelo in capa.getFeatures():
        inter = value.intersection(suelo.geometry())
        if not inter.isEmpty():
            area = inter.area() / 10000  # ha
            if area > 0:
                clase = str(suelo['clase'])
                area_por_clase[clase] = area_por_clase.get(clase, 0) + area

    clases_validas = {clase: round(area, 4) for clase, area in area_por_clase.items() if area >= 1}

    if not clases_validas:
        centroide = value.centroid()
        for suelo in capa.getFeatures():
            if suelo.geometry().contains(centroide):
                return str(suelo['clase'])
        return "Sin clase de suelo encontrada"

    if len(clases_validas) == 1:
        return list(clases_validas.keys())[0]
    else:
        resumen_ordenado = sorted(clases_validas.items(), key=lambda x: x[1])
        return "\n────────────\n".join([f"{clase}" for clase, area in resumen_ordenado])

# --------------------- interseccion_influencia ---------------------
# Determina el tipo de influencia dominante sobre una geometría.
# Si el área es menor a 1 ha, se clasifica como "MINIFUNDIO".
@qgsfunction(group='Custom', referenced_columns=['geometry'])
def interseccion_influencia(value, feature, parent):
    if value is None or value.isEmpty():
        return "Sin intersección"

    area_total = value.area() / 10000  # ha
    if area_total < 1:
        return "MINIFUNDIO"

    capa_influencia = QgsProject.instance().mapLayersByName('influencia')
    if not capa_influencia:
        return "Capa 'influencia' no encontrada"
    capa_influencia = capa_influencia[0]

    area_por_influencia = {}

    for inf in capa_influencia.getFeatures():
        inter = value.intersection(inf.geometry())
        if not inter.isEmpty():
            area = inter.area() / 10000  # ha
            if area > 0:
                tipo = str(inf['influencia'])
                area_por_influencia[tipo] = area_por_influencia.get(tipo, 0) + area

    influencias_validas = {tipo: round(area, 4) for tipo, area in area_por_influencia.items() if area >= 1}

    if not influencias_validas:
        centroide = value.centroid()
        for inf in capa_influencia.getFeatures():
            if inf.geometry().contains(centroide):
                return str(inf['influencia'])
        return "Sin influencia encontrada"

    if len(influencias_validas) == 1:
        return list(influencias_validas.keys())[0]
    else:
        resumen_ordenado = sorted(influencias_validas.items(), key=lambda x: x[1], reverse=True)
        return "\n────────────\n".join([f"{tipo}" for tipo, area in resumen_ordenado])

# --------------------- parroquia_predominante ---------------------
# Retorna el código de parroquia (últimos 2 dígitos del campo 'dpa_parroq') con mayor área de superposición.
@qgsfunction(group='Custom', referenced_columns=['geometry'])
def parroquia_predominante(value, feature, parent):
    if value is None or value.isEmpty():
        return "Sin intersección"

    capa_parroquias = QgsProject.instance().mapLayersByName('parroquias')[0]

    mayor_area = 0
    codigo_parroquia_mayor = "Sin intersección"
    geom_lote_rural = value

    for parroquia in capa_parroquias.getFeatures():
        interseccion = geom_lote_rural.intersection(parroquia.geometry())
        if not interseccion.isEmpty():
            area_interseccion = interseccion.area()
            if area_interseccion > mayor_area:
                mayor_area = area_interseccion
                codigo = str(parroquia['dpa_parroq'])
                codigo_parroquia_mayor = codigo[-2:] if len(codigo) >= 2 else codigo

    return codigo_parroquia_mayor

# --------------------- poligono_predominante ---------------------
# Retorna el valor del campo 'poligono' de la capa con mayor área de intersección con la geometría.
# Transforma CRS si es necesario.
@qgsfunction(group='Custom', referenced_columns=[])
def poligono_predominante(geom, feature, parent):
    if geom is None or geom.isEmpty():
        return "Geometría vacía"

    capa_poligono = None
    for layer in QgsProject.instance().mapLayers().values():
        if layer.name().lower() == 'poligono':
            capa_poligono = layer
            break

    if not capa_poligono:
        return "Capa 'poligono' no encontrada"

    crs_lote = QgsProject.instance().crs()
    crs_poligono = capa_poligono.crs()

    if crs_lote != crs_poligono:
        try:
            transform = QgsCoordinateTransform(crs_lote, crs_poligono, QgsProject.instance())
            geom = QgsGeometry(geom)
            geom.transform(transform)
        except Exception as e:
            return f"Error en transformación: {str(e)}"

    mayor_area = 0
    valor_predominante = None

    for pol in capa_poligono.getFeatures():
        pol_geom = pol.geometry()
        if pol_geom and not pol_geom.isEmpty() and geom.intersects(pol_geom):
            inter = geom.intersection(pol_geom)
            if inter and not inter.isEmpty():
                area = inter.area()
                if area > mayor_area:
                    mayor_area = area
                    valor_predominante = pol["poligono"]

    return valor_predominante if valor_predominante else "Sin intersección"
