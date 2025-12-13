"""
3D Earth Globe Visualization Module

This module provides an interactive 3D rotating earth globe that zooms to selected locations.
Uses Plotly for 3D visualization with smooth animations.
"""

import plotly.graph_objects as go
import numpy as np
from typing import List, Tuple, Optional


def create_earth_globe(
    locations: List[Tuple[float, float, str]],
    zoom_to_location: Optional[int] = None,
    show_all_markers: bool = True,
    height: int = 600
) -> go.Figure:
    """
    Create an interactive 3D earth globe with location markers and satellite-like imagery.
    
    Args:
        locations: List of tuples (latitude, longitude, location_name)
        zoom_to_location: Index of location to zoom to (None for global view)
        show_all_markers: Whether to show all location markers
        height: Height of the visualization in pixels
    
    Returns:
        Plotly Figure object
    """
    
    # Create the base earth sphere
    fig = go.Figure()
    
    # Add earth surface with enhanced satellite-like texture
    # Create a high-resolution sphere mesh
    theta = np.linspace(0, 2 * np.pi, 150)
    phi = np.linspace(0, np.pi, 150)
    
    # Earth sphere coordinates
    x_sphere = np.outer(np.cos(theta), np.sin(phi))
    y_sphere = np.outer(np.sin(theta), np.sin(phi))
    z_sphere = np.outer(np.ones(150), np.cos(phi))
    
    # Create realistic earth texture using elevation-based coloring
    # Simulate topography with latitude-based variations
    elevation = np.zeros((150, 150))
    for i in range(150):
        for j in range(150):
            lat = (phi[j] - np.pi/2) * 180 / np.pi
            lon = theta[i] * 180 / np.pi
            # Simulate land/ocean with noise-like pattern
            elevation[i, j] = (
                np.sin(lat/10) * np.cos(lon/15) + 
                np.sin(lat/5 + lon/8) * 0.5 +
                np.cos(lat/3) * 0.3
            )
    
    # Add earth surface with satellite-like colors
    fig.add_trace(go.Surface(
        x=x_sphere,
        y=y_sphere,
        z=z_sphere,
        surfacecolor=elevation,
        colorscale=[
            [0, '#0d1b2a'],      # Deep ocean
            [0.25, '#1b3a52'],   # Ocean blue
            [0.45, '#2b5a7a'],   # Shallow water
            [0.5, '#4a7c59'],    # Coastal green
            [0.55, '#5a8c40'],   # Lowland green
            [0.65, '#7a9c50'],   # Vegetation
            [0.75, '#9aac60'],   # Grassland
            [0.85, '#8b7355'],   # Mountains
            [0.95, '#b8a890'],   # High peaks
            [1, '#f0f0f0']       # Snow caps
        ],
        showscale=False,
        opacity=0.95,
        name='Earth',
        hoverinfo='skip',
        lighting=dict(
            ambient=0.4,
            diffuse=0.8,
            specular=0.3,
            roughness=0.5,
            fresnel=0.2
        ),
        lightposition=dict(x=1000, y=1000, z=1000)
    ))
    
    if locations and show_all_markers:
        # Convert lat/lon to 3D coordinates on sphere
        lats = [loc[0] for loc in locations]
        lons = [loc[1] for loc in locations]
        names = [loc[2] for loc in locations]
        
        # Convert to radians
        lat_rad = np.radians(lats)
        lon_rad = np.radians(lons)
        
        # Convert to 3D Cartesian coordinates (sphere radius = 1)
        radius = 1.02  # Slightly above surface
        x_markers = radius * np.cos(lat_rad) * np.cos(lon_rad)
        y_markers = radius * np.cos(lat_rad) * np.sin(lon_rad)
        z_markers = radius * np.sin(lat_rad)
        
        # Add location markers
        fig.add_trace(go.Scatter3d(
            x=x_markers,
            y=y_markers,
            z=z_markers,
            mode='markers+text',
            marker=dict(
                size=8,
                color='red',
                symbol='circle',
                line=dict(color='white', width=2)
            ),
            text=names,
            textposition='top center',
            textfont=dict(size=10, color='white'),
            hovertext=[f"<b>{name}</b><br>Lat: {lat:.2f}°<br>Lon: {lon:.2f}°" 
                      for name, lat, lon in zip(names, lats, lons)],
            hoverinfo='text',
            name='Locations'
        ))
        
        # If zooming to a specific location, add a highlighted marker
        if zoom_to_location is not None and 0 <= zoom_to_location < len(locations):
            zoom_lat, zoom_lon, zoom_name = locations[zoom_to_location]
            zoom_lat_rad = np.radians(zoom_lat)
            zoom_lon_rad = np.radians(zoom_lon)
            
            x_zoom = 1.05 * np.cos(zoom_lat_rad) * np.cos(zoom_lon_rad)
            y_zoom = 1.05 * np.cos(zoom_lat_rad) * np.sin(zoom_lon_rad)
            z_zoom = 1.05 * np.sin(zoom_lat_rad)
            
            fig.add_trace(go.Scatter3d(
                x=[x_zoom],
                y=[y_zoom],
                z=[z_zoom],
                mode='markers',
                marker=dict(
                    size=15,
                    color='yellow',
                    symbol='diamond',
                    line=dict(color='orange', width=3)
                ),
                hovertext=f"<b>SELECTED: {zoom_name}</b><br>Lat: {zoom_lat:.2f}°<br>Lon: {zoom_lon:.2f}°",
                hoverinfo='text',
                name='Selected Location',
                showlegend=False
            ))
    
    # Set camera position
    if zoom_to_location is not None and locations and 0 <= zoom_to_location < len(locations):
        # Zoom to specific location
        zoom_lat, zoom_lon, _ = locations[zoom_to_location]
        zoom_lat_rad = np.radians(zoom_lat)
        zoom_lon_rad = np.radians(zoom_lon)
        
        # Camera position (looking at the location from a distance)
        camera_distance = 2.5
        camera_x = camera_distance * np.cos(zoom_lat_rad) * np.cos(zoom_lon_rad)
        camera_y = camera_distance * np.cos(zoom_lat_rad) * np.sin(zoom_lon_rad)
        camera_z = camera_distance * np.sin(zoom_lat_rad)
        
        camera = dict(
            eye=dict(x=camera_x, y=camera_y, z=camera_z),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        )
    else:
        # Default view showing Africa
        camera = dict(
            eye=dict(x=1.5, y=1.5, z=1.0),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        )
    
    # Update layout with enhanced styling
    fig.update_layout(
        title=dict(
            text="🌍 Satellite Earth View - Selected Locations",
            font=dict(size=18, color='#e0e0e0', family='Arial'),
            x=0.5,
            xanchor='center'
        ),
        scene=dict(
            xaxis=dict(visible=False, range=[-1.5, 1.5]),
            yaxis=dict(visible=False, range=[-1.5, 1.5]),
            zaxis=dict(visible=False, range=[-1.5, 1.5]),
            aspectmode='cube',
            camera=camera,
            bgcolor='#000000'
        ),
        paper_bgcolor='#0f0f0f',
        plot_bgcolor='#0f0f0f',
        height=height,
        showlegend=False,
        hovermode='closest',
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig


def create_animated_earth_globe(
    locations: List[Tuple[float, float, str]],
    rotation_frames: int = 36,
    height: int = 600
) -> go.Figure:
    """
    Create an animated rotating earth globe with location markers.
    
    Args:
        locations: List of tuples (latitude, longitude, location_name)
        rotation_frames: Number of frames for full rotation
        height: Height of the visualization in pixels
    
    Returns:
        Plotly Figure object with animation
    """
    
    # Create base figure
    fig = create_earth_globe(locations, zoom_to_location=None, height=height)
    
    # Create frames for rotation animation
    frames = []
    angles = np.linspace(0, 360, rotation_frames)
    
    for angle in angles:
        angle_rad = np.radians(angle)
        camera_x = 2.5 * np.cos(angle_rad)
        camera_y = 2.5 * np.sin(angle_rad)
        camera_z = 1.0
        
        frame = go.Frame(
            layout=dict(
                scene=dict(
                    camera=dict(
                        eye=dict(x=camera_x, y=camera_y, z=camera_z),
                        center=dict(x=0, y=0, z=0),
                        up=dict(x=0, y=0, z=1)
                    )
                )
            ),
            name=str(angle)
        )
        frames.append(frame)
    
    fig.frames = frames
    
    # Add play/pause buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type='buttons',
                showactive=False,
                buttons=[
                    dict(
                        label='▶ Rotate',
                        method='animate',
                        args=[None, dict(
                            frame=dict(duration=100, redraw=True),
                            fromcurrent=True,
                            mode='immediate',
                            transition=dict(duration=0)
                        )]
                    ),
                    dict(
                        label='⏸ Pause',
                        method='animate',
                        args=[[None], dict(
                            frame=dict(duration=0, redraw=False),
                            mode='immediate',
                            transition=dict(duration=0)
                        )]
                    )
                ],
                x=0.1,
                y=0.95,
                xanchor='left',
                yanchor='top',
                bgcolor='rgba(255,255,255,0.2)',
                font=dict(color='white')
            )
        ]
    )
    
    return fig


