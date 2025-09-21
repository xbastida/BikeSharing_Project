import sys
from pathlib import Path

# Add the project root to the path to enable relative imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.Distance_to_bikelane import distances_to_bikelanes
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# Define relative paths
bike_gpkg = project_root / "data" / "geopackages" / "bike_edges.gpkg"
points_gpkg = Path(__file__).parent / "Stations.gpkg"
output_path = Path(__file__).parent / "Distance_to_bikelanes.html"

bike_layer = "bike"
points_layer = "stations"

result = distances_to_bikelanes(
    bike_gpkg, points_gpkg, bike_layer, points_layer, output_path
)
print(result[["dist_to_bike_m"]].head())
