from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.app.web.fastapi_api.deps import get_current_user, get_session
from app.database.dal import subscription_dal, user_dal

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
async def get_devices(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["id"])
    panel_service = request.app.state.panel_service
    if panel_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unavailable")

    user = await user_dal.get_user_by_id(session, user_id)
    if not user or not user.panel_user_uuid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")

    sub = await subscription_dal.get_active_subscription_by_user_id(session, user_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")

    devices_response, panel_user = await __import__("asyncio").gather(
        panel_service.get_user_devices(user.panel_user_uuid),
        panel_service.get_user_by_uuid(user.panel_user_uuid),
    )

    devices_list = []
    if isinstance(devices_response, dict):
        devices_list = devices_response.get("devices") or []
    elif isinstance(devices_response, list):
        devices_list = devices_response

    max_devices = None
    if panel_user:
        limit = panel_user.get("hwidDeviceLimit")
        if limit is not None and int(limit) > 0:
            max_devices = int(limit)

    return {
        "devices": devices_list,
        "current_count": len(devices_list),
        "max_devices": max_devices,
    }


@router.post("/disconnect")
async def disconnect_device(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["id"])
    panel_service = request.app.state.panel_service
    if panel_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unavailable")

    body = await request.json()
    hwid = str(body.get("hwid") or "").strip()
    if not hwid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="hwid is required")

    user = await user_dal.get_user_by_id(session, user_id)
    if not user or not user.panel_user_uuid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")

    success = await panel_service.disconnect_device(user.panel_user_uuid, hwid)
    if not success:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to disconnect device")
    return {"success": True}
