from fastapi import APIRouter, Depends
from freedata_server.api.common import api_response, api_abort
from freedata_server.api.command_helpers import enqueue_tx_command
from freedata_server import command_transmit_sine
from freedata_server.context import AppContext, get_ctx

router = APIRouter()


@router.get(
    "/",
    summary="Get Radio Parameters",
    tags=["Radio"],
    responses={
        200: {
            "description": "Current radio parameters.",
            "content": {
                "application/json": {
                    "example": {
                        "radio_frequency": "14093000",
                        "radio_mode": "PKTUSB",
                        "radio_rf_level": 100,
                        "radio_status": True,
                        "radio_swr": 0,
                        "radio_tuner": False,
                        "s_meter_strength": "20",
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
async def get_radio(ctx: AppContext = Depends(get_ctx)):
    """
    Retrieve current radio parameters.

    Returns:
        dict: The current radio parameters.
    """
    params = ctx.state_manager.get_radio_status()
    if params is None:
        api_abort("Radio parameters not found", 404)
    return api_response(params)


@router.post(
    "/",
    summary="Set Radio Parameters",
    tags=["Radio"],
    responses={
        200: {
            "description": "Radio parameters updated successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "radio_frequency": "14093000",
                        "radio_mode": "PKTUSB",
                        "radio_rf_level": 100,
                        "radio_status": True,
                        "radio_swr": 0,
                        "radio_tuner": True,
                        "s_meter_strength": "20",
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
    },
)
async def post_radio(
    new_params: dict,
    ctx: AppContext = Depends(get_ctx),
):
    """
    Set radio parameters: frequency, mode, RF level, tuner state.

    Parameters:
        new_params (dict): The radio parameters to set.
        ctx (AppContext): Injected application context.

    Returns:
        dict: The applied radio parameters.
    """
    radio_manager = ctx.radio_manager
    if "radio_frequency" in new_params:
        radio_manager.set_frequency(new_params["radio_frequency"])
    if "radio_mode" in new_params:
        radio_manager.set_mode(new_params["radio_mode"])
    if "radio_rf_level" in new_params:
        radio_manager.set_rf_level(int(new_params["radio_rf_level"]))
    if "radio_tuner" in new_params:
        radio_manager.set_tuner(new_params["radio_tuner"])
    return api_response(new_params)


@router.post(
    "/tune",
    summary="Enable/Disable Radio Tuning",
    tags=["Radio"],
    responses={
        200: {
            "description": "Radio tuning status updated successfully.",
            "content": {"application/json": {"example": {"enable_tuning": True}}},
        },
        400: {
            "description": "Bad Request: The request was malformed or missing required parameters.",
            "content": {"application/json": {"example": {"error": "Invalid parameters."}}},
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
async def post_radio_tune(
    params: dict,
    ctx: AppContext = Depends(get_ctx),
):
    """
    Enable or disable radio tuning tone.

    Parameters:
        params (dict): {'enable_tuning': bool}
        ctx (AppContext): Injected application context.

    Raises:
        HTTPException via api_abort if modem not running or busy.
    """
    enable = params.get("enable_tuning")
    if enable:
        if not ctx.state_manager.is_modem_running:
            api_abort("Modem not running", 503)
        await enqueue_tx_command(ctx, command_transmit_sine.TransmitSine)
    else:
        ctx.rf_modem.stop_sine()
    return api_response(params)
