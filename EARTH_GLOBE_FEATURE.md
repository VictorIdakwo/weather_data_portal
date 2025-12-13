# 🌍 3D Earth Globe Visualization Feature

## Overview
A new interactive 3D rotating earth globe visualization has been added to the Weather Data Portal. This feature provides an immersive way to view and explore selected locations on a realistic 3D earth model.

## Features

### 1. **📍 Zoom to Locations Tab**
- Automatically centers the globe on all selected locations
- Adjusts zoom level based on the geographic spread of locations
- Shows all location markers with labels
- Interactive: Click and drag to rotate, scroll to zoom

### 2. **🔄 Rotating Globe Tab**
- Animated rotating earth view
- Shows all selected locations as the globe spins
- Play/Pause controls for the animation
- Smooth 360° rotation

### 3. **🎯 Select Location Tab**
- Dropdown to choose any specific location
- Globe zooms directly to the selected location
- Highlights the selected location with a special marker
- Displays location details (name, latitude, longitude)

## How It Works

### When Locations Are Selected
After selecting locations (via African Countries/Divisions, Shapefile, or KML upload), the globe visualization automatically appears below the location list.

### Three Interactive Views
The feature provides three tabs, each offering a different perspective:

1. **Zoom to Locations**: Best for seeing all your locations at once
2. **Rotating Globe**: Great for presentations and getting a global perspective
3. **Select Location**: Perfect for focusing on individual locations

## Technical Details

### Implementation
- **Module**: `utils/earth_globe.py`
- **Visualization Library**: Plotly (3D Surface plots)
- **Integration**: `app.py` (lines 511-569)

### Key Functions

#### `create_earth_globe(locations, zoom_to_location, show_all_markers, height)`
Creates a static 3D earth globe with location markers.

**Parameters:**
- `locations`: List of tuples (latitude, longitude, location_name)
- `zoom_to_location`: Index of location to zoom to (optional)
- `show_all_markers`: Whether to show all location markers
- `height`: Height of visualization in pixels

#### `create_animated_earth_globe(locations, rotation_frames, height)`
Creates an animated rotating earth globe.

**Parameters:**
- `locations`: List of tuples (latitude, longitude, location_name)
- `rotation_frames`: Number of frames for full rotation (default: 36)
- `height`: Height of visualization in pixels

#### `create_location_zoom_globe(locations, height)`
Creates a globe that auto-zooms to the centroid of all locations.

**Parameters:**
- `locations`: List of tuples (latitude, longitude, location_name)
- `height`: Height of visualization in pixels

### Coordinate System
- Uses spherical coordinates (latitude/longitude)
- Converts to 3D Cartesian coordinates for rendering
- Earth radius normalized to 1.0 for visualization

### Styling
- **Earth Surface**: Blue-green gradient (ocean to land)
- **Location Markers**: Red circles with white borders
- **Selected Location**: Yellow diamond with orange border
- **Background**: Dark theme for better contrast
- **Labels**: White text for visibility

## User Experience

### Interactive Controls
- **Rotate**: Click and drag anywhere on the globe
- **Zoom**: Scroll wheel or pinch gesture
- **Reset**: Double-click to reset view
- **Animation**: Use Play/Pause buttons in Rotating Globe tab

### Visual Feedback
- Location markers are clearly visible above the earth surface
- Hover over markers to see location details
- Selected location is highlighted with a different color/shape
- Smooth transitions when zooming to locations

## Benefits

1. **Intuitive**: Users can immediately see where their selected locations are on Earth
2. **Interactive**: Full 3D manipulation provides better spatial understanding
3. **Educational**: Great for presentations and understanding geographic relationships
4. **Beautiful**: Modern, visually appealing interface
5. **Functional**: Helps verify location selections before downloading data

## Usage Example

```python
# Example: Create a globe for Nigerian cities
locations = [
    (9.0820, 8.6753, "Abuja, Nigeria"),
    (6.5244, 3.3792, "Lagos, Nigeria"),
    (11.9974, 8.5211, "Kano, Nigeria")
]

# Auto-zoom to show all locations
fig = create_location_zoom_globe(locations, height=600)

# Or zoom to a specific location (e.g., Lagos)
fig = create_earth_globe(locations, zoom_to_location=1)

# Or create rotating animation
fig = create_animated_earth_globe(locations)
```

## Testing

Run the test script to verify the module:
```bash
python test_earth_globe.py
```

All tests should pass, confirming:
- Basic globe creation
- Zoom to specific location
- Animated rotation
- Auto-zoom to multiple locations
- Empty location handling

## Future Enhancements

Potential improvements for future versions:
- Real earth texture/satellite imagery
- Country borders overlay
- Connection lines between locations
- Weather data overlay on globe
- Time-series animation showing data changes
- Export globe as interactive HTML

## Dependencies

- `plotly>=5.18.0` (already in requirements.txt)
- `numpy` (already in requirements.txt)
- `streamlit` (already in requirements.txt)

No additional dependencies required!

## Credits

Developed by: Victor Iko-ojo Idakwo (RTP, MNITP, MGEOSON)
Date: December 2024
