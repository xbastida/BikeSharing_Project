import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx

bici = gpd.read_file('data/geopackages/bike_edges.gpkg')

drive = gpd.read_file('data/geopackages/drive_edges.gpkg')

walk = gpd.read_file('data/geopackages/walk_edges.gpkg')

building = gpd.read_file('data/geopackages/buildings-small.gpkg')




