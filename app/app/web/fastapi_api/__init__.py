from fastapi import APIRouter

from .auth import router as auth_router
from .admin import router as admin_router
from .cabinet import router as cabinet_router
from .devices import router as devices_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(cabinet_router)
router.include_router(devices_router)
