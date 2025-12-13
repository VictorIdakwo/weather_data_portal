"""
Polygon Sampling Utilities

This module provides functions to generate sampling points within polygons
for weather data extraction. Instead of using only the centroid, it creates
a grid of points within the polygon based on the desired spatial resolution.
"""

import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPolygon
from typing import List, Tuple, Dict
import math


def calculate_optimal_grid_spacing(polygon_area_km2: float, min_points: int = 4, max_points: int = 100) -> float:
    """
    Calculate optimal grid spacing based on polygon area.
    
    Args:
        polygon_area_km2: Area of polygon in square kilometers
        min_points: Minimum number of sampling points
        max_points: Maximum number of sampling points
    
    Returns:
        Grid spacing in degrees (approximately)
    """
    # Target: ~1 point per 500 km² for large areas, more for small areas
    if polygon_area_km2 < 100:  # Small area (< 100 km²)
        target_points = min(max_points, max(min_points, int(polygon_area_km2 / 10)))
    elif polygon_area_km2 < 1000:  # Medium area (100-1000 km²)
        target_points = min(max_points, max(min_points, int(polygon_area_km2 / 50)))
    else:  # Large area (> 1000 km²)
        target_points = min(max_points, max(min_points, int(polygon_area_km2 / 500)))
    
    # Calculate grid spacing (1 degree ≈ 111 km at equator)
    points_per_side = math.sqrt(target_points)
    area_per_point = polygon_area_km2 / target_points
    spacing_km = math.sqrt(area_per_point)
    spacing_degrees = spacing_km / 111.0  # Approximate conversion
    
    # Ensure minimum spacing of 0.05 degrees (~5.5 km)
    spacing_degrees = max(0.05, spacing_degrees)
    
    return spacing_degrees


def generate_grid_points_in_polygon(
    geometry,
    grid_spacing_degrees: float = None,
    include_centroid: bool = True
) -> List[Tuple[float, float]]:
    """
    Generate a grid of points within a polygon.
    
    Args:
        geometry: Shapely Polygon or MultiPolygon
        grid_spacing_degrees: Spacing between grid points in degrees (auto-calculated if None)
        include_centroid: Whether to always include the centroid
    
    Returns:
        List of (latitude, longitude) tuples
    """
    points = []
    
    # Handle MultiPolygon
    if isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            points.extend(generate_grid_points_in_polygon(poly, grid_spacing_degrees, False))
        if include_centroid:
            centroid = geometry.centroid
            points.append((centroid.y, centroid.x))
        return points
    
    # Get polygon bounds
    minx, miny, maxx, maxy = geometry.bounds
    
    # Calculate area in km² (approximate)
    # 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 km * cos(latitude)
    center_lat = (miny + maxy) / 2
    width_km = (maxx - minx) * 111 * math.cos(math.radians(center_lat))
    height_km = (maxy - miny) * 111
    area_km2 = width_km * height_km * 0.7  # Approximate factor for irregular shapes
    
    # Auto-calculate grid spacing if not provided
    if grid_spacing_degrees is None:
        grid_spacing_degrees = calculate_optimal_grid_spacing(area_km2)
    
    # Generate grid points
    lat_points = np.arange(miny, maxy, grid_spacing_degrees)
    lon_points = np.arange(minx, maxx, grid_spacing_degrees)
    
    # Check which points fall within the polygon
    for lat in lat_points:
        for lon in lon_points:
            point = Point(lon, lat)
            if geometry.contains(point):
                points.append((lat, lon))
    
    # Always include centroid if requested
    if include_centroid:
        centroid = geometry.centroid
        centroid_point = (centroid.y, centroid.x)
        if centroid_point not in points:
            points.append(centroid_point)
    
    # If no points found (very small polygon), use centroid
    if not points:
        centroid = geometry.centroid
        points.append((centroid.y, centroid.x))
    
    return points


def sample_polygon_locations(
    gdf: gpd.GeoDataFrame,
    grid_spacing_degrees: float = None,
    include_centroid: bool = True
) -> List[Dict]:
    """
    Sample multiple points within each polygon in a GeoDataFrame.
    
    Args:
        gdf: GeoDataFrame with polygon geometries
        grid_spacing_degrees: Spacing between grid points (auto-calculated if None)
        include_centroid: Whether to include centroid in sampling
    
    Returns:
        List of location dictionaries with lat, lon, name, and parent info
    """
    all_locations = []
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        geom_type = geom.geom_type
        
        # Get name
        name = row.get('name', row.get('NAME', f'Location_{idx}'))
        
        if geom_type in ['Polygon', 'MultiPolygon']:
            # Generate grid points within polygon
            grid_points = generate_grid_points_in_polygon(
                geom, 
                grid_spacing_degrees,
                include_centroid
            )
            
            # Create location dict for each point
            for point_idx, (lat, lon) in enumerate(grid_points):
                location = {
                    "name": f"{name}_point_{point_idx + 1}",
                    "parent_name": name,
                    "lat": lat,
                    "lon": lon,
                    "geometry_type": "SamplingPoint",
                    "parent_geometry_type": geom_type,
                    "id": f"{idx}_{point_idx}",
                    "parent_id": idx,
                    "is_sampling_point": True,
                }
                
                # Add parent attributes
                for col in gdf.columns:
                    if col not in ['geometry', 'name', 'NAME']:
                        location[f"parent_{col}"] = row[col]
                
                all_locations.append(location)
        
        elif geom_type == 'Point':
            # For points, use directly
            location = {
                "name": name,
                "parent_name": name,
                "lat": geom.y,
                "lon": geom.x,
                "geometry_type": "Point",
                "parent_geometry_type": "Point",
                "id": idx,
                "parent_id": idx,
                "is_sampling_point": False,
            }
            
            # Add all attributes
            for col in gdf.columns:
                if col not in ['geometry', 'name', 'NAME']:
                    location[col] = row[col]
            
            all_locations.append(location)
    
    return all_locations


def get_sampling_summary(locations: List[Dict]) -> Dict:
    """
    Get summary statistics about sampling points.
    
    Args:
        locations: List of location dictionaries
    
    Returns:
        Dictionary with summary statistics
    """
    total_points = len(locations)
    sampling_points = sum(1 for loc in locations if loc.get('is_sampling_point', False))
    direct_points = total_points - sampling_points
    
    # Count unique parent polygons
    parent_ids = set(loc.get('parent_id') for loc in locations if loc.get('is_sampling_point', False))
    num_polygons = len(parent_ids)
    
    avg_points_per_polygon = sampling_points / num_polygons if num_polygons > 0 else 0
    
    return {
        "total_points": total_points,
        "sampling_points": sampling_points,
        "direct_points": direct_points,
        "num_polygons": num_polygons,
        "avg_points_per_polygon": avg_points_per_polygon,
    }
