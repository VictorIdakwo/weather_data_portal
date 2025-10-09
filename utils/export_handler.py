import pandas as pd
import geopandas as gpd
import json
import tempfile
import os
from typing import Dict, Any
from .shapefile_handler import create_geodataframe_from_data, create_shapefile_zip


def export_to_csv(df: pd.DataFrame) -> bytes:
    """
    Export DataFrame to CSV format.
    
    Args:
        df: DataFrame to export
    
    Returns:
        CSV data as bytes
    """
    return df.to_csv(index=False).encode("utf-8")


def export_to_json(df: pd.DataFrame, orient: str = "records") -> bytes:
    """
    Export DataFrame to JSON format.
    
    Args:
        df: DataFrame to export
        orient: JSON orientation ('records', 'split', 'index', 'columns', 'values')
    
    Returns:
        JSON data as bytes
    """
    # Handle datetime columns
    df_copy = df.copy()
    for col in df_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].astype(str)
    
    json_str = df_copy.to_json(orient=orient, indent=2)
    return json_str.encode("utf-8")


def export_to_geojson(df: pd.DataFrame, lat_col: str = "latitude", lon_col: str = "longitude") -> bytes:
    """
    Export DataFrame to GeoJSON format.
    
    Args:
        df: DataFrame to export
        lat_col: Name of latitude column
        lon_col: Name of longitude column
    
    Returns:
        GeoJSON data as bytes
    """
    # Create GeoDataFrame
    gdf = create_geodataframe_from_data(df, lat_col, lon_col)
    
    # Convert to GeoJSON
    geojson_str = gdf.to_json()
    return geojson_str.encode("utf-8")


def export_to_shapefile(df: pd.DataFrame, lat_col: str = "latitude", lon_col: str = "longitude") -> str:
    """
    Export DataFrame to Shapefile format (as ZIP).
    
    Args:
        df: DataFrame to export
        lat_col: Name of latitude column
        lon_col: Name of longitude column
    
    Returns:
        Path to ZIP file containing shapefile
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "export")
    
    # Create GeoDataFrame
    gdf = create_geodataframe_from_data(df, lat_col, lon_col)
    
    # Shapefile has column name length limit of 10 characters
    # Truncate column names if needed
    gdf.columns = [col[:10] if len(col) > 10 else col for col in gdf.columns]
    
    # Convert datetime columns to strings (shapefiles don't support datetime)
    for col in gdf.columns:
        if col != "geometry" and pd.api.types.is_datetime64_any_dtype(gdf[col]):
            gdf[col] = gdf[col].astype(str)
    
    # Save shapefile
    gdf.to_file(f"{output_path}.shp")
    
    # Create ZIP file
    zip_path = create_shapefile_zip(output_path)
    
    return zip_path


def export_to_excel(df: pd.DataFrame) -> bytes:
    """
    Export DataFrame to Excel format.
    
    Args:
        df: DataFrame to export
    
    Returns:
        Excel data as bytes
    """
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Write to Excel
        df.to_excel(tmp_path, index=False, engine="openpyxl")
        
        # Read back as bytes
        with open(tmp_path, "rb") as f:
            data = f.read()
        
        return data
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def get_export_filename(base_name: str, format: str) -> str:
    """
    Generate export filename based on format.
    
    Args:
        base_name: Base name for the file
        format: Export format ('CSV', 'JSON', 'GeoJSON', 'Shapefile', 'Excel')
    
    Returns:
        Filename with appropriate extension
    """
    format_extensions = {
        "CSV": ".csv",
        "JSON": ".json",
        "GeoJSON": ".geojson",
        "Shapefile": ".zip",
        "Excel": ".xlsx",
    }
    
    extension = format_extensions.get(format, ".txt")
    return f"{base_name}{extension}"


def get_export_mime_type(format: str) -> str:
    """
    Get MIME type for export format.
    
    Args:
        format: Export format
    
    Returns:
        MIME type string
    """
    mime_types = {
        "CSV": "text/csv",
        "JSON": "application/json",
        "GeoJSON": "application/geo+json",
        "Shapefile": "application/zip",
        "Excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    
    return mime_types.get(format, "application/octet-stream")
