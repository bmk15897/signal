"""
Unkey API key verification middleware.
Add as a FastAPI dependency on any route that needs auth.
"""

import os
from fastapi import Header, HTTPException


async def verify_api_key(x_api_key: str = Header(...)):
    """FastAPI dependency — verifies the X-Api-Key header via Unkey."""
    try:
        from unkey import Unkey  # noqa: PLC0415
        client = Unkey(root_key=os.environ["UNKEY_ROOT_KEY"])
        result = await client.keys.verify({"key": x_api_key, "api_id": os.environ["UNKEY_API_ID"]})
        if not result.valid:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return result
    except ImportError:
        # unkey package not available — skip auth in dev
        return {"valid": True, "dev_mode": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Auth error: {e}")
