import sys
from pathlib import Path

actual_folder_path = Path(__file__).parent
project_root = Path(__file__).parent.parent
sys.path.insert(0,str(project_root))
from utils.Plot_gpkg import plot_layer_from_gpkg


gpkg_path = actual_folder_path / "drive_edges.gpkg"
layer_name = "drive"
output_html = actual_folder_path / "driving_roads.html"

k = plot_layer_from_gpkg(gpkg_path, layer_name, output_html)