import sys
from pathlib import Path
import geopandas as gpd
import folium
import numpy as np

# Add the project root to the path to enable relative imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Define relative paths
bike_gpkg = project_root / "data" / "geopackages" / "bike_edges.gpkg"
walk_gpkg = project_root / "data" / "geopackages" / "walk_edges.gpkg"
output_dir = Path(__file__).parent

print("Loading bike lanes and walkable ways...")

# Load data with proper layer names
try:
    bike_lanes = gpd.read_file(bike_gpkg, layer="bike")
    print(f"Loaded {len(bike_lanes)} bike lane segments")
except:
    bike_lanes = gpd.read_file(bike_gpkg)
    print(f"Loaded {len(bike_lanes)} bike lane segments (default layer)")

try:
    walkable_ways = gpd.read_file(walk_gpkg, layer="walk")
    print(f"Loaded {len(walkable_ways)} walkable way segments")
except:
    walkable_ways = gpd.read_file(walk_gpkg)
    print(f"Loaded {len(walkable_ways)} walkable way segments (default layer)")

# Make sure both are in the same projected CRS (UTM 30N for Donostia)
print("Converting to UTM 30N (EPSG:25830)...")
bike_lanes = bike_lanes.to_crs(epsg=25830)
walkable_ways = walkable_ways.to_crs(epsg=25830)

# Define threshold distance in meters
DISTANCE_THRESHOLD = 50  # 50 meters

print(f"Using fast Euclidean distance calculation...")

# Create a buffer around bike lanes
print("Creating buffer around bike lanes...")
bike_buffer = bike_lanes.buffer(DISTANCE_THRESHOLD)

# Dissolve into one big geometry (union)
print("Creating union of all bike lane buffers...")
bike_union = bike_buffer.union_all()

# Filter walkable ways within threshold distance of any bike lane
print("Filtering walkable ways within buffer...")
walkable_near_bike = walkable_ways[walkable_ways.geometry.intersects(bike_union)]

print(f"Found {len(walkable_near_bike)} walkable way segments within {DISTANCE_THRESHOLD}m of bike lanes")

# Create filtered bike lane archive (only bike lanes that have walkable ways nearby)
print("Creating filtered bike lane archive...")
bike_lanes_filtered = bike_lanes[bike_lanes.geometry.intersects(walkable_near_bike.union_all())]

print(f"Filtered bike lanes: {len(bike_lanes_filtered)} segments")

# Save the filtered data
walkable_output = output_dir / f"walkable_within_{DISTANCE_THRESHOLD}m_bikelanes_euclidean.gpkg"
bike_output = output_dir / f"bikelanes_near_walkable_{DISTANCE_THRESHOLD}m_euclidean.gpkg"

walkable_near_bike.to_file(walkable_output, driver="GPKG", layer="walkable_near_bike")
bike_lanes_filtered.to_file(bike_output, driver="GPKG", layer="bike_lanes_filtered")

print(f"Saved filtered walkable ways to: {walkable_output}")
print(f"Saved filtered bike lanes to: {bike_output}")

# Create interactive map
print("Creating interactive map...")

# Convert to WGS84 for mapping
bike_lanes_wgs84 = bike_lanes.to_crs(epsg=4326)
walkable_near_bike_wgs84 = walkable_near_bike.to_crs(epsg=4326)
bike_lanes_filtered_wgs84 = bike_lanes_filtered.to_crs(epsg=4326)

# Calculate map center
if not walkable_near_bike_wgs84.empty:
    # Calculate centroid of all geometries
    centroid = walkable_near_bike_wgs84.geometry.centroid
    center_lat = float(centroid.y.mean())
    center_lon = float(centroid.x.mean())
else:
    center_lat = 43.3183  # Donostia coordinates
    center_lon = -1.9812

# Create map
m = folium.Map(
    location=[center_lat, center_lon], 
    zoom_start=13, 
    tiles="cartodbpositron"
)

# Add all bike lanes (light blue)
folium.GeoJson(
    bike_lanes_wgs84.__geo_interface__,
    name="All Bike Lanes",
    style_function=lambda _: {"color": "#87CEEB", "weight": 2, "opacity": 0.6},
    tooltip="Bike Lane"
).add_to(m)

# Add filtered bike lanes (dark blue)
folium.GeoJson(
    bike_lanes_filtered_wgs84.__geo_interface__,
    name=f"Bike Lanes Near Walkable Routes ({DISTANCE_THRESHOLD}m)",
    style_function=lambda _: {"color": "#1f78b4", "weight": 4, "opacity": 0.8},
    tooltip="Filtered Bike Lane"
).add_to(m)

# Add filtered walkable ways (green)
folium.GeoJson(
    walkable_near_bike_wgs84.__geo_interface__,
    name=f"Walkable Routes Near Bike Lanes ({DISTANCE_THRESHOLD}m)",
    style_function=lambda _: {"color": "#33a02c", "weight": 3, "opacity": 0.7},
    tooltip="Walkable Route"
).add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

# Save map
map_output = output_dir / f"walkable_bikelanes_constraint_{DISTANCE_THRESHOLD}m_euclidean.html"
m.save(str(map_output))

print(f"Interactive map saved to: {map_output}")

# Print summary statistics
print("\n" + "="*60)
print("EUCLIDEAN DISTANCE ANALYSIS SUMMARY")
print("="*60)
print(f"Total bike lane segments: {len(bike_lanes)}")
print(f"Total walkable way segments: {len(walkable_ways)}")
print(f"Walkable segments within {DISTANCE_THRESHOLD}m of bike lanes: {len(walkable_near_bike)}")
print(f"Bike lane segments near walkable routes: {len(bike_lanes_filtered)}")
print(f"Percentage of walkable ways near bike lanes: {len(walkable_near_bike)/len(walkable_ways)*100:.1f}%")
print(f"Percentage of bike lanes near walkable routes: {len(bike_lanes_filtered)/len(bike_lanes)*100:.1f}%")
print("\nNote: Distances calculated using Euclidean (straight-line) distance")
print("="*60)
