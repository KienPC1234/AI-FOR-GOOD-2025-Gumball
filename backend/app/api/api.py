from fastapi import APIRouter

from app.api.endpoints import auth, users, files, patients, scans, xray, tasks

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(xray.router, prefix="/xray", tags=["xray"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])