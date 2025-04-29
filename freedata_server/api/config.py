from fastapi import APIRouter, Request, Depends
from api.common import api_response, api_abort, api_ok, validate
import api_validations as validations
from context import AppContext, get_ctx
router = APIRouter()

@router.get("/", summary="Get Modem Configuration", tags=["Configuration"], responses={
    200: {
        "description": "Current modem configuration settings.",
        "content": {
            "application/json": {
                "example": {
                    "AUDIO": {
                        "input_device": "2fc0",
                        "output_device": "3655",
                        "rx_audio_level": 0,
                        "tx_audio_level": 2
                    },
                    "MESSAGES": {
                        "enable_auto_repeat": True
                    },
                    "MODEM": {
                        "enable_morse_identifier": False,
                        "enable_socket_interface": False,
                        "maximum_bandwidth": 2438,
                        "tx_delay": 200
                    },
                    "NETWORK": {
                        "modemaddress": "",
                        "modemport": 5000
                    },
                    "RADIO": {
                        "control": "rigctld",
                        "data_bits": 8,
                        "model_id": 1001,
                        "ptt_port": "ignore",
                        "ptt_type": "USB",
                        "serial_dcd": "NONE",
                        "serial_dtr": "OFF",
                        "serial_handshake": "ignore",
                        "serial_port": "/dev/cu.Bluetooth-Incoming-Port",
                        "serial_speed": 38400,
                        "stop_bits": 1
                    },
                    "RIGCTLD": {
                        "arguments": "",
                        "command": "",
                        "ip": "127.0.0.1",
                        "path": "",
                        "port": 4532
                    },
                    "SOCKET_INTERFACE": {
                        "cmd_port": 0,
                        "data_port": 0,
                        "enable": False,
                        "host": ""
                    },
                    "STATION": {
                        "enable_explorer": True,
                        "enable_stats": True,
                        "mycall": "LA3QMA",
                        "mygrid": "JP20ql",
                        "myssid": 0,
                        "ssid_list": [0,1,2,3,4,5,6,7,8,9],
                        "respond_to_cq": True,
                    }
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    }
})
async def get_config(ctx: AppContext = Depends(get_ctx)):
    """
    Retrieve the current modem configuration.

    Returns:
        dict: The modem configuration settings.
    """
    cfg = ctx.config_manager.config
    if cfg is None:
        api_abort("Configuration not found", 404)
    return cfg


@router.post("/", summary="Update Modem Configuration", tags=["Configuration"], responses={
    200: {
        "description": "Modem configuration updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "AUDIO": {
                        "input_device": "2fc0",
                        "output_device": "3655",
                        "rx_audio_level": 0,
                        "tx_audio_level": 2
                    },
                    # ...
                }
            }
        }
    },
    400: {
        "description": "Invalid configuration data.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Invalid config"
                }
            }
        }
    },
    500: {
        "description": "Error writing configuration.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Error writing config"
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    }
})
async def post_config(
    new_cfg: dict,
    ctx: AppContext = Depends(get_ctx),
):
    """
    Update the modem configuration with new settings.

    Parameters:
        new_cfg (dict): The new configuration payload.
        ctx (AppContext): Injected application context.

    Returns:
        dict: The updated modem configuration.

    Raises:
        HTTPException via api_abort on validation or write errors.
    """
    # Validate incoming data
    if not validations.validate_remote_config(new_cfg):
        api_abort("Invalid configuration", 400)

    # Read and compare
    old_cfg = ctx.config_manager.read()
    if old_cfg == new_cfg:
        return old_cfg

    # Write new config
    if not ctx.config_manager.write(new_cfg):
        api_abort("Error writing configuration", 500)

    # Trigger modem restart
    ctx.modem_service.put("restart")

    # Return updated configuration
    updated = ctx.config_manager.read()
    return updated