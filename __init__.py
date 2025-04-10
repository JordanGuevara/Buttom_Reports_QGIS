#Ejecución del plugin
def classFactory(iface):
    from .main import LayoutPlugin
    return LayoutPlugin(iface)
