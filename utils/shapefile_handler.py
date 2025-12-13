import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon
from typing import List, Tuple, Dict
import tempfile
import os
import zipfile
from .polygon_sampler import sample_polygon_locations, get_sampling_summary

def extract_shapefile_from_zip(zip_file) -> str:
    """
    Extract shapefile from uploaded ZIP file.
    
    Args:
        zip_file: Uploaded ZIP file object
    
    Returns:
        Path to extracted .shp file
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Save uploaded file
    zip_path = os.path.join(temp_dir, "upload.zip")
    with open(zip_path, "wb") as f:
        f.write(zip_file.read())
    
    # Extract ZIP
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Find .shp file
    shp_file = None
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".shp"):
                shp_file = os.path.join(root, file)
                break
        if shp_file:
            break
    
    if not shp_file:
        raise ValueError("No .shp file found in ZIP archive")
    
    return shp_file


def read_shapefile(file_path: str) -> gpd.GeoDataFrame:
    """
    Read shapefile and return as GeoDataFrame.
    
    Args:
        file_path: Path to shapefile
    
    Returns:
        GeoDataFrame
    """
    try:
        gdf = gpd.read_file(file_path)
        
        # Ensure CRS is set to WGS84 (EPSG:4326)
        if gdf.crs is None:
            gdf.set_crs("EPSG:4326", inplace=True)
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs("EPSG:4326")
        
        return gdf
    
    except Exception as e:
        raise ValueError(f"Error reading shapefile: {str(e)}")


def extract_locations_from_shapefile(
    gdf: gpd.GeoDataFrame, 
    use_polygon_sampling: bool = True,
    grid_spacing_degrees: float = None
) -> List[Dict]:
    """
    Extract locations from shapefile.
    - For point geometries: use the points directly
    - For polygon geometries: generate grid sampling points (if use_polygon_sampling=True)
                            or use centroids (if use_polygon_sampling=False)
    
    Args:
        gdf: GeoDataFrame
        use_polygon_sampling: If True, sample multiple points within polygons
        grid_spacing_degrees: Grid spacing for sampling (auto-calculated if None)
    
    Returns:
        List of dicts with 'name', 'lat', 'lon', 'geometry_type', and any other attributes
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
            "name": row.get("name", row.get("NAME", f"Location_{idx}")),
            "lat": lat,
            "lon": lon,
            "geometry_type": geom_type,
            "id": idx,
        }
        
        # Add all other attributes
        for col in gdf.columns:
            if col not in ["geometry", "name", "NAME"]:
                location[col] = row[col]
        
        locations.append(location)
    
    return locations


def create_geodataframe_from_data(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
) -> gpd.GeoDataFrame:
    """
    Create GeoDataFrame from DataFrame with lat/lon columns.
    
    Args:
        df: DataFrame with data
        lat_col: Name of latitude column
        lon_col: Name of longitude column
    
    Returns:
        GeoDataFrame
    """
    # Create geometry column
    geometry = [Point(xy) for xy in zip(df[lon_col], df[lat_col])]
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    
    return gdf


def save_shapefile(gdf: gpd.GeoDataFrame, output_path: str):
    """
    Save GeoDataFrame as shapefile.
    
    Args:
        gdf: GeoDataFrame to save
        output_path: Output path (without extension)
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    # Save shapefile
    gdf.to_file(f"{output_path}.shp")


def create_shapefile_zip(shapefile_path: str) -> str:
    """
    Create a ZIP file containing all shapefile components.
    
    Args:
        shapefile_path: Path to .shp file (without extension)
    
    Returns:
        Path to ZIP file
    """
    # Get directory and base name
    directory = os.path.dirname(shapefile_path)
    base_name = os.path.basename(shapefile_path)
    
    # Extensions to include in ZIP
    extensions = [".shp", ".shx", ".dbf", ".prj", ".cpg"]
    
    # Create ZIP file
    zip_path = f"{shapefile_path}.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for ext in extensions:
            file_path = f"{shapefile_path}{ext}"
            if os.path.exists(file_path):
                zipf.write(file_path, f"{base_name}{ext}")
    
    return zip_path


def validate_shapefile_locations(locations: List[Dict]) -> tuple:
    """
    Validate if locations are within reasonable bounds for Africa.
    
    Args:
        locations: List of location dictionaries
    
    Returns:
        (is_valid, error_message)
    """
    # Africa approximate bounds (expanded to cover entire continent)
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
