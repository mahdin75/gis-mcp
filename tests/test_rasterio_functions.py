"""Tests for Rasterio functions."""
import pytest
import sys
import os
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_bounds, from_origin
import geopandas as gpd
from shapely.geometry import Polygon

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from gis_mcp.mcp import gis_mcp
from fastmcp import Client
import json
from tests.test_helpers import get_result_data


@pytest.fixture
def sample_raster_file(temp_dir):
    """Create a sample raster file for testing."""
    # Use pyproj to avoid PROJ database conflicts with PostgreSQL
    import pyproj
    data = np.random.randint(0, 255, (1, 10, 10), dtype=np.uint8)
    transform = from_bounds(0, 0, 10, 10, 10, 10)
    
    test_file = os.path.join(temp_dir, 'test_raster.tif')
    # Use pyproj to create CRS, then convert to WKT for rasterio
    # This avoids conflicts with PostgreSQL's PROJ database
    try:
        pyproj_crs = pyproj.CRS.from_epsg(4326)
        crs = pyproj_crs.to_wkt()
    except Exception:
        # Fallback to simple WKT string for EPSG:4326
        crs = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
    
    with rasterio.open(
        test_file,
        'w',
        driver='GTiff',
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs=crs,
        transform=transform,
        nodata=0
    ) as dst:
        dst.write(data)
    
    return test_file


@pytest.fixture
def sample_vector_file(temp_dir):
    """Create a sample vector file for testing."""
    gdf = gpd.GeoDataFrame(
        {'id': [1, 2]},
        geometry=[
            Polygon([(2, 2), (4, 2), (4, 4), (2, 4), (2, 2)]),
            Polygon([(6, 6), (8, 6), (8, 8), (6, 8), (6, 6)])
        ],
        crs='EPSG:4326'
    )
    test_file = os.path.join(temp_dir, 'test_polygons.shp')
    gdf.to_file(test_file)
    return test_file


@pytest.fixture
def constant_raster_no_nodata(temp_dir):
    """10x10 raster of 100s with no nodata (issue #47 reproduction)."""
    test_file = os.path.join(temp_dir, "constant_100.tif")
    with rasterio.open(
        test_file,
        "w",
        driver="GTiff",
        width=10,
        height=10,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(0, 10, 1, 1),
    ) as dst:
        dst.write(np.full((1, 10, 10), 100, dtype=np.float32))
    return test_file


@pytest.fixture
def triangle_vector_file(temp_dir):
    """Triangle covering about half of a 0–10 / 0–10 bounding box."""
    gdf = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[Polygon([(0, 0), (10, 0), (0, 10), (0, 0)])],
        crs="EPSG:4326",
    )
    test_file = os.path.join(temp_dir, "triangle.geojson")
    gdf.to_file(test_file, driver="GeoJSON")
    return test_file


