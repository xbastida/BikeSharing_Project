import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx

# Load the GeoJSON
gdf = gpd.read_file("your_polygon.geojson")

# Convert to Web Mercator (required by contextily basemaps)
gdf_webmerc = gdf.to_crs(epsg=3857)

# Plot
ax = gdf_webmerc.plot(edgecolor="red", facecolor="none", linewidth=2, figsize=(8, 8))
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)  # OSM basemap
plt.show()
