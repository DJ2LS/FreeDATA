from fastapi import APIRouter, Depends
from freedata_server.api.common import api_response, api_abort, api_ok
from freedata_server.api.command_helpers import enqueue_tx_command
from freedata_server import (
    command_cq,
    command_beacon,
    command_ping,
    command_test,
    command_fec,
    command_arq_raw,
)
from freedata_server import api_validations as validations
from freedata_server.context import AppContext, get_ctx

router = APIRouter()


@router.get(
    "/state",
    summary="Get Modem State",
    tags=["Modem"],
    responses={
        200: {
            "description": "Current modem state information.",
            "content": {
                "application/json": {
                    "example": {
                        "activities": {
                            "161dd75ef3b5847a": {
                                "activity_type": "ARQ_BURST_ACK",
                                "direction": "received",
                                "frequency": "14093000",
                                "frequency_offset": 0,
                                "session_id": 105,
                                "snr": 4,
                                "timestamp": 1713034266,
                            },
                            "168e90799d13b7b4": {
                                "activity_type": "ARQ_SESSION_INFO_ACK",
                                "direction": "received",
                                "frequency": "14093000",
                                "frequency_offset": 0,
                                "session_id": 105,
                                "snr": -3,
                                "timestamp": 1713034248,
                            },
                            "2218b849e937d36d": {
                                "activity_type": "QRV",
                                "direction": "received",
                                "frequency": "14093000",
                                "frequency_offset": 0,
                                "gridsquare": "JP15OW",
                                "origin": "SOMECALL-1",
                                "snr": 2,
                                "timestamp": 1713034200,
                            },
                            "3fb424827f4632ab": {
                                "activity_type": "BEACON",
                                "direction": "received",
                                "frequency": "14093000",
                                "frequency_offset": 0,
                                "gridsquare": "JP22AI",
                                "origin": "CALLSIGN-1",
                                "snr": -8,
                                "timestamp": 1713034455,
                            },
                            "743222d1dd64ce9d": {
                                "activity_type": "ARQ_SESSION_OPEN_ACK",
                                "direction": "received",
                                "frequency": "14093000",
                                "frequency_offset": 0,
                                "origin": "CALL-1",
                                "session_id": 105,
                                "snr": -2,
                                "timestamp": 1713034243,
                            },
                            "7589edf6bf23ceed": {
                                "activity_type": "ARQ_BURST_ACK",
                                "direction": "received",
                                "frequency": "14093000",
                                "frequency_offset": 0,
                                "session_id": 105,
                                "snr": 2,
                                "timestamp": 1713034275,
                            },
                            "9d2c5a98fe0f9894": {
                                "activity_type": "QRV",
                                "direction": "received",
                                "frequency": "14093000",
                                "frequency_offset": 0,
                                "gridsquare": "JP12AW",
                                "origin": "CALLME-1",
                                "snr": 5,
                                "timestamp": 1713034178,
                            },
                            "f85609dced4ea40a": {
                                "activity_type": "ARQ_BURST_ACK",
                                "direction": "received",
                                "frequency": "14093000",
                                "frequency_offset": 0,
                                "session_id": 105,
                                "snr": 0,
                                "timestamp": 1713034257,
                            },
                        },
                        "audio_dbfs": -7.915304862713354,
                        "channel_busy_slot": [False, False, True, False, False],
                        "is_away_from_key": False,
                        "is_beacon_running": True,
                        "is_modem_busy": False,
                        "is_modem_running": True,
                        "radio_frequency": "14093000",
                        "radio_mode": "PKTUSB",
                        "radio_status": True,
                        "s_meter_strength": "20",
                        "type": "state",
                    }
                }
            },
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Resource not found."}}},
        },
    },
)
async def get_modem_state(ctx: AppContext = Depends(get_ctx)):
    """
    Retrieve the current state of the modem.

    Returns:
        dict: A JSON object containing modem state information.
    """
    state = ctx.state_manager.sendState()
    if state is None:
        api_abort("Modem state not available", 404)
    return api_response(state)


@router.post(
    "/cqcqcq",
    summary="Send CQ Command",
    tags=["Modem"],
    responses={
        200: {
            "description": "CQ command sent successfully.",
            "content": {"application/json": {"example": {"message": "ok"}}},
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Resource not found."}}},
        },
        503: {
            "description": "Modem not running.",
            "content": {"application/json": {"example": {"error": "Modem not running."}}},
        },
    },
)
async def post_cq(ctx: AppContext = Depends(get_ctx)):
    """
    Trigger the modem to send a CQ.
    """
    if not ctx.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    await enqueue_tx_command(ctx, command_cq.CQCommand)
    return api_ok()


