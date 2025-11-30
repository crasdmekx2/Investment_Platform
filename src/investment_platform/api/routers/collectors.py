"""Collectors API router."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from investment_platform.api.services import collector_service as collector_svc
from investment_platform.api.models.scheduler import ValidateRequest, ValidateResponse

router = APIRouter()


@router.get("/metadata", response_model=Dict[str, Any])
async def get_collector_metadata():
    """Get metadata for all available collector types."""
    try:
        metadata = collector_svc.get_collector_metadata()
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asset_type}/options", response_model=Dict[str, Any])
async def get_collector_options(asset_type: str):
    """Get collector-specific options for an asset type."""
    try:
        options = collector_svc.get_collector_options(asset_type)
        return options
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asset_type}/search", response_model=List[Dict[str, Any]])
async def search_assets(
    asset_type: str,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
):
    """Search for assets/symbols of a given type."""
    try:
        results = collector_svc.search_assets(asset_type, q, limit=limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidateResponse)
async def validate_collection_params(request: ValidateRequest):
    """Validate collection parameters before scheduling."""
    try:
        result = collector_svc.validate_collection_params(
            asset_type=request.asset_type,
            symbol=request.symbol,
            collector_kwargs=request.collector_kwargs,
        )
        return ValidateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

