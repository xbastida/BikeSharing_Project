import geopandas as gpd
from shapely.geometry import Point
import numpy as np

# Center of Donostia-San Sebastián (approx)
center_lon, center_lat = -1.98, 43.32

# How many random points
n_points = 70

# Random radius in meters (e.g. within 2 km of city center)
radius_m = 2000

# Generate random polar coordinates
angles = np.random.uniform(0, 2 * np.pi, n_points)
radii = np.random.uniform(0, radius_m, n_points)

# Project to local CRS (meters) to generate offsets
center = gpd.GeoSeries([Point(center_lon, center_lat)], crs="EPSG:4326").to_crs(
    epsg=25830
)
cx, cy = center.geometry.iloc[0].x, center.geometry.iloc[0].y

# Create random points around center
xs = cx + radii * np.cos(angles)
ys = cy + radii * np.sin(angles)
points = [Point(x, y) for x, y in zip(xs, ys)]

# Make GeoDataFrame
gdf_points = gpd.GeoDataFrame(geometry=points, crs="EPSG:25830").to_crs(epsg=4326)

# Save to GeoPackage
out_path = "random_points_sansebastian.gpkg"
gdf_points.to_file(out_path, layer="points", driver="GPKG")

print(f"✅ Saved {n_points} random points to {out_path}")
print(gdf_points.head())
