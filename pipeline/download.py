import io
import os
import json
import datetime as dt
from pathlib import Path
import argparse

import numpy as np
import matplotlib.pyplot as plt
from sentinelhub import SHConfig, WebFeatureService, BBox, CRS, DataCollection, SentinelHubCatalog, MimeType, SentinelHubDownloadClient, SentinelHubRequest, bbox_to_dimensions, filter_times

from . import DEFAULT_SEARCH

ROOT_DIR = Path(__file__).parent.parent.resolve()

def setup_config():
    with open(ROOT_DIR / "config.json") as json_data_file:
        cfg = json.load(json_data_file)

    config = SHConfig()
    config.sh_client_id = cfg["sentinelhub"]["client_id"]
    config.sh_client_secret = cfg["sentinelhub"]["client_secret"]
    config.save()
    
    return config

def search(config, bbox, time_interval, limit=1):
    catalog = SentinelHubCatalog(config=config)
    results = catalog.search(
        DataCollection.SENTINEL2_L2A,
        bbox=bbox,
        time=time_interval,
        limit=limit,
        fields={"include": ["id", "properties.datetime"], "exclude": []},
    )
    
    return results

def download(config, search_results, bbox, time_interval, target_size=(512, 512)):
     
    evalscript = """
        //VERSION=3

        function setup() {
            return {
                input: [{
                    bands: ["B02", "B03", "B04"],
                }],
                output: {
                    id: "default",
                    bands: 3
                }
            };
        }

        function updateOutputMetadata(scenes, inputMetadata, outputMetadata) {
            outputMetadata.userData = {
                "search_id": __placeholder_search_id__,
                "bbox": __placeholder_bbox__,
                "datetime": __placeholder_datetime__
            }
        }

        function evaluatePixel(sample) {
            return [sample.B04 * 2.5, sample.B03 * 2.5, sample.B02 * 2.5];
        }
    """
    
    responses = [
        SentinelHubRequest.output_response("default", MimeType.TIFF),
        SentinelHubRequest.output_response("userdata", MimeType.JSON)
    ]
    
    requests = [] 
    for search_result in search_results:
        input_data = [
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(search_result["properties"]["datetime"], search_result["properties"]["datetime"])
            )
        ]
        
        evalscript_with_id = evalscript.replace("__placeholder_search_id__", f'"{search_result["id"]}"')
        evalscript_with_id = evalscript_with_id.replace("__placeholder_bbox__", f'"{bbox.wkt}"')
        evalscript_with_id = evalscript_with_id.replace("__placeholder_datetime__", f'"{search_result["properties"]["datetime"]}"')
        
        request = SentinelHubRequest(
            data_folder=ROOT_DIR / "data/raw",
            evalscript=evalscript_with_id,
            input_data=input_data,
            responses=responses,
            bbox=bbox,
            size=target_size,
        )
        
        requests.append(request)

    return SentinelHubDownloadClient(config=config).download([request.download_list[0] for request in requests], max_threads=5, show_progress=True)

def main(bbox, time_interval):
    config = setup_config()
    search_results = search(
        config,
        bbox=bbox,
        time_interval=time_interval,
        limit=100
    )
    print(f"Total number of search results: {len(list(search_results))}")
        
    data = download(
        config,
        search_results,
        bbox=bbox,
        time_interval=time_interval,
    )
    return data


if __name__ == "__main__":
    
    argparser = argparse.ArgumentParser(description="Download Sentinel-2 data from Sentinel Hub.")
    argparser.add_argument("--bbox", type=float, nargs=4, metavar=('min_lat', 'min_lon', 'max_lat', 'max_lon'),
                           help="Bounding box coordinates: min_lat min_lon max_lat max_lon", default=DEFAULT_SEARCH['bbox'])
    argparser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format", default=DEFAULT_SEARCH['timeInterval'][0])
    argparser.add_argument("--end-date", type=str, help="End date in YYYY-MM-DD format", default=DEFAULT_SEARCH['timeInterval'][1])
    args = argparser.parse_args()
    
    bbox = BBox(bbox=args.bbox, crs=CRS.WGS84)
    time_interval = (args.start_date, args.end_date)
    
    _ = main(bbox, time_interval)