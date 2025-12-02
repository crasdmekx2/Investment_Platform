"""Collectors API router."""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from investment_platform.api.services import collector_service as collector_svc
from investment_platform.api.models.scheduler import ValidateRequest, ValidateResponse
from investment_platform.collectors.base import ValidationError, APIError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metadata", response_model=Dict[str, Any])
async def get_collector_metadata() -> Dict[str, Any]:
    """Get metadata for all available collector types."""
    try:
        metadata = collector_svc.get_collector_metadata()
        return metadata
    except Exception as e:
        logger.error(f"Unexpected error getting collector metadata: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{asset_type}/options", response_model=Dict[str, Any])
async def get_collector_options(asset_type: str) -> Dict[str, Any]:
    """Get collector-specific options for an asset type."""
    try:
        options = collector_svc.get_collector_options(asset_type)
        return options
    except ValueError as e:
        logger.warning(f"Invalid asset type for get_collector_options: {asset_type}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error getting collector options for {asset_type}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{asset_type}/search", response_model=List[Dict[str, Any]])
async def search_assets(
    asset_type: str,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
) -> List[Dict[str, Any]]:
    """Search for assets/symbols of a given type."""
    try:
        results = collector_svc.search_assets(asset_type, q, limit=limit)
        return results
    except ValueError as e:
        logger.warning(f"Invalid parameters for search_assets: asset_type={asset_type}, q={q}")
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        logger.error(f"API error searching assets: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"External API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error searching assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate", response_model=ValidateResponse)
async def validate_collection_params(request: ValidateRequest) -> ValidateResponse:
    """Validate collection parameters before scheduling."""
    try:
        result = collector_svc.validate_collection_params(
            asset_type=request.asset_type,
            symbol=request.symbol,
            collector_kwargs=request.collector_kwargs,
        )
        return ValidateResponse(**result)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except ValueError as e:
        logger.warning(f"Invalid parameters for validate_collection_params: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error validating collection params: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
