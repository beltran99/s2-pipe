from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from rio_tiler.io import COGReader

import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/home")
def root():
    """
    List all available endpoints.
    """

    endpoints = [
        {"endpoint": "/cog", "description": "List all available Cloud Optimized GeoTIFFs."},
        {"endpoint": "/cog/{cog_id}", "description": "Retrieve a specific Cloud Optimized GeoTIFF by its ID."},
        {"endpoint": "/stac", "description": "List all available STAC items."},
        {"endpoint": "/stac/{cog_id}", "description": "Retrieve a specific STAC item by its associated COG ID."},
        {"endpoint": "/tiles/{cog_id}/{z}/{x}/{y}.png", "description": "Retrieve a specific Cloud Optimized GeoTIFF tile by its ID and tile coordinates."},
    ]

    return {
        "info": "Cloud Optimized GeoTIFF service",
        "endpoints": endpoints,
    }

@app.get("/cog/{cog_id}")
async def get_cog(cog_id: str):
    
    cog_path = ROOT_DIR / f"data/cog/{cog_id}/{cog_id}.tiff"

    if not cog_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(
        path=cog_path,
        media_type="image/tiff; application=geotiff; profile=cloud-optimized",
        filename=f"{cog_id}.tif"
    )

@app.get("/cog")
def list_cogs():
    files = [f.parent.name for f in (ROOT_DIR / "data/cog").glob("*/*.tiff")]
    return {"available_cogs": files}

@app.get("/tiles/{cog_id}/{z}/{x}/{y}.png")
def get_tile(cog_id: str, z: int, x: int, y: int):
    cog_path = ROOT_DIR / f"data/cog/{cog_id}/{cog_id}.tiff"
    try:
        with COGReader(str(cog_path)) as cog:
            tile = cog.tile(x, y, z)
            return Response(tile.render(), media_type="image/png")
    except Exception as e:
        if "TileOutsideBounds" in str(e):
            return Response(status_code=204)  # empty tile
        raise 

@app.get("/stac/{cog_id}")
async def get_stac(cog_id: str):
    
    stac_path = ROOT_DIR / f"data/cog/{cog_id}/{cog_id}.json"

    if not stac_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(
        path=stac_path,
        media_type="application/json",
        filename=f"{cog_id}.json"
    )

@app.get("/stac")
def list_stacs():
    files = [f.parent.name for f in (ROOT_DIR / "data/cog").glob("*/*.json")]
    return {"available_stacs": list(set(files))}