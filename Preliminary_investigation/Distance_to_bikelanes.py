import sys 
sys.path.insert(0, r"D:\BikeSharing_Project\utils")
from Distance_to_bikelane import distances_to_bikelanes
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# estaciones = pd.read_csv('D:\BikeSharing_Project\data\Rides\Stations_new.csv')
# print(estaciones.head())
# geometry = [Point(xy) for xy in zip(estaciones["Longitude"], estaciones["Latitude"])]
# gdf = gpd.GeoDataFrame(estaciones, geometry=geometry, crs="EPSG:4326")  
# output_path = r"D:\BikeSharing_Project\Preliminary_investigation\Stations.gpkg"
# gdf.to_file(output_path, layer="stations", driver="GPKG")
# import fiona

# print(fiona.listlayers("D:\BikeSharing_Project\Preliminary_investigation\Stations.gpkg"))

# us = gpd.read_file("D:\BikeSharing_Project\Preliminary_investigation\Stations.gpkg")
# print(us.head())

bike_gpkg = 'D:/BikeSharing_Project/data/geopackages/bike_edges.gpkg'
points_gpkg = 'D:/BikeSharing_Project/Preliminary_investigation/Stations.gpkg'
output_path= 'D:/BikeSharing_Project/Preliminary_investigation/Distance_to_bikelanes.html'

bike_layer = 'bike'
points_layer = 'stations'

result = distances_to_bikelanes(bike_gpkg, points_gpkg,bike_layer,points_layer,output_path)
print(result[["dist_to_bike_m"]].head())