class TestBasicRasterOperations:
    """Test basic raster operations."""
    
    @pytest.mark.asyncio
    async def test_metadata_raster(self, sample_raster_file):
        """Test getting raster metadata."""
        async with Client(gis_mcp) as client:
            result = await client.call_tool("metadata_raster", {"path_or_url": sample_raster_file})
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert "metadata" in result_data
            metadata = result_data["metadata"]
            assert "width" in metadata
            assert "height" in metadata
            assert "count" in metadata
            assert metadata["width"] == 10
            assert metadata["height"] == 10
    
    @pytest.mark.asyncio
    async def test_get_raster_crs(self, sample_raster_file):
        """Test getting raster CRS."""
        async with Client(gis_mcp) as client:
            result = await client.call_tool("get_raster_crs", {"path_or_url": sample_raster_file})
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert "wkt" in result_data
            assert "proj4" in result_data
    
    @pytest.mark.asyncio
    async def test_extract_band(self, sample_raster_file, temp_dir):
        """Test extracting a band."""
        output_path = os.path.join(temp_dir, "band.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("extract_band", {
                "source": sample_raster_file,
                "band_index": 1,
                "destination": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_raster_band_statistics(self, sample_raster_file):
        """Test calculating band statistics."""
        async with Client(gis_mcp) as client:
            result = await client.call_tool("raster_band_statistics", {
                "source": sample_raster_file
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert "statistics" in result_data
            # Statistics are nested by band name (e.g., "Band 1")
            band_stats = list(result_data["statistics"].values())[0]
            assert "min" in band_stats
            assert "max" in band_stats
            assert "mean" in band_stats
    
    @pytest.mark.asyncio
    async def test_raster_histogram(self, sample_raster_file):
        """Test computing raster histogram."""
        async with Client(gis_mcp) as client:
            result = await client.call_tool("raster_histogram", {
                "source": sample_raster_file
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert "histograms" in result_data


class TestRasterProcessing:
    """Test raster processing operations."""
    
    @pytest.mark.asyncio
    async def test_clip_raster_with_shapefile(self, sample_raster_file, sample_vector_file, temp_dir):
        """Test clipping raster with shapefile."""
        output_path = os.path.join(temp_dir, "clipped_raster.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("clip_raster_with_shapefile", {
                "raster_path_or_url": sample_raster_file,
                "shapefile_path": sample_vector_file,
                "destination": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_resample_raster(self, sample_raster_file, temp_dir):
        """Test resampling raster."""
        output_path = os.path.join(temp_dir, "resampled.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("resample_raster", {
                "source": sample_raster_file,
                "scale_factor": 0.5,
                "resampling": "bilinear",
                "destination": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_reproject_raster(self, sample_raster_file, temp_dir):
        """Test reprojecting raster."""
        output_path = os.path.join(temp_dir, "reprojected.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("reproject_raster", {
                "source": sample_raster_file,
                "target_crs": "EPSG:3857",
                "destination": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_tile_raster(self, sample_raster_file, temp_dir):
        """Test tiling raster."""
        async with Client(gis_mcp) as client:
            result = await client.call_tool("tile_raster", {
                "source": sample_raster_file,
                "tile_size": 5,
                "destination_dir": temp_dir
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert "tiles_created" in result_data


class TestRasterAnalysis:
    """Test raster analysis operations."""
    
    @pytest.mark.asyncio
    async def test_compute_ndvi(self, temp_dir):
        """Test computing NDVI."""
        # Create a simple 2-band raster (red and NIR)
        data = np.random.randint(0, 255, (2, 10, 10), dtype=np.uint8)
        transform = from_bounds(0, 0, 10, 10, 10, 10)
        
        # Use pyproj to avoid PROJ database conflicts with PostgreSQL
        import pyproj
        try:
            pyproj_crs = pyproj.CRS.from_epsg(4326)
            crs = pyproj_crs.to_wkt()
        except Exception:
            # Fallback to simple WKT string for EPSG:4326
            crs = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
        
        raster_file = os.path.join(temp_dir, 'multiband.tif')
        with rasterio.open(
            raster_file,
            'w',
            driver='GTiff',
            height=10,
            width=10,
            count=2,
            dtype=data.dtype,
            crs=crs,
            transform=transform
        ) as dst:
            dst.write(data)
        
        output_path = os.path.join(temp_dir, "ndvi.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("compute_ndvi", {
                "source": raster_file,
                "red_band_index": 1,
                "nir_band_index": 2,
                "destination": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_raster_algebra(self, sample_raster_file, temp_dir):
        """Test raster algebra."""
        output_path = os.path.join(temp_dir, "algebra.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("raster_algebra", {
                "raster1": sample_raster_file,
                "raster2": sample_raster_file,
                "band_index": 1,
                "operation": "add",
                "destination": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_concat_bands(self, sample_raster_file, temp_dir):
        """Test concatenating bands."""
        # Create a folder with two raster files for concat_bands
        import shutil
        concat_dir = os.path.join(temp_dir, "concat_input")
        os.makedirs(concat_dir, exist_ok=True)
        shutil.copy(sample_raster_file, os.path.join(concat_dir, "band1.tif"))
        shutil.copy(sample_raster_file, os.path.join(concat_dir, "band2.tif"))
        
        output_path = os.path.join(temp_dir, "concat.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("concat_bands", {
                "folder_path": concat_dir,
                "destination": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_weighted_band_sum(self, sample_raster_file, temp_dir):
        """Test weighted band sum."""
        output_path = os.path.join(temp_dir, "weighted.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("weighted_band_sum", {
                "source": sample_raster_file,
                "weights": [1.0],
                "destination": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)


class TestAdvancedAnalysis:
    """Test advanced analysis operations."""
    
    @pytest.mark.asyncio
    async def test_zonal_statistics(self, sample_raster_file, sample_vector_file):
        """Test zonal statistics."""
        async with Client(gis_mcp) as client:
            result = await client.call_tool("zonal_statistics", {
                "raster_path": sample_raster_file,
                "vector_path": sample_vector_file,
                "stats": ["mean", "min", "max"]
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert "results" in result_data
            assert len(result_data["results"]) > 0

    @pytest.mark.asyncio
    async def test_zonal_statistics_ignores_fill_when_no_nodata(
        self, constant_raster_no_nodata, triangle_vector_file
    ):
        """Fill pixels outside the polygon must not be counted as 0 (issue #47)."""
        async with Client(gis_mcp) as client:
            result = await client.call_tool("zonal_statistics", {
                "raster_path": constant_raster_no_nodata,
                "vector_path": triangle_vector_file,
                "stats": ["mean", "min", "max", "count"],
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            stats = result_data["results"][0]
            assert stats["mean"] == 100.0
            assert stats["min"] == 100.0
            assert stats["max"] == 100.0
            assert stats["count"] > 0
            # Cropped bbox is 10x10; the triangle covers about half, not the fill zeros.
            assert stats["count"] < 100

    @pytest.mark.asyncio
    async def test_clip_raster_writes_nodata_when_source_has_none(
        self, constant_raster_no_nodata, triangle_vector_file, temp_dir
    ):
        """Clipped output must set nodata so outside-polygon pixels are not 0."""
        output_path = os.path.join(temp_dir, "clipped_no_nodata.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("clip_raster_with_shapefile", {
                "raster_path_or_url": constant_raster_no_nodata,
                "shapefile_path": triangle_vector_file,
                "destination": output_path,
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"

        with rasterio.open(output_path) as src:
            assert src.nodata is not None
            band = src.read(1, masked=True)
            assert np.ma.is_masked(band)
            assert float(band.mean()) == 100.0
            assert float(band.min()) == 100.0
            assert float(band.max()) == 100.0
    
    @pytest.mark.asyncio
    async def test_reclassify_raster(self, sample_raster_file, temp_dir):
        """Test reclassifying raster."""
        output_path = os.path.join(temp_dir, "reclassified.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("reclassify_raster", {
                "raster_path": sample_raster_file,
                "reclass_map": {0: 1, 255: 2},
                "output_path": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_focal_statistics(self, sample_raster_file, temp_dir):
        """Test focal statistics."""
        output_path = os.path.join(temp_dir, "focal.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("focal_statistics", {
                "raster_path": sample_raster_file,
                "statistic": "mean",
                "size": 3,
                "output_path": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_hillshade(self, sample_raster_file, temp_dir):
        """Test hillshade generation."""
        output_path = os.path.join(temp_dir, "hillshade.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("hillshade", {
                "raster_path": sample_raster_file,
                "azimuth": 315,
                "angle_altitude": 45,
                "output_path": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_write_raster(self, sample_raster_file, temp_dir):
        """Test writing raster from array."""
        # Read existing raster to get reference
        with rasterio.open(sample_raster_file) as src:
            data = src.read(1)
        
        output_path = os.path.join(temp_dir, "written.tif")
        async with Client(gis_mcp) as client:
            result = await client.call_tool("write_raster", {
                "array": data.tolist(),
                "reference_raster": sample_raster_file,
                "output_path": output_path
            })
            result_data = get_result_data(result)
            assert result_data["status"] == "success"
            assert os.path.exists(output_path)
