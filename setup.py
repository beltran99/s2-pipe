from pipeline import DEFAULT_SEARCH
from pipeline.download import main as download
from pipeline.process import process_data
from pipeline.stac import create_stac_catalog

from sentinelhub import BBox, CRS

def setup():
    # Download data
    print(f"Downloading example Sentinel-2 data...")
    bbox = BBox(bbox=DEFAULT_SEARCH["bbox"], crs=CRS.WGS84)
    time_interval = DEFAULT_SEARCH["timeInterval"]
    _ = download(bbox, time_interval)
    print(f"Download complete.\n")
    
    # Process raw data
    print(f"Processing raw data into COG format...")
    process_data()
    print(f"Processing complete.\n")

    # Create STAC catalog
    print(f"Creating STAC catalog...")
    create_stac_catalog()
    print(f"STAC catalog creation complete.\n")
    
if __name__ == "__main__":
    setup()