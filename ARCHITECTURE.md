# 🏗️ Weather Data Portal - Architecture

## System Overview

The Weather Data Portal is a modular Streamlit application designed to fetch, process, and export weather data from multiple sources for locations across Nigeria.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI (app.py)                     │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐    │
│  │ Data Source  │  │   Location    │  │  Export Format   │    │
│  │  Selection   │  │   Selection   │  │    Selection     │    │
│  └──────────────┘  └───────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Source Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────┐  ┌───────┐  ┌────────┐ │
│  │   NASA   │  │  Open    │  │ ERA5 │  │ MODIS │  │ CHIRPS │ │
│  │  POWER   │  │ Weather  │  │      │  │       │  │        │ │
│  └──────────┘  └──────────┘  └──────┘  └───────┘  └────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Utilities Layer                             │
│  ┌─────────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │    Nigeria      │  │  Shapefile  │  │     Export       │   │
│  │   Locations     │  │   Handler   │  │     Handler      │   │
│  └─────────────────┘  └─────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     External APIs/Data                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │   NASA   │  │   CDS    │  │ OpenAPI  │  │   AppEEARS   │   │
│  │ POWER API│  │   API    │  │          │  │              │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend Layer (Streamlit)
**File**: `app.py`

**Responsibilities**:
- User interface rendering
- User input collection
- Progress feedback
- Data visualization
- Export triggering

**Key Features**:
- Responsive sidebar for configuration
- Dynamic parameter selection based on data source
- Location selection (states/LGAs or shapefile)
- Date range picker
- Export format selector

### 2. Data Source Layer
**Directory**: `data_sources/`

**Modules**:

#### `nasa_power.py`
- **Source**: NASA POWER API (freely accessible)
- **Data**: Meteorological and solar parameters
- **Resolutions**: Hourly, Daily, Monthly
- **Authentication**: None required
- **Performance**: Fast (synchronous API)

#### `openweather.py`
- **Source**: OpenWeather API
- **Data**: Real-time and forecast weather
- **Resolutions**: Hourly, Daily
- **Authentication**: API key required
- **Performance**: Fast (synchronous API)
- **Limitations**: Historical data requires subscription

#### `era5.py`
- **Source**: Copernicus Climate Data Store
- **Data**: Climate reanalysis data
- **Resolutions**: Hourly, Daily, Monthly
- **Authentication**: CDS API key required
- **Performance**: Slow (queue-based processing)
- **Format**: NetCDF (requires processing)

#### `modis.py`
- **Source**: NASA AppEEARS
- **Data**: Satellite imagery products (LST, NDVI, ET)
- **Resolutions**: Daily, 8-day, 16-day
- **Authentication**: NASA Earthdata account
- **Performance**: Very slow (asynchronous task submission)
- **Status**: Simplified implementation (framework provided)

#### `chirps.py`
- **Source**: UCSB Climate Hazards Group
- **Data**: Precipitation estimates
- **Resolutions**: Daily, Pentadal, Dekadal, Monthly
- **Authentication**: None required
- **Performance**: Moderate (requires GeoTIFF processing)
- **Status**: Simplified implementation (framework provided)

### 3. Utilities Layer
**Directory**: `utils/`

#### `nigeria_locations.py`
**Purpose**: Nigeria geographic data management

**Features**:
- 37 states + FCT centroids
- LGA coordinates for major states (Lagos, Kano, FCT)
- Location validation
- Hierarchical selection support

**Data Structure**:
```python
NIGERIA_STATES = {
    "State": (latitude, longitude),
    ...
}

NIGERIA_LGAS = {
    "State": {
        "LGA": (latitude, longitude),
        ...
    },
    ...
}
```

#### `shapefile_handler.py`
**Purpose**: Shapefile processing and validation

**Features**:
- ZIP file extraction
- Shapefile reading (point and polygon geometries)
- Centroid extraction for polygons
- Coordinate system conversion (to WGS84)
- Nigeria bounds validation
- GeoDataFrame creation

**Supported Geometries**:
- Point → Use directly
- Polygon → Extract centroid
- MultiPolygon → Extract centroid
- MultiPoint → Use first point

#### `export_handler.py`
**Purpose**: Data export in multiple formats

**Formats**:
1. **CSV** - Standard tabular format
2. **JSON** - Structured JSON with datetime handling
3. **GeoJSON** - Geographic JSON with geometry
4. **Shapefile** - ESRI Shapefile (as ZIP)
5. **Excel** - XLSX format with openpyxl

**Features**:
- Automatic datetime conversion
- Column name truncation for Shapefile (10 char limit)
- MIME type handling for downloads
- Temporary file cleanup

### 4. Configuration
**File**: `config.py`

**Contains**:
- Environment variable loading
- API endpoints
- Default settings
- Geographic bounds
- Limits and timeouts

## Data Flow

### Typical Request Flow

```
1. User selects data source
   ↓
2. UI updates available parameters
   ↓
3. User selects parameters, dates, locations
   ↓
4. User clicks "Fetch Data"
   ↓
5. App validates inputs
   ↓
6. Data source module is called
   ↓
7. API requests are made (with retries if needed)
   ↓
8. Data is parsed and standardized
   ↓
9. DataFrame is created and cached
   ↓
10. User views and exports data
```

