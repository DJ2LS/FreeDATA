from fastapi import APIRouter, Depends
import platform
from context import AppContext, get_ctx

router = APIRouter()


@router.get(
    "/",
    summary="API Root",
    tags=["General"],
    responses={
        200: {"description": "API information."},
        404: {"description": "Resource not found."},
        503: {"description": "Service unavailable."},
    },
)
async def index(ctx: AppContext = Depends(get_ctx)):
    """
    Retrieve API metadata.

    Returns:
        dict: A JSON object containing API metadata.
    """
    return {
        "name": "FreeDATA API",
        "description": "A sample API that provides free data services",
        "api_version": ctx.constants.API_VERSION,
        "modem_version": ctx.constants.MODEM_VERSION,
        "license": ctx.constants.LICENSE,
        "documentation": ctx.constants.DOCUMENTATION_URL,
    }


@router.get(
    "/version",
    summary="Get Modem Version",
    tags=["General"],
    responses={
        200: {"description": "Successful Response."},
    },
)
async def get_modem_version(ctx: AppContext = Depends(get_ctx)):
    """
    Retrieve the modem version, API version, OS information, and Python information.

    Returns:
        dict: A JSON object containing version information.
    """
    os_info = {
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }

    python_info = {
        "build": platform.python_build(),
        "compiler": platform.python_compiler(),
        "implementation": platform.python_implementation(),
        "version": platform.python_version(),
    }

    return {
        "api_version": ctx.constants.API_VERSION,
        "modem_version": ctx.constants.MODEM_VERSION,
        "os_info": os_info,
        "python_info": python_info,
    }
