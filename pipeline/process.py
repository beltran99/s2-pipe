from rio_cogeo.cogeo import cog_translate, cog_validate
from rio_cogeo.profiles import cog_profiles
from rio_tiler.io import COGReader
from rasterio.io import DatasetReader, MemoryFile
from rasterio import open as rio_open

from pathlib import Path
from typing import Union
import os
import tarfile
import json

ROOT_DIR = Path(__file__).parent.parent.resolve()
RAW_DATA_PATH = ROOT_DIR / "data/raw"

def resolve_data_path(path: Union[str, Path]) -> list[Path]:
    if isinstance(path, str):
        path_str = str(ROOT_DIR / path)
    elif isinstance(path, Path):
        path_str = str(path)
    else:
        raise TypeError("Path must be a string or Path object.")
        
    if os.path.isfile(path_str) and path_str.endswith(".tar"):
        return [Path(path_str)]
    elif os.path.isdir(path_str):
        return [
            Path(os.path.join(root, file))
            for root, dirs, files in os.walk(str(path_str)) if not dirs # take only leaf nodes
            for file in files if file.endswith(".tar")
        ]
    else:
        raise FileNotFoundError(f"Path {path_str} does not exist or is not a valid .tar file or directory.")
    
def extract_data(paths: list[Path]):
    for path in paths:
        with tarfile.open(str(path), "r:*") as tar:
            # extract userdata.json
            member = tar.getmember("userdata.json")
            f = tar.extractfile(member)
            data = f.read()
            data_json = json.loads(data.decode('utf-8'))
            
            search_id = data_json["search_id"]
            
            out_dir = ROOT_DIR / ("data/cog/" + search_id)
            out_dir.mkdir(parents=True, exist_ok=True)
            
            with open(out_dir / ".metadata.json", "w") as outfile:
                json.dump(data_json, outfile)
            
            # extract tiff file to memory and convert to COG
            member = tar.getmember("default.tif") 
            f = tar.extractfile(member)
            memfile = MemoryFile(f.read())
            input_tiff = memfile.open()
            output_tiff = out_dir / (search_id + ".tiff")
            
            convert_to_cog(input_tiff, output_tiff)
            is_valid, errors, warnings = cog_validate(output_tiff)
            print(f"COG validation for {output_tiff.parent.stem}: {is_valid=}, {errors=}, {warnings=}")
            
            input_tiff.close()
            memfile.close()

def convert_to_cog(input_tiff, output_tiff):
    cog_translate(
        input_tiff,
        output_tiff,
        dst_kwargs=cog_profiles.get("deflate"),
        use_cog_driver=True,
        quiet=True,
    )
    
def process_data(datapath: Union[str, Path] = RAW_DATA_PATH):
    resolved_paths = resolve_data_path(datapath)
    extract_data(resolved_paths)
        
if __name__ == "__main__":
    process_data()