import sys
sys.path.insert(0, r"D:\BikeSharing_Project\utils")
from Plot_gpkg import plot_layer_from_gpkg


gpkg_path = r"D:\Proyecto_auxiliares\Proyecto_learn\bike_edges.gpkg"
layer_name = "bike"
output_html = r"data/geopackages/yessir.html"

k = plot_layer_from_gpkg(gpkg_path, layer_name, output_html)