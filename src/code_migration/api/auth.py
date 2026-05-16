import secrets
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from code_migration.config import settings

X_API_KEY = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(X_API_KEY)):
    """Verify API key for protected API routes."""
    expected_key = settings.api_key_value

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key authentication is not configured",
        )

    if not api_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return True
