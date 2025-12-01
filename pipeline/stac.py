import json
from datetime import datetime
from pathlib import Path

import pystac
from shapely import from_wkt
from shapely.geometry import mapping

ROOT_DIR = Path(__file__).parent.parent.resolve()
PROCESSED_DATA_PATH = ROOT_DIR / "data/cog"

def get_bbox_and_footprint(wkt_str):
    geom = from_wkt(wkt_str)
    minx, miny, maxx, maxy = geom.bounds
    bbox = [minx, miny, maxx, maxy]
    footprint = mapping(geom)
    
    return bbox, footprint

def build_stac_item(cog_path):
    
    with open(cog_path.parent / ".metadata.json", "r") as file:
        metadata = json.load(file)
        
    bbox, footprint = get_bbox_and_footprint(metadata["bbox"])
    
    item = pystac.Item(
        id=metadata["search_id"],
        geometry=footprint,
        bbox=bbox,
        datetime=datetime.fromisoformat(metadata["datetime"]),
        properties={},
    )

    asset = pystac.Asset(
        href=str(cog_path),
        media_type=pystac.MediaType.COG,
        roles=["data"]
    )
    item.add_asset("cog", asset)

    return item

def create_stac_catalog(datapath: Path = PROCESSED_DATA_PATH):
    
    catalog = pystac.Catalog(
        id="s2-pipeline",
        description="STAC catalog for Sentinel-2 COGs",
        title="Sentinel-2 COG Catalog",
    )
    
    cog_dirs = datapath.glob("*/*.tiff")
    for cog_dir in cog_dirs:
        item = build_stac_item(cog_dir)
        catalog.add_item(item)
        print(f"Created STAC item: {item.id}")        

    catalog.normalize_hrefs(str(datapath))
    catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED, dest_href=str(datapath))

    print(f"Saved STAC catalog: {datapath / 'catalog.json'}")


if __name__ == "__main__":
    
    create_stac_catalog()