def create_location_zoom_globe(
    locations: List[Tuple[float, float, str]],
    height: int = 600
) -> go.Figure:
    """
    Create an earth globe that focuses on the centroid of all selected locations.
    
    Args:
        locations: List of tuples (latitude, longitude, location_name)
        height: Height of the visualization in pixels
    
    Returns:
        Plotly Figure object
    """
    
    if not locations:
        return create_earth_globe([], height=height)
    
    # Calculate centroid of all locations
    lats = [loc[0] for loc in locations]
    lons = [loc[1] for loc in locations]
    
    center_lat = np.mean(lats)
    center_lon = np.mean(lons)
    
    # Calculate zoom level based on spread of locations
    lat_range = max(lats) - min(lats)
    lon_range = max(lons) - min(lons)
    max_range = max(lat_range, lon_range)
    
    # Adjust camera distance based on spread
    if max_range < 5:
        camera_distance = 1.8
    elif max_range < 15:
        camera_distance = 2.2
    elif max_range < 30:
        camera_distance = 2.8
    else:
        camera_distance = 3.5
    
    # Create figure
    fig = create_earth_globe(locations, show_all_markers=True, height=height)
    
    # Set camera to look at centroid
    center_lat_rad = np.radians(center_lat)
    center_lon_rad = np.radians(center_lon)
    
    camera_x = camera_distance * np.cos(center_lat_rad) * np.cos(center_lon_rad)
    camera_y = camera_distance * np.cos(center_lat_rad) * np.sin(center_lon_rad)
    camera_z = camera_distance * np.sin(center_lat_rad)
    
    fig.update_layout(
        scene=dict(
            camera=dict(
                eye=dict(x=camera_x, y=camera_y, z=camera_z),
                center=dict(x=0, y=0, z=0),
                up=dict(x=0, y=0, z=1)
            )
        ),
        title=dict(
            text=f"🌍 Earth Globe - {len(locations)} Location(s) Selected",
            font=dict(size=20, color='white')
        )
    )
    
    return fig
