import geopandas as gpd
import matplotlib.pyplot as plt
import folium
import pandas as pd

# ---- Paths to your shapefiles ----
walk_shp = "data/FullSS_noSquare/roads/ss_walk.shp"
bike_shp = "data/FullSS_noSquare/roads/ss_bike.shp"
drive_shp = "data/FullSS_noSquare/roads/ss_drive.shp"

# ---- Load with GeoPandas ----
gdf_walk = gpd.read_file(walk_shp)
gdf_bike = gpd.read_file(bike_shp)
gdf_ride = gpd.read_file(drive_shp)

# ---- Basic static plot with matplotlib ----
fig, ax = plt.subplots(figsize=(10, 10))
gdf_walk.plot(ax=ax, color="green", linewidth=1, label="Walk")
gdf_bike.plot(ax=ax, color="blue", linewidth=1, label="Bike")
gdf_ride.plot(ax=ax, color="red", linewidth=1, label="Drive")
ax.set_title("Walk / Bike / Drive roads in San Sebastián")
ax.legend()
plt.show()

# ---- Interactive plot with Folium ----

# Compute a centroid to center the map
# Combine all geometries to approximate center
all_geoms = gpd.GeoSeries(
    pd.concat(
        [gdf_walk.geometry, gdf_bike.geometry, gdf_ride.geometry], ignore_index=True
    )
)
centroid = all_geoms.unary_union.centroid
centroid_lat = centroid.y
centroid_lon = centroid.x

m = folium.Map(
    location=[centroid_lat, centroid_lon], zoom_start=13, tiles="cartodbpositron"
)

# Add layers
folium.GeoJson(
    gdf_walk, name="Walk", style_function=lambda x: {"color": "green", "weight": 2}
).add_to(m)
folium.GeoJson(
    gdf_bike, name="Bike", style_function=lambda x: {"color": "blue", "weight": 2}
).add_to(m)
folium.GeoJson(
    gdf_ride, name="Ride", style_function=lambda x: {"color": "red", "weight": 2}
).add_to(m)

folium.LayerControl().add_to(m)

# Save out
m.save("data/FullSS_noSquare/roads/san_sebastian_roads_walk_bike_ride.html")
print("Saved interactive map to san_sebastian_roads_walk_bike_ride.html")
