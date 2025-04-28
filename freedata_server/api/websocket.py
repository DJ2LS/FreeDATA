from fastapi import APIRouter, Request, WebSocket
router = APIRouter()

# WebSocket Event Handlers
@router.websocket("/events")
async def websocket_events(websocket: WebSocket):
    await websocket.accept()
    await websocket.app.ctx.wsm.handle_connection(websocket, websocket.app.ctx.wsm.events_client_list, websocket.app.ctx.modem_events)

@router.websocket("/fft")
async def websocket_fft(websocket: WebSocket):
    await websocket.accept()
    await websocket.app.ctx.wsm.handle_connection(websocket, websocket.app.ctx.wsm.fft_client_list, websocket.app.ctx.modem_fft)

@router.websocket("/states")
async def websocket_states(websocket: WebSocket):
    await websocket.accept()
    await websocket.app.ctx.wsm.handle_connection(websocket, websocket.app.ctx.wsm.states_client_list, websocket.app.ctx.state_queue)
