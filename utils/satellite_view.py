"""
Google Earth Engine Satellite Imagery Integration

This module provides real satellite imagery visualization using Google Earth Engine
and displays it in an interactive map with location markers.
"""

import folium
from folium import plugins
import streamlit as st
from typing import List, Tuple, Optional, Union
import numpy as np
import geopandas as gpd
import json


def create_satellite_map_from_geodataframe(
    gdf: gpd.GeoDataFrame,
    zoom_start: Optional[int] = None,
    height: int = 600
) -> folium.Map:
    """
    Create an interactive map with satellite imagery from GeoDataFrame.
    Displays actual polygons for polygon geometries and points for point geometries.
    
    Args:
        gdf: GeoDataFrame with geometries
        zoom_start: Initial zoom level (auto-calculated if None)
        height: Height of the map in pixels
    
    Returns:
        Folium Map object with satellite imagery
    """
    
    if gdf is None or len(gdf) == 0:
        # Default to Africa view
        center_lat, center_lon = 0.0, 20.0
        zoom_start = 3
    else:
        # Calculate center from bounds
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Calculate zoom level based on spread
        if zoom_start is None:
            lat_range = bounds[3] - bounds[1]
            lon_range = bounds[2] - bounds[0]
            max_range = max(lat_range, lon_range)
            
            if max_range < 1:
                zoom_start = 10
            elif max_range < 5:
                zoom_start = 8
            elif max_range < 15:
                zoom_start = 6
            elif max_range < 30:
                zoom_start = 5
            else:
                zoom_start = 4
    
    # Create map with satellite imagery
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles=None,
        control_scale=True,
        prefer_canvas=True
    )
    
    # Add Google Satellite imagery
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='© Google',
        name='Satellite',
        overlay=False,
        control=True,
        show=True
    ).add_to(m)
    
    # Add Google Hybrid (Satellite + Labels)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='© Google',
        name='Satellite + Labels',
        overlay=False,
        control=True,
        show=False
    ).add_to(m)
    
    # Add OpenStreetMap as alternative
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='Street Map',
        overlay=False,
        control=True,
        show=False
    ).add_to(m)
    
    # Add geometries from GeoDataFrame
    if gdf is not None and len(gdf) > 0:
        # Import sampling function to get sampling points
        from .polygon_sampler import sample_polygon_locations
        
        # Get sampling points for display
        sampling_locations = sample_polygon_locations(gdf, grid_spacing_degrees=None, include_centroid=True)
        
        for idx, row in gdf.iterrows():
            geom = row.geometry
            geom_type = geom.geom_type
            
            # Get name
            name = row.get('name', row.get('NAME', f'Location_{idx}'))
            
            # Create popup content
            popup_html = f"""
            <div style='font-family: Arial; min-width: 250px;'>
                <h4 style='margin: 0; color: #2c3e50;'>📍 {name}</h4>
                <hr style='margin: 5px 0;'>
                <p style='margin: 5px 0;'><b>Type:</b> {geom_type}</p>
            """
            
            # Add centroid coordinates
            if geom_type in ['Polygon', 'MultiPolygon']:
                centroid = geom.centroid
                popup_html += f"<p style='margin: 5px 0;'><b>Centroid:</b> {centroid.y:.4f}°, {centroid.x:.4f}°</p>"
                # Count sampling points for this polygon
                polygon_sampling_points = [loc for loc in sampling_locations if loc.get('parent_id') == idx]
                popup_html += f"<p style='margin: 5px 0;'><b>Sampling Points:</b> {len(polygon_sampling_points)}</p>"
            elif geom_type == 'Point':
                popup_html += f"<p style='margin: 5px 0;'><b>Coordinates:</b> {geom.y:.4f}°, {geom.x:.4f}°</p>"
            
            # Add other attributes
            for col in gdf.columns:
                if col not in ['geometry', 'name', 'NAME']:
                    value = row[col]
                    if value is not None and str(value) != 'nan':
                        popup_html += f"<p style='margin: 5px 0;'><b>{col}:</b> {value}</p>"
            
            popup_html += "</div>"
            
            # Add geometry based on type
            if geom_type in ['Polygon', 'MultiPolygon']:
                # Add polygon
                folium.GeoJson(
                    geom.__geo_interface__,
                    style_function=lambda x: {
                        'fillColor': '#ff7800',
                        'color': '#ff0000',
                        'weight': 2,
                        'fillOpacity': 0.3
                    },
                    highlight_function=lambda x: {
                        'fillColor': '#ffff00',
                        'color': '#ff0000',
                        'weight': 3,
                        'fillOpacity': 0.5
                    },
                    tooltip=name,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)
                
                # Add centroid marker
                centroid = geom.centroid
                folium.CircleMarker(
                    location=[centroid.y, centroid.x],
                    radius=5,
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.8,
                    popup=folium.Popup(f"<b>Centroid of {name}</b>", max_width=200),
                    tooltip=f"Centroid: {name}"
                ).add_to(m)
                
            elif geom_type == 'Point':
                # Add point marker
                folium.Marker(
                    location=[geom.y, geom.x],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=name,
                    icon=folium.Icon(color='red', icon='map-pin', prefix='fa')
                ).add_to(m)
                
                # Add circle around point
                folium.Circle(
                    location=[geom.y, geom.x],
                    radius=5000,  # 5km radius
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.1,
                    weight=2
                ).add_to(m)
        
        # Add sampling points as small markers (for polygons only)
        for loc in sampling_locations:
            if loc.get('is_sampling_point', False):
                # Small blue circle for sampling points
                folium.CircleMarker(
                    location=[loc['lat'], loc['lon']],
                    radius=3,
                    color='#0066ff',
                    fill=True,
                    fillColor='#0066ff',
                    fillOpacity=0.7,
                    weight=1,
                    popup=folium.Popup(
                        f"<b>Sampling Point</b><br>{loc['parent_name']}<br>Lat: {loc['lat']:.4f}°<br>Lon: {loc['lon']:.4f}°",
                        max_width=200
                    ),
                    tooltip=f"Data point: {loc['parent_name']}"
                ).add_to(m)
    
    # Add layer control
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen(
        position='topleft',
        title='Fullscreen',
        title_cancel='Exit fullscreen',
        force_separate_button=True
    ).add_to(m)
    
    # Add measure control
    plugins.MeasureControl(
        position='topleft',
        primary_length_unit='kilometers',
        secondary_length_unit='miles',
        primary_area_unit='sqkilometers',
        secondary_area_unit='acres'
    ).add_to(m)
    
    # Add minimap with proper tile layer
    minimap_tile = folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='© Google'
    )
    minimap = plugins.MiniMap(
        tile_layer=minimap_tile,
        position='bottomright',
        width=150,
        height=150,
        collapsed_width=25,
        collapsed_height=25,
        zoom_level_offset=-5
    )
    m.add_child(minimap)
    
    # Add mouse position
    plugins.MousePosition(
        position='bottomleft',
        separator=' | ',
        prefix='Coordinates:',
        lat_formatter="function(num) {return L.Util.formatNum(num, 4) + '° N';}",
        lng_formatter="function(num) {return L.Util.formatNum(num, 4) + '° E';}"
    ).add_to(m)
    
    # Fit bounds to show all geometries
    if gdf is not None and len(gdf) > 0:
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], padding=[50, 50])
    
    return m


