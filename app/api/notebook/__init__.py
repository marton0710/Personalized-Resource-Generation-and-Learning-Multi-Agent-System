from fastapi import APIRouter

from .chat_routes import router as chat_router
from .file_routes import router as file_router
from .note_routes import router as note_router
from .workspace_routes import router as workspace_router

router = APIRouter()
router.include_router(workspace_router, prefix="/notebooks", tags=["notebooks"])
router.include_router(file_router, prefix="/notebooks", tags=["notebooks"])
router.include_router(chat_router, prefix="/notebooks", tags=["notebooks"])
router.include_router(note_router, prefix="/notebooks", tags=["notebooks"])
