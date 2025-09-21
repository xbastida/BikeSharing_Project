def plot_layer_from_gpkg(gpkg_path, layer_name, output_html=None, color="#0a84ff"):

    import geopandas as gpd
    import folium

    # Load the layer
    gdf = gpd.read_file(gpkg_path, layer=layer_name)
    gdf = gdf.to_crs(epsg=4326)  # ensure WGS84 for folium
    
    # Compute center
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="cartodbpositron")
    
    # Add the GeoJSON layer
    folium.GeoJson(
        gdf,
        name=layer_name,
        style_function=lambda x: {"color": color, "weight": 2}
    ).add_to(m)
    
    # Add controls
    folium.LayerControl().add_to(m)
    
    # Save if requested
    m.save(output_html)
    print(f"✅ Saved {output_html}")
    return m