### Location Selection Flow

#### States/LGAs Path:
```
1. User selects states → get_states()
   ↓
2. User selects LGAs (optional) → get_lgas_for_state()
   ↓
3. Extract coordinates → get_selected_locations()
   ↓
4. Return list of (lat, lon) tuples
```

#### Shapefile Path:
```
1. User uploads ZIP file
   ↓
2. Extract shapefile → extract_shapefile_from_zip()
   ↓
3. Read shapefile → read_shapefile()
   ↓
4. Extract locations → extract_locations_from_shapefile()
   ↓
5. Validate bounds → validate_shapefile_locations()
   ↓
6. Return list of (lat, lon) tuples
```

## Technology Stack

### Core Framework
- **Streamlit**: Web application framework
- **Python 3.8+**: Programming language

### Data Processing
- **Pandas**: Tabular data manipulation
- **NumPy**: Numerical operations
- **GeoPandas**: Geospatial data handling
- **Shapely**: Geometric operations

### Geospatial
- **Rasterio**: Raster data reading
- **Fiona**: Vector data I/O
- **PyProj**: Coordinate transformations
- **Folium**: Interactive maps (optional)

### APIs & Network
- **Requests**: HTTP requests
- **CDS API**: ERA5 data access
- **XArray**: NetCDF data handling
- **NetCDF4**: NetCDF file support

### Export
- **OpenPyXL**: Excel file creation
- **JSON**: Built-in Python module
- **GeoPandas**: Shapefile/GeoJSON export

## Performance Considerations

### Optimization Strategies

1. **API Request Batching**
   - Group multiple locations when possible
   - Minimize API calls

2. **Caching**
   - Session state for fetched data
   - Avoids re-fetching on UI updates

3. **Lazy Loading**
   - Parameters loaded on source selection
   - Modules imported only when needed

4. **Progress Feedback**
   - Spinners for long operations
   - Status messages during fetching

### Bottlenecks

1. **ERA5 Requests**: Queue-based, can take 5-30 minutes
2. **Large Date Ranges**: More data = longer processing
3. **Multiple Locations**: Linear scaling with location count
4. **Shapefile Export**: Geometry creation overhead

## Error Handling

### Strategy
- Try-catch blocks around API calls
- Graceful degradation
- User-friendly error messages
- Logging for debugging

### Common Errors Handled
- Network timeouts
- Invalid API keys
- Missing data
- Invalid coordinates
- File processing errors

## Security Considerations

### API Key Management
- Environment variables (`.env` file)
- Never committed to version control
- User-provided keys not stored

### Input Validation
- Date range validation
- Coordinate bounds checking
- File type verification
- Parameter validation

### Data Privacy
- No user data stored
- Session-based state only
- Temporary files cleaned up

## Extensibility

### Adding New Data Sources

1. Create new module in `data_sources/`
2. Implement standard interface:
   ```python
   def get_available_parameters() -> Dict
   def get_temporal_resolutions() -> List
   def fetch_data(...) -> pd.DataFrame
   ```
3. Update `app.py` to include new source
4. Add API configuration if needed

### Adding New Export Formats

1. Add function to `utils/export_handler.py`
2. Update `get_export_filename()`
3. Update `get_export_mime_type()`
4. Add to `EXPORT_FORMATS` in config

### Adding More Locations

1. Update `NIGERIA_LGAS` in `nigeria_locations.py`
2. Add coordinates for new LGAs
3. No code changes needed

## Deployment Options

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud
1. Push to GitHub
2. Connect repository to Streamlit Cloud
3. Add secrets in dashboard
4. Deploy

### Docker (Future)
```dockerfile
FROM python:3.9
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

### Server Deployment
- Use with NGINX reverse proxy
- Set up systemd service
- Configure firewall rules
- Add SSL certificate

## Testing Strategy

### Unit Tests (Future Enhancement)
- Test each data source module
- Test utility functions
- Mock API responses

### Integration Tests
- End-to-end data fetching
- Export functionality
- Shapefile processing

### Manual Testing
- Run `test_setup.py`
- Test each data source
- Verify exports
- Check error handling

## Maintenance

### Regular Updates
- Update package versions
- Check API endpoint changes
- Add new parameters as available
- Expand LGA coverage

### Monitoring
- Log API failures
- Track popular data sources
- Monitor performance metrics

## Future Enhancements

1. **Data Visualization**
   - Time series plots
   - Spatial maps
   - Comparison charts

2. **Advanced Features**
   - Data quality checks
   - Anomaly detection
   - Statistical analysis
   - Batch processing

3. **Additional Data Sources**
   - TRMM (Precipitation)
   - SRTM (Elevation)
   - Sentinel (Satellite)
   - Local weather stations

4. **Performance**
   - Async data fetching
   - Result caching
   - Database storage
   - Background tasks

5. **User Management**
   - User accounts
   - Saved queries
   - Download history
   - API key management

---

**Last Updated**: October 2025
