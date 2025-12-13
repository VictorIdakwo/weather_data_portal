"""
KML file handling utilities for the Weather Data Portal.
Supports reading KML/KMZ files and extracting location data.
"""

import os
import tempfile
import zipfile
from typing import List, Dict, Tuple
from xml.etree import ElementTree as ET
import geopandas as gpd
from shapely.geometry import Point, Polygon
import pandas as pd
from .polygon_sampler import sample_polygon_locations, get_sampling_summary


def read_kml_file(kml_path: str) -> gpd.GeoDataFrame:
    """
    Read KML/KMZ file and return GeoDataFrame.
    
    Args:
        kml_path: Path to KML or KMZ file
    
    Returns:
        GeoDataFrame with geometries and attributes
    
    Raises:
        ValueError: If file cannot be read or parsed
    """
    try:
        # Handle KMZ files (zipped KML)
        if kml_path.lower().endswith('.kmz'):
            return read_kmz_file(kml_path)
        
        # Handle KML files
        return read_kml_content(kml_path)
        
    except Exception as e:
        raise ValueError(f"Error reading KML file: {str(e)}")


def read_kmz_file(kmz_path: str) -> gpd.GeoDataFrame:
    """
    Read KMZ (zipped KML) file.
    
    Args:
        kmz_path: Path to KMZ file
    
    Returns:
        GeoDataFrame
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract KMZ
        with zipfile.ZipFile(kmz_path, 'r') as kmz:
            kmz.extractall(temp_dir)
        
        # Find KML file in extracted contents
        kml_file = None
        for file in os.listdir(temp_dir):
            if file.lower().endswith('.kml'):
                kml_file = os.path.join(temp_dir, file)
                break
        
        if not kml_file:
            raise ValueError("No KML file found in KMZ archive")
        
        return read_kml_content(kml_file)


def read_kml_content(kml_path: str) -> gpd.GeoDataFrame:
    """
    Read KML file content and parse geometries.
    
    Args:
        kml_path: Path to KML file
    
    Returns:
        GeoDataFrame
    """
    # Try using geopandas first (supports basic KML)
    try:
        gdf = gpd.read_file(kml_path, driver='KML')
        return gdf
    except Exception:
        pass
    
    # Fallback: Manual XML parsing for complex KML
    return parse_kml_xml(kml_path)


def parse_kml_xml(kml_path: str) -> gpd.GeoDataFrame:
    """
    Parse KML XML manually to extract placemarks.
    
    Args:
        kml_path: Path to KML file
    
    Returns:
        GeoDataFrame
    """
    # Parse XML
    tree = ET.parse(kml_path)
    root = tree.getroot()
    
    # Handle KML namespaces
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    if not root.tag.startswith('{'):
        # No namespace
        ns = {'kml': ''}
    
    # Find all Placemarks
    placemarks = []
    
    for placemark in root.findall('.//kml:Placemark', ns) or root.findall('.//Placemark'):
        placemark_data = {}
        
        # Extract name
        name_elem = placemark.find('.//kml:name', ns) or placemark.find('.//name')
        placemark_data['name'] = name_elem.text if name_elem is not None else "Unnamed"
        
        # Extract description
        desc_elem = placemark.find('.//kml:description', ns) or placemark.find('.//description')
        placemark_data['description'] = desc_elem.text if desc_elem is not None else ""
        
        # Extract geometry
        geometry = None
        
        # Try Point
        point = placemark.find('.//kml:Point/kml:coordinates', ns) or placemark.find('.//Point/coordinates')
        if point is not None:
            coords = point.text.strip().split(',')
            if len(coords) >= 2:
                lon, lat = float(coords[0]), float(coords[1])
                geometry = Point(lon, lat)
        
        # Try Polygon if no Point found
        if geometry is None:
            polygon = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', ns) or \
                     placemark.find('.//Polygon/outerBoundaryIs/LinearRing/coordinates')
            if polygon is not None:
                coords_text = polygon.text.strip()
                coord_pairs = []
                for coord in coords_text.split():
                    parts = coord.split(',')
                    if len(parts) >= 2:
                        coord_pairs.append((float(parts[0]), float(parts[1])))
                
                if len(coord_pairs) > 2:
                    geometry = Polygon(coord_pairs)
        
        if geometry:
            placemark_data['geometry'] = geometry
            placemarks.append(placemark_data)
    
    if not placemarks:
        raise ValueError("No valid placemarks found in KML file")
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(placemarks, crs="EPSG:4326")
    return gdf


def extract_locations_from_kml(
    gdf: gpd.GeoDataFrame,
    use_polygon_sampling: bool = True,
    grid_spacing_degrees: float = None
) -> List[Dict]:
    """
    Extract locations from KML GeoDataFrame.
    Similar to shapefile extraction but tailored for KML structure.
    
    Args:
        gdf: GeoDataFrame from KML
        use_polygon_sampling: If True, sample multiple points within polygons
        grid_spacing_degrees: Grid spacing for sampling (auto-calculated if None)
    
    Returns:
        List of dicts with 'name', 'lat', 'lon', 'geometry_type', and other attributes
    """
    
    # Check if we have any polygons
    has_polygons = any(geom.geom_type in ['Polygon', 'MultiPolygon'] for geom in gdf.geometry)
    
    # Use polygon sampling if requested and polygons exist
    if use_polygon_sampling and has_polygons:
        return sample_polygon_locations(gdf, grid_spacing_degrees, include_centroid=True)
    
    # Otherwise, use centroid-based approach (legacy)
    locations = []
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        
        # Determine geometry type and extract location
        if geom.geom_type == "Point":
            lat, lon = geom.y, geom.x
            geom_type = "Point"
        
        elif geom.geom_type in ["Polygon", "MultiPolygon"]:
            centroid = geom.centroid
            lat, lon = centroid.y, centroid.x
            geom_type = "Polygon"
        
        elif geom.geom_type == "MultiPoint":
            # Use first point
            first_point = list(geom.geoms)[0]
            lat, lon = first_point.y, first_point.x
            geom_type = "MultiPoint"
        
        else:
            # Skip unsupported geometry types
            continue
        
        # Create location dict
        location = {
            "name": row.get("name", f"Location_{idx}"),
            "lat": lat,
            "lon": lon,
            "geometry_type": geom_type,
            "id": idx,
        }
        
        # Add description if available
        if "description" in row and pd.notna(row["description"]):
            location["description"] = row["description"]
        
        # Add all other attributes
        for col in gdf.columns:
            if col not in ["geometry", "name", "description"]:
                if pd.notna(row[col]):
                    location[col] = row[col]
        
        locations.append(location)
    
    return locations


def validate_kml_locations(locations: List[Dict]) -> Tuple[bool, str]:
    """
    Validate if KML locations are within reasonable bounds for Africa.
    Uses same validation as shapefiles.
    
    Args:
        locations: List of location dictionaries
    
    Returns:
        (is_valid, error_message)
    """
    # Africa approximate bounds
    min_lat, max_lat = -35.0, 37.0  # Cape Agulhas to Mediterranean
    min_lon, max_lon = -25.0, 52.0  # Atlantic to Indian Ocean
    
    out_of_bounds = []
    
    for i, loc in enumerate(locations):
        lat, lon = loc["lat"], loc["lon"]
        
        if not (min_lat <= lat <= max_lat):
            out_of_bounds.append(f"Location {i+1} (lat {lat:.2f}): outside Africa latitude bounds ({min_lat}, {max_lat})")
        
        if not (min_lon <= lon <= max_lon):
            out_of_bounds.append(f"Location {i+1} (lon {lon:.2f}): outside Africa longitude bounds ({min_lon}, {max_lon})")
    
    if out_of_bounds:
        error_msg = "Some locations are outside Africa bounds:\n" + "\n".join(out_of_bounds[:5])
        if len(out_of_bounds) > 5:
            error_msg += f"\n... and {len(out_of_bounds) - 5} more locations"
        return False, error_msg
    
    return True, ""