def create_satellite_map(
    locations: List[Tuple[float, float, str]],
    zoom_start: Optional[int] = None,
    height: int = 600,
    gdf: Optional[gpd.GeoDataFrame] = None
) -> folium.Map:
    """
    Create an interactive map with satellite imagery and location markers.
    If GeoDataFrame is provided, uses it to display actual geometries.
    
    Args:
        locations: List of tuples (latitude, longitude, location_name)
        zoom_start: Initial zoom level (auto-calculated if None)
        height: Height of the map in pixels
        gdf: Optional GeoDataFrame with actual geometries
    
    Returns:
        Folium Map object with satellite imagery
    """
    
    # If GeoDataFrame is provided, use the enhanced function
    if gdf is not None and len(gdf) > 0:
        return create_satellite_map_from_geodataframe(gdf, zoom_start, height)
    
    if not locations:
        # Default to Africa view
        center_lat, center_lon = 0.0, 20.0
        zoom_start = 3
    else:
        # Calculate center and zoom based on locations
        lats = [loc[0] for loc in locations]
        lons = [loc[1] for loc in locations]
        
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        
        # Calculate zoom level based on spread
        if zoom_start is None:
            lat_range = max(lats) - min(lats)
            lon_range = max(lons) - min(lons)
            max_range = max(lat_range, lon_range)
            
            if max_range < 1:
                zoom_start = 10
            elif max_range < 5:
                zoom_start = 8
            elif max_range < 15:
                zoom_start = 6
            elif max_range < 30:
                zoom_start = 5
            else:
                zoom_start = 4
    
    # Create map with satellite imagery
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles=None,  # We'll add custom tiles
        control_scale=True,
        prefer_canvas=True
    )
    
    # Add Google Satellite imagery
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='© Google',
        name='Satellite',
        overlay=False,
        control=True,
        show=True
    ).add_to(m)
    
    # Add Google Hybrid (Satellite + Labels)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='© Google',
        name='Satellite + Labels',
        overlay=False,
        control=True,
        show=False
    ).add_to(m)
    
    # Add OpenStreetMap as alternative
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='Street Map',
        overlay=False,
        control=True,
        show=False
    ).add_to(m)
    
    # Add location markers
    if locations:
        # Create a feature group for markers
        marker_cluster = plugins.MarkerCluster(name='Locations').add_to(m)
        
        for lat, lon, name in locations:
            # Create custom icon
            icon = folium.Icon(
                color='red',
                icon='map-pin',
                prefix='fa'
            )
            
            # Add marker with popup
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(
                    f"""
                    <div style='font-family: Arial; min-width: 200px;'>
                        <h4 style='margin: 0; color: #2c3e50;'>📍 {name}</h4>
                        <hr style='margin: 5px 0;'>
                        <p style='margin: 5px 0;'><b>Latitude:</b> {lat:.4f}°</p>
                        <p style='margin: 5px 0;'><b>Longitude:</b> {lon:.4f}°</p>
                    </div>
                    """,
                    max_width=300
                ),
                tooltip=name,
                icon=icon
            ).add_to(marker_cluster)
            
            # Add a circle to highlight the area
            folium.Circle(
                location=[lat, lon],
                radius=5000,  # 5km radius
                color='red',
                fill=True,
                fillColor='red',
                fillOpacity=0.1,
                weight=2,
                popup=f"{name} - 5km radius"
            ).add_to(m)
    
    # Add layer control
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen(
        position='topleft',
        title='Fullscreen',
        title_cancel='Exit fullscreen',
        force_separate_button=True
    ).add_to(m)
    
    # Add measure control
    plugins.MeasureControl(
        position='topleft',
        primary_length_unit='kilometers',
        secondary_length_unit='miles',
        primary_area_unit='sqkilometers',
        secondary_area_unit='acres'
    ).add_to(m)
    
    # Add minimap with proper tile layer
    minimap_tile = folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='© Google'
    )
    minimap = plugins.MiniMap(
        tile_layer=minimap_tile,
        position='bottomright',
        width=150,
        height=150,
        collapsed_width=25,
        collapsed_height=25,
        zoom_level_offset=-5
    )
    m.add_child(minimap)
    
    # Add mouse position
    plugins.MousePosition(
        position='bottomleft',
        separator=' | ',
        prefix='Coordinates:',
        lat_formatter="function(num) {return L.Util.formatNum(num, 4) + '° N';}",
        lng_formatter="function(num) {return L.Util.formatNum(num, 4) + '° E';}"
    ).add_to(m)
    
    # Fit bounds to show all markers
    if locations and len(locations) > 1:
        bounds = [[lat, lon] for lat, lon, _ in locations]
        m.fit_bounds(bounds, padding=[50, 50])
    
    return m


def create_3d_satellite_view(
    locations: List[Tuple[float, float, str]],
    height: int = 600
) -> str:
    """
    Create an HTML embed for Google Earth 3D view.
    
    Args:
        locations: List of tuples (latitude, longitude, location_name)
        height: Height of the view in pixels
    
    Returns:
        HTML string for embedding
    """
    
    if not locations:
        center_lat, center_lon = 0.0, 20.0
    else:
        lats = [loc[0] for loc in locations]
        lons = [loc[1] for loc in locations]
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
    
    # Create Google Earth embed URL
    # Note: This uses Google Maps 3D view as Google Earth API is deprecated
    html = f"""
    <iframe
        width="100%"
        height="{height}px"
        frameborder="0"
        style="border:0; border-radius: 8px;"
        referrerpolicy="no-referrer-when-downgrade"
        src="https://www.google.com/maps/embed/v1/view?key=YOUR_API_KEY&center={center_lat},{center_lon}&zoom=12&maptype=satellite"
        allowfullscreen>
    </iframe>
    """
    
    return html
