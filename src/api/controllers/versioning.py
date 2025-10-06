from fastapi import Query, HTTPException

SUPPORTED_VERSIONS = {"1.0"}

def require_api_version(version: str = Query("1.0", alias="api-version", description="API version (e.g., 1.0)")) -> None:
    if version not in SUPPORTED_VERSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported API version: {version}")