@router.post(
    "/beacon",
    summary="Enable/Disable Modem Beacon",
    tags=["Modem"],
    responses={
        200: {
            "description": "Beacon status updated successfully.",
            "content": {"application/json": {"example": {"enabled": True, "away_from_key": False}}},
        },
        400: {
            "description": "Invalid input parameters.",
            "content": {
                "application/json": {
                    "example": {"error": "Incorrect value for 'enabled' or 'away_from_key'. Should be bool."}
                }
            },
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Resource not found."}}},
        },
        503: {
            "description": "Modem not running.",
            "content": {"application/json": {"example": {"error": "Modem not running."}}},
        },
    },
)
async def post_beacon(
    payload: dict,
    ctx: AppContext = Depends(get_ctx),
):
    """
    Enable or disable the modem beacon.
    """
    enabled = payload.get("enabled")
    away = payload.get("away_from_key")
    if not isinstance(enabled, bool) or not isinstance(away, bool):
        api_abort("Expected booleans for 'enabled' and 'away_from_key'", 400)
    if not ctx.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    ctx.state_manager.set("is_beacon_running", enabled)
    ctx.state_manager.set("is_away_from_key", away)
    if enabled and not ctx.state_manager.getARQ():
        await enqueue_tx_command(ctx, command_beacon.BeaconCommand, payload)
    return api_response({"enabled": enabled, "away_from_key": away})


@router.post(
    "/ping_ping",
    summary="Trigger Modem to PING a Station",
    tags=["Modem"],
    responses={
        200: {
            "description": "Ping command sent successfully.",
            "content": {"application/json": {"example": {"message": True}}},
        },
        400: {
            "description": "Invalid input parameters.",
            "content": {"application/json": {"example": {"error": "Invalid 'dxcall' parameter."}}},
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Resource not found."}}},
        },
        503: {
            "description": "Modem not running.",
            "content": {"application/json": {"example": {"error": "Modem not running."}}},
        },
    },
)
async def post_ping(
    payload: dict,
    ctx: AppContext = Depends(get_ctx),
):
    """
    Trigger the modem to send a PING to a station.
    """
    if not ctx.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    dxcall = payload.get("dxcall")
    if not dxcall or not validations.validate_freedata_callsign(dxcall):
        api_abort("Invalid 'dxcall' parameter.", 400)
    await enqueue_tx_command(ctx, command_ping.PingCommand, payload)
    return api_response({"message": True})


@router.post(
    "/send_test_frame",
    summary="Send Test Frame",
    tags=["Modem"],
    responses={
        200: {
            "description": "Test frame sent successfully.",
            "content": {"application/json": {"example": {"message": "ok"}}},
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Resource not found."}}},
        },
        503: {
            "description": "Modem not running.",
            "content": {"application/json": {"example": {"error": "Modem not running."}}},
        },
    },
)
async def post_send_test(
    ctx: AppContext = Depends(get_ctx),
):
    """
    Trigger the modem to send a test frame.
    """
    if not ctx.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    await enqueue_tx_command(ctx, command_test.TestCommand)
    return api_ok()


@router.post(
    "/fec_transmit",
    summary="FEC Transmit",
    tags=["Modem"],
    responses={
        200: {
            "description": "FEC frame transmitted successfully.",
            "content": {"application/json": {"example": {"message": "FEC transmission started."}}},
        },
        400: {
            "description": "Bad Request: The request was malformed or missing required parameters.",
            "content": {"application/json": {"example": {"error": "Invalid parameters."}}},
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Resource not found."}}},
        },
        500: {
            "description": "Internal Server Error: An unexpected error occurred on the server.",
            "content": {"application/json": {"example": {"error": "Internal server error."}}},
        },
        503: {
            "description": "Modem not running.",
            "content": {"application/json": {"example": {"error": "Modem not running."}}},
        },
    },
)
async def post_fec(
    payload: dict,
    ctx: AppContext = Depends(get_ctx),
):
    """
    Trigger FEC frame transmission.
    """
    if not ctx.state_manager.is_modem_running:
        api_abort("Modem not running", 503)
    if "message" not in payload:
        api_abort("Field 'message' required.", 400)
    await enqueue_tx_command(ctx, command_fec.FecCommand, payload)
    return api_response({"message": "FEC transmission started."})


