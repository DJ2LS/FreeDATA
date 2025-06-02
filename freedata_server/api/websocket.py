from fastapi import APIRouter, WebSocket, Depends
from context import AppContext, get_ctx

router = APIRouter()

@router.websocket("/events")
async def websocket_events(
    websocket: WebSocket,
    ctx: AppContext = Depends(get_ctx)
):
    """
    WebSocket endpoint for event streams.
    """
    await websocket.accept()
    await ctx.websocket_manager.handle_connection(
        websocket,
        ctx.websocket_manager.events_client_list,
        ctx.modem_events
    )

@router.websocket("/fft")
async def websocket_fft(
    websocket: WebSocket,
    ctx: AppContext = Depends(get_ctx)
):
    """
    WebSocket endpoint for FFT data streams.
    """
    await websocket.accept()
    await ctx.websocket_manager.handle_connection(
        websocket,
        ctx.websocket_manager.fft_client_list,
        ctx.modem_fft
    )

@router.websocket("/states")
async def websocket_states(
    websocket: WebSocket,
    ctx: AppContext = Depends(get_ctx)
):
    """
    WebSocket endpoint for state updates.
    """
    await websocket.accept()
    await ctx.websocket_manager.handle_connection(
        websocket,
        ctx.websocket_manager.states_client_list,
        ctx.state_queue
    )

@router.websocket("/audio_rx")
async def websocket_audio_rx(
    websocket: WebSocket,
    ctx: AppContext = Depends(get_ctx)
):
    """
    WebSocket endpoint for state updates.
    """
    await websocket.accept()
    await ctx.websocket_manager.handle_connection(
        websocket,
        ctx.websocket_manager.audio_rx_client_list,
        ctx.state_queue
    )
    #while True:
    #    await websocket.send_bytes(b"\x00" * 1024)
