import os
import httpx
import logging
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()
logger = logging.getLogger(__name__)

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml_service:5000")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_ml_service(request: Request, path: str):
    """
    Proxies all requests to the ML service.
    """
    async with httpx.AsyncClient() as client:
        url = f"{ML_SERVICE_URL}/{path}"
        
        # Strip '/api/ml' from the beginning of the path if it's there
        # This depends on how the router is included in main.py
        
        try:
            method = request.method
            content = await request.body()
            headers = dict(request.headers)
            # Remove host header to avoid issues with proxying
            headers.pop("host", None)
            
            response = await client.request(
                method,
                url,
                content=content,
                headers=headers,
                params=request.query_params,
                timeout=60.0
            )
            return response.json() if "application/json" in response.headers.get("content-type", "") else response.content
        except httpx.HTTPError as e:
            logger.error(f"Error proxying to ML service: {e}")
            raise HTTPException(status_code=502, detail="Error proxying to ML service")
