"""
Utility script to create a sample shapefile for testing the Weather Data Portal.
This creates a shapefile with sample locations across Nigeria.
"""

import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import os

def create_sample_points_shapefile(output_path="sample_locations"):
    """
    Create a sample point shapefile with locations across Nigeria.
    
    Args:
        output_path: Output path without extension (default: "sample_locations")
    """
    # Sample locations (health facilities, schools, etc.)
    locations = [
        {"name": "Lagos_Central", "type": "Health", "lat": 6.5244, "lon": 3.3792},
        {"name": "Abuja_North", "type": "Health", "lat": 9.0765, "lon": 7.3986},
        {"name": "Kano_City", "type": "Health", "lat": 12.0022, "lon": 8.5919},
        {"name": "Port_Harcourt", "type": "Health", "lat": 4.8156, "lon": 7.0498},
        {"name": "Ibadan_Central", "type": "School", "lat": 7.3775, "lon": 3.9470},
        {"name": "Kaduna_Metro", "type": "School", "lat": 10.5265, "lon": 7.4388},
        {"name": "Benin_City", "type": "Health", "lat": 6.3350, "lon": 5.6037},
        {"name": "Jos_Plateau", "type": "Research", "lat": 9.9285, "lon": 8.8921},
        {"name": "Maiduguri_Town", "type": "Health", "lat": 11.8333, "lon": 13.1500},
        {"name": "Calabar_South", "type": "School", "lat": 4.9517, "lon": 8.3222},
    ]
    
    # Create DataFrame
    df = pd.DataFrame(locations)
    
    # Create geometry column
    geometry = [Point(row['lon'], row['lat']) for _, row in df.iterrows()]
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df.drop(['lat', 'lon'], axis=1),
        geometry=geometry,
        crs="EPSG:4326"
    )
    
    # Add additional attributes
    gdf['id'] = range(1, len(gdf) + 1)
    gdf['country'] = 'Nigeria'
    gdf['created'] = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    # Save shapefile
    output_file = f"{output_path}.shp"
    gdf.to_file(output_file)
    
    print(f"✓ Created sample point shapefile: {output_file}")
    print(f"  - {len(gdf)} locations")
    print(f"  - Attributes: {', '.join(gdf.columns.drop('geometry'))}")
    
    return output_file


def create_sample_polygon_shapefile(output_path="sample_regions"):
    """
    Create a sample polygon shapefile with regions in Nigeria.
    
    Args:
        output_path: Output path without extension (default: "sample_regions")
    """
    from shapely.geometry import Polygon
    
    # Sample regions (simplified bounding boxes)
    regions = [
        {
            "name": "Lagos_Region",
            "population": 15000000,
            "area_km2": 3577,
            "coordinates": [
                (3.0, 6.2),
                (3.7, 6.2),
                (3.7, 6.7),
                (3.0, 6.7),
                (3.0, 6.2)
            ]
        },
        {
            "name": "Kano_Region",
            "population": 13000000,
            "area_km2": 20131,
            "coordinates": [
                (7.8, 11.5),
                (9.0, 11.5),
                (9.0, 12.5),
                (7.8, 12.5),
                (7.8, 11.5)
            ]
        },
        {
            "name": "FCT_Region",
            "population": 3500000,
            "area_km2": 7315,
            "coordinates": [
                (6.9, 8.5),
                (7.8, 8.5),
                (7.8, 9.5),
                (6.9, 9.5),
                (6.9, 8.5)
            ]
        },
    ]
    
    # Create geometries
    geometries = [Polygon(region['coordinates']) for region in regions]
    
    # Create DataFrame
    data = [{k: v for k, v in region.items() if k != 'coordinates'} for region in regions]
    df = pd.DataFrame(data)
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometries, crs="EPSG:4326")
    
    # Add additional attributes
    gdf['id'] = range(1, len(gdf) + 1)
    gdf['country'] = 'Nigeria'
    gdf['created'] = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    # Calculate centroids for reference
    gdf['cent_lat'] = gdf.geometry.centroid.y
    gdf['cent_lon'] = gdf.geometry.centroid.x
    
    # Save shapefile
    output_file = f"{output_path}.shp"
    gdf.to_file(output_file)
    
    print(f"✓ Created sample polygon shapefile: {output_file}")
    print(f"  - {len(gdf)} regions")
    print(f"  - Attributes: {', '.join(gdf.columns.drop('geometry'))}")
    
    return output_file


def zip_shapefile(shapefile_path):
    """
    Create a ZIP file containing all shapefile components.
    
    Args:
        shapefile_path: Path to .shp file (with or without extension)
    """
    import zipfile
    
    # Remove extension if present
    base_path = shapefile_path.replace('.shp', '')
    base_name = os.path.basename(base_path)
    
    # Extensions to include
    extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg']
    
    # Create ZIP file
    zip_path = f"{base_path}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for ext in extensions:
            file_path = f"{base_path}{ext}"
            if os.path.exists(file_path):
                zipf.write(file_path, f"{base_name}{ext}")
    
    print(f"✓ Created ZIP file: {zip_path}")
    print(f"  Ready to upload to Weather Data Portal!")
    
    return zip_path


def main():
    """Main function to create sample shapefiles."""
    print("=" * 60)
    print("Creating Sample Shapefiles for Weather Data Portal")
    print("=" * 60)
    print()
    
    # Create sample directory if it doesn't exist
    sample_dir = "sample_shapefiles"
    os.makedirs(sample_dir, exist_ok=True)
    
    print("Creating sample shapefiles...\n")
    
    # Create point shapefile
    point_path = os.path.join(sample_dir, "sample_locations")
    point_file = create_sample_points_shapefile(point_path)
    print()
    
    # Create polygon shapefile
    polygon_path = os.path.join(sample_dir, "sample_regions")
    polygon_file = create_sample_polygon_shapefile(polygon_path)
    print()
    
    # Create ZIP files
    print("Creating ZIP files for upload...\n")
    point_zip = zip_shapefile(point_path)
    print()
    polygon_zip = zip_shapefile(polygon_path)
    print()
    
    # Summary
    print("=" * 60)
    print("✓ Sample shapefiles created successfully!")
    print("=" * 60)
    print("\nFiles created:")
    print(f"  1. {point_zip}")
    print(f"     - Point geometries (10 locations)")
    print(f"     - Use for: Weather data at specific points")
    print()
    print(f"  2. {polygon_zip}")
    print(f"     - Polygon geometries (3 regions)")
    print(f"     - Use for: Weather data at region centroids")
    print()
    print("Usage:")
    print("  1. Run the Weather Data Portal")
    print("  2. Select 'Upload Shapefile' option")
    print("  3. Upload one of the ZIP files above")
    print("  4. Fetch weather data for the locations")
    print()
    print("Note: These are sample files for testing. Replace with your")
    print("      own shapefiles for real applications.")
    print("=" * 60)


if __name__ == "__main__":
    main()
