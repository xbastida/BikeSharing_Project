import sys
from pathlib import Path
import geopandas as gpd
import folium
import numpy as np
import osmnx as ox
import networkx as nx
from typing import Union

# Add the project root to the path to enable relative imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def nearest_edges(
    geometries: Union[gpd.GeoDataFrame, gpd.GeoSeries], G, max_dist: float = None
):
    """Efficiently find nearest network edges to geometries using spatial indexing."""
    edges = ox.graph_to_gdfs(G, nodes=False)
    
    # Handle both GeoDataFrame and GeoSeries
    if isinstance(geometries, gpd.GeoDataFrame):
        geom = geometries.geometry.to_crs(edges.crs).copy()
    else:
        geom = geometries.to_crs(edges.crs).copy()
    
    # Use a simpler approach with direct assignment
    edge_ids = []
    for i, geometry in enumerate(geom):
        if geometry is not None and not geometry.is_empty:
            # Find nearest edge using spatial index
            idx_geom, idx_edges = edges.sindex.nearest(
                [geometry], max_distance=max_dist, return_all=False
            )
            if len(idx_edges) > 0:
                edge_ids.append(edges.index[idx_edges[0]])
            else:
                edge_ids.append(None)
        else:
            edge_ids.append(None)
    
    return edge_ids

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

print(f"Using efficient spatial indexing for distance calculation...")

# Download walking network for Donostia-San Sebastián
print("Downloading walking network...")
place = "Donostia-San Sebastián, Gipuzkoa, Spain"
G = ox.graph_from_place(place, network_type="walk")
G = ox.project_graph(G, to_crs="EPSG:25830")

# Convert graph to GeoDataFrame for efficient spatial operations
edges_gdf = ox.graph_to_gdfs(G, nodes=False)
print(f"Network has {len(edges_gdf)} edges")

# Find nearest edges to bike lanes
print("Finding nearest edges to bike lanes...")
bike_edge_ids = nearest_edges(bike_lanes, G, max_dist=DISTANCE_THRESHOLD)
bike_edge_ids = [eid for eid in bike_edge_ids if eid is not None]
print(f"Found {len(bike_edge_ids)} bike lane edges within network")

# Find nearest edges to walkable ways
print("Finding nearest edges to walkable ways...")
walkable_edge_ids = nearest_edges(walkable_ways, G, max_dist=DISTANCE_THRESHOLD)
walkable_edge_ids = [eid for eid in walkable_edge_ids if eid is not None]
print(f"Found {len(walkable_edge_ids)} walkable way edges within network")

# Calculate network distances efficiently
print("Calculating network distances...")
if bike_edge_ids and walkable_edge_ids:
    # Get unique bike edge nodes
    bike_edge_nodes = set()
    for edge_id in bike_edge_ids:
        if edge_id in G.edges:
            # Handle both (u, v) and (u, v, key) edge formats
            if len(edge_id) == 2:
                u, v = edge_id
            else:
                u, v, key = edge_id
            bike_edge_nodes.add(u)
            bike_edge_nodes.add(v)
    
    # Multi-source Dijkstra from bike edge nodes
    dist_dict, path_dict = nx.multi_source_dijkstra(G, sources=list(bike_edge_nodes), weight="length")
    
    # Find walkable edges within threshold distance
    walkable_edges_near_bike = []
    for edge_id in walkable_edge_ids:
        if edge_id in G.edges:
            # Handle both (u, v) and (u, v, key) edge formats
            if len(edge_id) == 2:
                u, v = edge_id
            else:
                u, v, key = edge_id
            min_dist = min(
                dist_dict.get(u, float('inf')),
                dist_dict.get(v, float('inf'))
            )
            if min_dist <= DISTANCE_THRESHOLD:
                walkable_edges_near_bike.append(edge_id)
    
    print(f"Found {len(walkable_edges_near_bike)} walkable edges within {DISTANCE_THRESHOLD}m of bike lanes")
    
    # Filter walkable ways that have edges within threshold distance
    walkable_near_bike = walkable_ways[
        walkable_ways.index.isin([
            i for i, edge_id in enumerate(walkable_edge_ids) 
            if edge_id in walkable_edges_near_bike
        ])
    ]
    
    print(f"Found {len(walkable_near_bike)} walkable way segments within {DISTANCE_THRESHOLD}m of bike lanes")
else:
    print("No valid edges found for distance calculation!")
    walkable_near_bike = gpd.GeoDataFrame(columns=walkable_ways.columns, crs=walkable_ways.crs)

# Create filtered bike lane archive (only bike lanes that have walkable ways nearby)
print("Creating filtered bike lane archive...")
if not walkable_near_bike.empty and bike_edge_ids:
    # Find bike lane edges that are within threshold distance of walkable edges
    bike_edges_near_walkable = []
    for edge_id in bike_edge_ids:
        if edge_id in G.edges:
            # Handle both (u, v) and (u, v, key) edge formats
            if len(edge_id) == 2:
                u, v = edge_id
            else:
                u, v, key = edge_id
            min_dist = min(
                dist_dict.get(u, float('inf')),
                dist_dict.get(v, float('inf'))
            )
            if min_dist <= DISTANCE_THRESHOLD:
                bike_edges_near_walkable.append(edge_id)
    
    bike_lanes_filtered = bike_lanes[
        bike_lanes.index.isin([
            i for i, edge_id in enumerate(bike_edge_ids) 
            if edge_id in bike_edges_near_walkable
        ])
    ]
else:
    bike_lanes_filtered = gpd.GeoDataFrame(columns=bike_lanes.columns, crs=bike_lanes.crs)

print(f"Filtered bike lanes: {len(bike_lanes_filtered)} segments")

# Save the filtered data
walkable_output = output_dir / f"walkable_within_{DISTANCE_THRESHOLD}m_bikelanes.gpkg"
bike_output = output_dir / f"bikelanes_near_walkable_{DISTANCE_THRESHOLD}m.gpkg"

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
map_output = output_dir / f"walkable_bikelanes_constraint_{DISTANCE_THRESHOLD}m.html"
m.save(str(map_output))

print(f"Interactive map saved to: {map_output}")

# Print summary statistics
print("\n" + "="*60)
print("NETWORK-BASED DISTANCE ANALYSIS SUMMARY")
print("="*60)
print(f"Total bike lane segments: {len(bike_lanes)}")
print(f"Total walkable way segments: {len(walkable_ways)}")
print(f"Bike lane network nodes: {len(bike_nodes) if 'bike_nodes' in locals() else 0}")
print(f"Walkable way network nodes: {len(walkable_nodes) if 'walkable_nodes' in locals() else 0}")
print(f"Walkable nodes within {DISTANCE_THRESHOLD}m of bike lanes: {len(walkable_nodes_near_bike) if 'walkable_nodes_near_bike' in locals() else 0}")
print(f"Walkable segments within {DISTANCE_THRESHOLD}m of bike lanes: {len(walkable_near_bike)}")
print(f"Bike lane segments near walkable routes: {len(bike_lanes_filtered)}")
print(f"Percentage of walkable ways near bike lanes: {len(walkable_near_bike)/len(walkable_ways)*100:.1f}%")
print(f"Percentage of bike lanes near walkable routes: {len(bike_lanes_filtered)/len(bike_lanes)*100:.1f}%")
print("\nNote: Distances calculated along actual walkable network paths, not Euclidean distance")
print("="*60)
