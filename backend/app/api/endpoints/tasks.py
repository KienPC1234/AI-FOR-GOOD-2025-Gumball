import asyncio

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

import app.schemas as schemas
from app.api import deps, APIResponse
from app.celery_app import celery_app
from app.utils import connect_async_db


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_update(self, user_id: str, data: dict):
        if websocket := self.active_connections.get(user_id):
            await websocket.send_json(data)


router = APIRouter()

manager = ConnectionManager()


@router.websocket("/status/ws",
    description="WebSocket endpoint for real-time task status updates")
async def task_status_websocket(websocket: WebSocket):
    """
    WebSocket connection for real-time task status updates.

    Provides real-time updates for long-running tasks like scan processing
    and analysis. The client will receive updates whenever task status changes.

    Message format:
    {
        "status": "COMPLETED|FAILED|IN_PROGRESS",
        "result": {}     # included when completed
    }

    Parameters:
        websocket: WebSocket connection
        token: Valid user authentication token

    Authentication:
        Requires valid user token in query parameter

    Errors:
        4003: Invalid authentication
        4004: Task not found
    """

    db = connect_async_db()
    user = deps.get_current_user_ws(websocket, db)
    await db.close()

    await manager.connect(user.id, websocket)
    try:
        while True:
            task_token = await websocket.receive_text()
            task_info = await deps.get_user_task(task_token, user)

            result = AsyncResult(task_info.id, app=celery_app)
            if result.ready():
                await websocket.send_json({
                    "status": result.state,
                    # "result": result.result
                })
                break
            await asyncio.sleep(1)  # Avoid busy-waiting
    except WebSocketDisconnect:
        await manager.disconnect(user.id)
    

@router.post("/cancel/", 
    response_model=APIResponse,
    responses={
        500: {
            "description": "Failed to cancel a task",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "..."
                    }
                }
            }
        },
        200: {
            "description": "Successfully cancelled a task",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Task cancelled"
                    }
                }
            }
        },
    })
async def cancel_task(
    task_data: schemas.TaskTokenPayload = Depends(deps.get_user_task)
):
    """
    Cancel a running task.

    Parameters:
        None

    Returns:
        The created user object
    
    Raises:
        400: If the task couldn't be cancelled
    """

    try:
        result = AsyncResult(task_data.id, app=celery_app)

        if not result.ready():
            result.revoke(terminate=True, signal='SIGKILL')
            return JSONResponse(
                APIResponse(
                    success=True,
                    message="Task cancelled"
                ),
                status_code=200
            )
        else:
            return JSONResponse(
                APIResponse(
                    success=False,
                    message="Cannot cancel task"
                ),
                status_code=400
            )
    except Exception:
        return JSONResponse(
            APIResponse(
                success=False,
                message="Internal error occurred"
            ),
            status_code=500
        )    