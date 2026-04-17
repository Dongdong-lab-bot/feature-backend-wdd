from fastapi import APIRouter
from app.modules.user.api import router as user_router
from app.modules.user.org_api import router as org_router
from app.modules.user.image_api import router as image_router
from app.modules.ledger.api import router as ledger_router
from app.modules.inspection.api import router as inspection_router
from app.modules.video.api import router as video_router
from app.modules.device.api import router as device_router

api_router = APIRouter()

api_router.include_router(user_router)
api_router.include_router(org_router)
api_router.include_router(image_router)
api_router.include_router(ledger_router)
api_router.include_router(inspection_router)
api_router.include_router(video_router)
api_router.include_router(device_router)