@router.post(
    "/start",
    summary="Start Modem",
    tags=["Modem"],
    responses={
        200: {
            "description": "Modem started successfully.",
            "content": {
                "application/json": {
                    "examples": {
                        "modem_started": {
                            "summary": "Modem Started",
                            "value": {"modem": "started"},
                        },
                        "message_ok": {"summary": "Message OK", "value": {"message": "ok"}},
                    }
                }
            },
        },
        400: {
            "description": "Bad Request: The request was malformed or missing required parameters.",
            "content": {"application/json": {"example": {"error": "Invalid parameters."}}},
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Resource not found."}}},
        },
        500: {
            "description": "Internal Server Error: An unexpected error occurred on the server.",
            "content": {"application/json": {"example": {"error": "Internal server error."}}},
        },
    },
)
async def post_start(ctx: AppContext = Depends(get_ctx)):
    """
    Trigger the modem to start.
    """
    if ctx.state_manager.is_modem_running:
        api_abort("Modem already running", 503)
    ctx.modem_service.put("start")
    return api_response({"modem": "started"})


@router.post(
    "/stop",
    summary="Stop Modem",
    tags=["Modem"],
    responses={
        200: {
            "description": "Modem stopped successfully.",
            "content": {
                "application/json": {
                    "examples": {
                        "modem_stopped": {
                            "summary": "Modem Stopped",
                            "value": {"modem": "stopped"},
                        },
                        "message_ok": {"summary": "Message OK", "value": {"message": "ok"}},
                    }
                }
            },
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Resource not found."}}},
        },
        503: {
            "description": "Modem not running.",
            "content": {"application/json": {"example": {"error": "Modem not running."}}},
        },
    },
)
async def post_stop(ctx: AppContext = Depends(get_ctx)):
    """
    Trigger the modem to stop.
    """
    # if not ctx.state_manager.is_modem_running:
    #    api_abort("Modem not running", 503)
    ctx.modem_service.put("stop")
    return api_response({"modem": "stopped"})


@router.post(
    "/send_arq_raw",
    summary="Send ARQ Raw Data",
    tags=["Modem"],
    responses={
        200: {
            "description": "ARQ raw data sent successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "data": "RnJlZURBVEEgaXMgdGhlIGJlc3Qh",
                        "dxcall": "XX1XXX-6",
                        "type": "raw",
                    }
                }
            },
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Resource not found."}}},
        },
        503: {
            "description": "Modem not running or busy.",
            "content": {
                "application/json": {
                    "examples": {
                        "modem_not_running": {
                            "summary": "Modem Not Running",
                            "value": {"error": "Modem not running."},
                        },
                        "modem_busy": {"summary": "Modem Busy", "value": {"error": "Modem Busy."}},
                    }
                }
            },
        },
    },
)
async def post_arq_raw(
    payload: dict,
    ctx: AppContext = Depends(get_ctx),
):
    """
    Send ARQ raw data to a specified station.
    """
    if not ctx.state_manager.is_modem_running:
        api_abort("Modem not running.", 503)
    if ctx.state_manager.is_modem_busy:
        api_abort("Modem Busy.", 503)
    dxcall = payload.get("dxcall")
    data_type = payload.get("type")
    raw_data = payload.get("data")
    if not dxcall or not validations.validate_freedata_callsign(dxcall):
        api_abort("Invalid 'dxcall' parameter.", 400)
    if data_type not in ["raw", "raw_lzma", "raw_gzip"]:
        api_abort("Invalid 'type' parameter.", 400)
    if not raw_data:
        api_abort("Missing 'data' parameter.", 400)
    await enqueue_tx_command(ctx, command_arq_raw.SendARQRawCommand, payload)
    return api_response({"data": raw_data, "dxcall": dxcall, "type": data_type})


@router.post(
    "/stop_transmission",
    summary="Stop Transmission",
    tags=["Modem"],
    responses={
        200: {
            "description": "Transmission stopped successfully.",
            "content": {"application/json": {"example": {"message": "ok"}}},
        },
        400: {
            "description": "Bad Request: The request was malformed or missing required parameters.",
            "content": {"application/json": {"example": {"error": "Invalid request."}}},
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Resource not found."}}},
        },
        500: {
            "description": "Internal Server Error: An unexpected error occurred on the server.",
            "content": {"application/json": {"example": {"error": "Internal server error."}}},
        },
        503: {
            "description": "Modem not running.",
            "content": {"application/json": {"example": {"error": "Modem not running."}}},
        },
    },
)
async def post_stop_transmission(ctx: AppContext = Depends(get_ctx)):
    """
    Stop the current transmission.
    """
    try:
        ctx.state_manager.stop_transmission()
    except Exception:
        pass
    return api_ok()
