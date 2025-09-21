import osmnx as ox
import geopandas as gpd
import networkx as nx
import numpy as np
import folium

def distances_to_bikelanes(bike_gpkg, points_gpkg,
                           bike_layer="bike", points_layer="points",
                           output_html="map.html"):
    """
    Compute network distances from points to the nearest bike lane,
    using OSMnx's walking network for Donostia-San Sebastián,
    and generate an interactive Folium map.
    """

    # 1. Load data in metric CRS (UTM 30N)
    gdf_bike = gpd.read_file(bike_gpkg, layer=bike_layer).to_crs(epsg=25830)
    gdf_points = gpd.read_file(points_gpkg, layer=points_layer).to_crs(epsg=25830)

    gdf_points = gdf_points[~gdf_points.geometry.is_empty & gdf_points.geometry.notna()].copy()
    import numpy as np

    gdf_points = gdf_points[
        gdf_points.geometry.notnull()
        & ~gdf_points.geometry.is_empty
        & np.isfinite(gdf_points.geometry.x)
        & np.isfinite(gdf_points.geometry.y)
    ].copy()
    # 2. Download walk network in EPSG:25830
    place = "Donostia-San Sebastián, Gipuzkoa, Spain"
    G = ox.graph_from_place(place, network_type="walk")
    G = ox.project_graph(G, to_crs="EPSG:25830")

    # 3. Map points → nearest graph nodes (vectorized)
    point_nodes = ox.distance.nearest_nodes(
        G,
        gdf_points.geometry.x.values,
        gdf_points.geometry.y.values,
    )

    # 4. Gather bike-lane vertices → nearest graph nodes (vectorized)
    exploded = gdf_bike.explode(index_parts=False)
    coords_list = [np.array(geom.coords) for geom in exploded.geometry
                   if geom is not None and not geom.is_empty]
    if not coords_list:
        raise ValueError("No coordinate vertices found in bike lane geometries.")
    bike_coords = np.vstack(coords_list)
    bike_nodes = ox.distance.nearest_nodes(G, bike_coords[:, 0], bike_coords[:, 1])
    bike_nodes = np.unique(bike_nodes).tolist()  # list of ints

    # 5. Multi-source Dijkstra → distances and paths
    dist_dict, path_dict = nx.multi_source_dijkstra(G, sources=bike_nodes, weight="length")

    # 6. Distances for each point node
    gdf_points["dist_to_bike_m"] = [dist_dict.get(n, float("nan")) for n in point_nodes]

    # 7. Prepare data for Folium (convert to WGS84)
    gdf_bike_ll = gdf_bike.to_crs(epsg=4326)
    gdf_points_ll = gdf_points.to_crs(epsg=4326)
    G_ll = ox.project_graph(G, to_crs="EPSG:4326")

    # Center map on points or bike lanes
    if not gdf_points_ll.empty:
        center_lat = float(gdf_points_ll.geometry.y.mean())
        center_lon = float(gdf_points_ll.geometry.x.mean())
    else:
        u = gdf_bike_ll.geometry.unary_union
        center_lat = float(u.centroid.y)
        center_lon = float(u.centroid.x)

    m = folium.Map(location=[center_lat, center_lon],
                   zoom_start=13, tiles="cartodbpositron")

    # 8. Draw bike lanes
    folium.GeoJson(
        gdf_bike_ll.__geo_interface__,
        name="Bike lanes",
        style_function=lambda _: {"color": "#1f78b4", "weight": 3, "opacity": 0.8},
    ).add_to(m)

    # 9. Draw points and paths
    for node, row in zip(point_nodes, gdf_points_ll.itertuples()):
        dist_m = dist_dict.get(node)

        #  Safely get station name
        station_name = getattr(row, "Nombre", "Unknown Station")

        #  Build text
        if dist_m is not None:
            text = f"{station_name}<br>Distance to nearest bikelane = {dist_m:.1f} m"
        else:
            text = f"{station_name}<br>No path to bike lane"
        folium.CircleMarker(
            location=(row.geometry.y, row.geometry.x),
            radius=5,
            color="#33a02c",
            fill=True,
            fill_color="#33a02c",
            fill_opacity=0.9,
            popup=text,      # click shows info
            tooltip=text,    # hover shows info
        ).add_to(m)


        # Path line
        path_nodes = path_dict.get(node)
        if path_nodes:
            coords = [(G_ll.nodes[n]["y"], G_ll.nodes[n]["x"]) for n in path_nodes[::-1]]
            folium.PolyLine(
                locations=coords,
                color="#e31a1c",
                weight=3,
                opacity=0.7,
            ).add_to(m)

    # 10. Save map
    folium.LayerControl().add_to(m)
    m.save(output_html)

    return gdf_points


# Example usage
# bike_gpkg = 'D:/BikeSharing_Project/data/geopackages/bike_edges.gpkg'
# points_gpkg = 'D:/BikeSharing_Project/random_points_sansebastian.gpkg'

# result = distances_to_bikelanes(bike_gpkg, points_gpkg)
# print(result[["dist_to_bike_m"]].head())