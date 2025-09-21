import geopandas as gpd

bike_lanes = gpd.read_file("D:\BikeSharing_Project\data\geopackages\bike_edges.gpkg", layer="bikelanes_layer")
walkable_ways = gpd.read_file("D:\BikeSharing_Project\data\geopackages\walk_edges.gpkg", layer="walkways_layer")

bike_lanes.to_file("bike_lanes.geojson", driver="GeoJSON")
walkable_ways.to_file("walkable_ways.geojson", driver="GeoJSON")

# Load your data (shapefiles, GeoJSON, etc.)
# Replace with your actual file paths
bike_lanes = gpd.read_file("bike_lanes.geojson")
walkable_ways = gpd.read_file("walkable_ways.geojson")

# Make sure both are in the same projected CRS (meters, not degrees!)
# Example: UTM or EPSG:3857 (Web Mercator)
bike_lanes = bike_lanes.to_crs(epsg=3857)
walkable_ways = walkable_ways.to_crs(epsg=3857)

# Define your threshold distance in meters
X = 50  # example: 50 meters

# Create a buffer around bike lanes
bike_buffer = bike_lanes.buffer(X)

# Dissolve into one big geometry (union)
bike_union = bike_buffer.unary_union

# Filter walkable ways within X meters of any bike lane
walkable_near_bike = walkable_ways[walkable_ways.geometry.intersects(bike_union)]

# Save the result
walkable_near_bike.to_file("walkable_near_bike.geojson", driver="GeoJSON")

