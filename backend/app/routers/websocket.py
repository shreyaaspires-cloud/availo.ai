import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from app.services.auth_service import decode_token
from app.services.connection_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...),
):
    try:
        payload = decode_token(token)
        token_sub = payload.get("sub")
        if not token_sub or token_sub != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await connection_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)
    except Exception as e:
        logger.error("WS error: %s", e)
        connection_manager.disconnect(user_id)
