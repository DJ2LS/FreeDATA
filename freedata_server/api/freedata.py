from fastapi import APIRouter, Depends, HTTPException

import command_norm
import command_message_send
import adif_udp_logger
import wavelog_api_logger
from context import AppContext, get_ctx
import asyncio

from freedata_server.api.common import api_response, api_abort
from freedata_server.api.command_helpers import enqueue_tx_command
from freedata_server.message_system_db_messages import DatabaseManagerMessages
from freedata_server.message_system_db_attachments import DatabaseManagerAttachments
from freedata_server.message_system_db_beacon import DatabaseManagerBeacon
from freedata_server.message_system_db_station import DatabaseManagerStations
from freedata_server.message_system_db_broadcasts import DatabaseManagerBroadcasts
from freedata_server import command_message_send
from freedata_server import adif_udp_logger
from freedata_server import wavelog_api_logger
from freedata_server.context import AppContext, get_ctx
from freedata_server.norm.norm_transmission_iss import NormTransmissionISS


router = APIRouter()


def _mgr_msgs(ctx: AppContext):
    return DatabaseManagerMessages(ctx)


def _mgr_attach(ctx: AppContext):
    return DatabaseManagerAttachments(ctx)


def _mgr_beacon(ctx: AppContext):
    return DatabaseManagerBeacon(ctx)


def _mgr_stations(ctx: AppContext):
    return DatabaseManagerStations(ctx)

def _mgr_broadcasts(ctx: AppContext):
    return DatabaseManagerBroadcasts(ctx)


@router.get(
    "/messages/{message_id}",
    summary="Get Message by ID",
    tags=["FreeDATA"],
    responses={
        200: {"description": "Message found and returned."},
        404: {"description": "Message not found."},
    },
)
async def get_freedata_message(message_id: str, ctx: AppContext = Depends(get_ctx)):
    message = _mgr_msgs(ctx).get_message_by_id_json(message_id)
    if message is None:
        api_abort("Message not found", 404)
    return api_response(message)


@router.post(
    "/messages",
    summary="Transmit Message",
    tags=["FreeDATA"],
    responses={
        200: {
            "description": "Message transmitted successfully.",
            "content": {
                "application/json": {
                    "example": {"destination": "XX1XXX-6", "body": "Hello FreeDATA"}
                }
            },
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Resource not found."}}},
        },
    },
)
async def post_freedata_message(payload: dict, ctx: AppContext = Depends(get_ctx)):
    # Transmit FreeDATA message
    await enqueue_tx_command(ctx, command_message_send.SendMessageCommand, payload)
    return api_response(payload)


@router.post(
    "/messages/{message_id}/adif",
    summary="Send Message ADIF Log",
    tags=["FreeDATA"],
    responses={
        200: {
            "description": "ADIF log sent successfully.",
            "content": {"application/json": {"example": {"adif_output": "ADIF data..."}}},
        },
        400: {
            "description": "Bad Request: The request was malformed or missing required parameters.",
            "content": {"application/json": {"example": {"error": "Invalid message ID."}}},
        },
        404: {
            "description": "The requested resource was not found.",
            "content": {"application/json": {"example": {"error": "Message not found."}}},
        },
        503: {
            "description": "Modem not running.",
            "content": {"application/json": {"example": {"error": "Modem not running."}}},
        },
    },
)
async def post_freedata_message_adif_log(message_id: str, ctx: AppContext = Depends(get_ctx)):
    adif = _mgr_msgs(ctx).get_message_by_id_adif(message_id)
    if not adif:
        api_abort("Message not found or ADIF unavailable", 404)
    # send logs
    adif_udp_logger.send_adif_qso_data(ctx, adif)
    wavelog_api_logger.send_wavelog_qso_data(ctx, adif)
    return api_response({"adif_output": adif})


@router.patch(
    "/messages/{message_id}",
    summary="Update Message by ID",
    tags=["FreeDATA"],
    responses={
        200: {
            "description": "Message updated successfully.",
            "content": {"application/json": {"example": {"is_read": True}}},
        },
        400: {
            "description": "Bad Request: The request was malformed or missing required parameters.",
            "content": {"application/json": {"example": {"error": "Invalid parameters."}}},
        },
        404: {
            "description": "Message not found.",
            "content": {"application/json": {"example": {"error": "Message not found."}}},
        },
    },
)
async def patch_freedata_message(
    message_id: str, payload: dict, ctx: AppContext = Depends(get_ctx)
):
    if payload.get("action") == "retransmit":
        _mgr_msgs(ctx).update_message(message_id, {"status": "queued"})
        _mgr_msgs(ctx).increment_message_attempts(message_id)
        result = {"message_id": message_id, "status": "queued"}
    else:
        result = _mgr_msgs(ctx).update_message(message_id, update_data=payload)
    if result is None:
        api_abort("Message not found", 404)
    return api_response(result)


@router.get(
    "/messages",
    summary="Get All Messages",
    tags=["FreeDATA"],
    responses={
        200: {
            "description": "List of all messages.",
            "content": {
                "application/json": {
                    "example": {
                        "total_messages": 1,
                        "messages": [
                            {
                                "id": "DXCALL-6_MYCALL-0_2024-04-12T20:39:05.302479",
                                "timestamp": "2024-04-12T20:39:05.302479",
                                "origin": "DXCALL-6",
                                "via": None,
                                "destination": "MYCALL-0",
                                "direction": "receive",
                                "body": "Hello !",
                                "attachments": [],
                                "status": "received",
                                "priority": 10,
                                "is_read": False,
                                "statistics": {
                                    "total_bytes": 120,
                                    "duration": 29.76698660850525,
                                    "bytes_per_minute": 241,
                                    "time_histogram": {
                                        "0": "2024-04-12T20:39:23.423169",
                                        "1": "2024-04-12T20:39:30.504638",
                                        "2": "2024-04-12T20:39:37.745075",
                                    },
                                    "snr_histogram": {"0": -6, "1": -6, "2": -6},
                                    "bpm_histogram": {"0": 198, "1": 265, "2": 252},
                                },
                            }
                        ],
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
async def get_freedata_messages(ctx: AppContext = Depends(get_ctx)):
    filters = {k: v for k, v in ctx.config_manager.read().get("FILTERS", {}).items()}
    # use query params if needed
    # filters = dict(ctx.request.query_params)
    result = _mgr_msgs(ctx).get_all_messages_json(filters=filters)
    return api_response(result)


@router.delete(
    "/messages/{message_id}",
    summary="Delete Message by ID",
    tags=["FreeDATA"],
    responses={
        200: {
            "description": "Message deleted successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "DXCALL-0_MYCALL-5_2024-04-04T17:22:14.002502 deleted",
                        "status": "success",
                    }
                }
            },
        },
        404: {
            "description": "Message not found.",
            "content": {
                "application/json": {
                    "example": {"message": "Message not found", "status": "failure"}
                }
            },
        },
    },
)
async def delete_freedata_message(message_id: str, ctx: AppContext = Depends(get_ctx)):
    ok = _mgr_msgs(ctx).delete_message(message_id)
    if not ok:
        api_abort("Message not found", 404)
    return api_response({"message": f"{message_id} deleted", "status": "success"})


@router.get(
    "/messages/{message_id}/attachments",
    summary="Get Attachments by Message ID",
    tags=["FreeDATA"],
    responses={
        200: {
            "description": "List of attachments for the specified message.",
            "content": {
                "application/json": {
                    "example": {
                        "attachments": [
                            {
                                "id": "attachment1",
                                "filename": "file1.txt",
                                "file_size": 1024,
                                "file_type": "text/plain",
                                "data_sha512": "abcdef1234567890...",
                            },
                            {
                                "id": "attachment2",
                                "filename": "image.png",
                                "file_size": 2048,
                                "file_type": "image/png",
                                "data_sha512": "123456abcdef7890...",
                            },
                        ]
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
async def get_message_attachments(message_id: str, ctx: AppContext = Depends(get_ctx)):
    attachments = _mgr_attach(ctx).get_attachments_by_message_id_json(message_id)
    return api_response({"attachments": attachments})


@router.get(
    "/messages/attachment/{data_sha512}",
    summary="Get Attachment by SHA512",
    tags=["FreeDATA"],
    responses={
        200: {
            "description": "Retrieve a specific attachment by its SHA512 hash.",
            "content": {
                "application/json": {
                    "example": {
                        "id": "attachment1",
                        "filename": "file1.txt",
                        "file_size": 1024,
                        "file_type": "text/plain",
                        "data_sha512": "abcdef1234567890...",
                    }
                }
            },
        },
        404: {
            "description": "The requested attachment was not found.",
            "content": {"application/json": {"example": {"error": "Attachment not found."}}},
        },
        503: {
            "description": "Modem not running.",
            "content": {"application/json": {"example": {"error": "Modem not running."}}},
        },
    },
)
async def get_message_attachment(data_sha512: str, ctx: AppContext = Depends(get_ctx)):
    attachment = _mgr_attach(ctx).get_attachment_by_sha512(data_sha512)
    if attachment is None:
        api_abort("Attachment not found", 404)
    return api_response(attachment)


@router.get(
    "/beacons",
    summary="Get Received Beacons",
    tags=["FreeDATA"],
    responses={
        200: {
            "description": "List of received beacons.",
            "content": {
                "application/json": {
                    "example": {
                        "total_beacons": 2,
                        "beacons": [
                            {
                                "id": "DXCALL-0_MYCALL-5_2024-04-04T17:22:14.002502",
                                "timestamp": "2024-04-04T17:22:14.002502",
                                "origin": "DXCALL-0",
                                "via": None,
                                "destination": "MYCALL-5",
                                "direction": "receive",
                                "body": "Hello FreeDATA",
                                "attachments": [],
                                "status": "received",
                                "priority": 10,
                                "is_read": False,
                                "statistics": {
                                    "total_bytes": 120,
                                    "duration": 29.77,
                                    "bytes_per_minute": 241,
                                    "time_histogram": {
                                        "0": "2024-04-04T17:22:23.423169",
                                        "1": "2024-04-04T17:22:30.504638",
                                        "2": "2024-04-04T17:22:37.745075",
                                    },
                                    "snr_histogram": {"0": -6, "1": -6, "2": -6},
                                    "bpm_histogram": {"0": 198, "1": 265, "2": 252},
                                },
                            }
                        ],
                    }
                }
            },
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
async def get_all_beacons(ctx: AppContext = Depends(get_ctx)):
    beacons = _mgr_beacon(ctx).get_all_beacons()
    return api_response(beacons)


@router.get(
    "/beacons/{callsign}",
    summary="Get Beacon by Callsign",
    tags=["FreeDATA"],
    responses={
        200: {
            "description": "List of beacons from the specified callsign.",
            "content": {
                "application/json": {
                    "example": {
                        "beacons": [
                            {
                                "id": "DXCALL-0_MYCALL-5_2024-04-04T17:22:14.002502",
                                "timestamp": "2024-04-04T17:22:14.002502",
                                "origin": "DXCALL-0",
                                "via": None,
                                "destination": "MYCALL-5",
                                "direction": "receive",
                                "body": "Hello FreeDATA",
                                "attachments": [],
                                "status": "received",
                                "priority": 10,
                                "is_read": False,
                                "statistics": {
                                    "total_bytes": 120,
                                    "duration": 29.77,
                                    "bytes_per_minute": 241,
                                    "time_histogram": {
                                        "0": "2024-04-04T17:22:23.423169",
                                        "1": "2024-04-04T17:22:30.504638",
                                        "2": "2024-04-04T17:22:37.745075",
                                    },
                                    "snr_histogram": {"0": -6, "1": -6, "2": -6},
                                    "bpm_histogram": {"0": 198, "1": 265, "2": 252},
                                },
                            }
                        ]
                    }
                }
            },
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
async def get_beacons_by_callsign(callsign: str, ctx: AppContext = Depends(get_ctx)):
    beacons = _mgr_beacon(ctx).get_beacons_by_callsign(callsign)
    return api_response(beacons)


@router.get(
    "/station/{callsign}",
    summary="Get Station Info",
    tags=["FreeDATA"],
    responses={
        200: {
            "description": "Retrieve station information by callsign.",
            "content": {
                "application/json": {
                    "example": {
                        "callsign": "MYCALL-0",
                        "location": "Springfield",
                        "frequency": "14093000",
                        "mode": "PKTUSB",
                        "status": "active",
                        "additional_info": "Station details here.",
                    }
                }
            },
        },
        400: {
            "description": "Bad Request: The request was malformed or missing required parameters.",
            "content": {"application/json": {"example": {"error": "Invalid callsign parameter."}}},
        },
        404: {
            "description": "The requested station was not found.",
            "content": {"application/json": {"example": {"error": "Station not found."}}},
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
async def get_station_info(callsign: str, ctx: AppContext = Depends(get_ctx)):
    station = _mgr_stations(ctx).get_station(callsign)
    if station is None:
        api_abort("Station not found", 404)
    return api_response(station)


@router.post(
    "/station/{callsign}",
    summary="Set Station Info",
    tags=["FreeDATA"],
    responses={
        200: {
            "description": "Station information updated successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "callsign": "MYCALL-0",
                        "location": "Springfield",
                        "frequency": "14093000",
                        "mode": "PKTUSB",
                        "status": "active",
                        "additional_info": "Updated station details.",
                    }
                }
            },
        },
        400: {
            "description": "Bad Request: The request was malformed or missing required parameters.",
            "content": {"application/json": {"example": {"error": "Invalid input data."}}},
        },
        404: {
            "description": "The requested station was not found.",
            "content": {"application/json": {"example": {"error": "Station not found."}}},
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
async def set_station_info(callsign: str, payload: dict, ctx: AppContext = Depends(get_ctx)):
    info = payload.get("info")
    if not isinstance(info, dict):
        api_abort("Invalid input data", 400)
    result = _mgr_stations(ctx).update_station_info(callsign, new_info=info)
    if result is None:
        api_abort("Station not found", 404)
    return api_response(result)


@router.get("/broadcasts", summary="Get All Broadcast Messages", tags=["FreeDATA"], responses={})
async def get_freedata_broadcasts(
    ctx: AppContext = Depends(get_ctx)
):
    #filters = {k: v for k, v in ctx.config_manager.read().get('FILTERS', {}).items()}
    # use query params if needed
    # filters = dict(ctx.request.query_params)
    result = _mgr_broadcasts(ctx).get_all_broadcasts_json()
    return api_response(result)

@router.get("/broadcasts/{domain}/", summary="Get Broadcats per Domain", tags=["FreeDATA"], responses={})
async def get_freedata_broadcasts_per_domain(
    domain: str,
    ctx: AppContext = Depends(get_ctx)
):
    result = _mgr_broadcasts(ctx).get_broadcasts_per_domain_json(domain)
    return api_response(result)


@router.get("/broadcasts/domains", summary="Get All Broadcast Messages", tags=["FreeDATA"], responses={})
async def get_freedata_broadcasts(
    ctx: AppContext = Depends(get_ctx)
):
    #filters = {k: v for k, v in ctx.config_manager.read().get('FILTERS', {}).items()}
    # use query params if needed
    # filters = dict(ctx.request.query_params)
    result = _mgr_broadcasts(ctx).get_broadcast_domains_json()
    return api_response(result)


@router.delete("/broadcasts/{id}", summary="Delete Message or Broadcast by ID", tags=["FreeDATA"], responses={})
async def delete_freedata_broadcast_domain(
    id: str,
    ctx: AppContext = Depends(get_ctx)
):
    ok = _mgr_broadcasts(ctx).delete_broadcast_message_or_domain(id)
    if not ok:
        api_abort("Message not found", 404)
    return api_response({"message": f"{id} deleted", "status": "success"})



@router.patch("/broadcasts/{id}", summary="Retransmit Broadcast by ID", tags=["FreeDATA"], responses={})
async def patch_freedata_broadcast_domain(
    id: str,
    payload: dict,
    ctx: AppContext = Depends(get_ctx)
):
    if payload.get("action") == "retransmit":
        _mgr_broadcasts(ctx).increment_attempts(id)
        msg = _mgr_broadcasts(ctx).get_broadcast_per_id(id, get_object=True)
        if msg:
            loop = asyncio.get_running_loop()
            loop.run_in_executor(
                None,
                NormTransmissionISS(ctx).retransmit_data,
                msg
            )
            return api_response({"message_id": id, "status": "retransmit started"})
        else:
            api_abort("Message not found", 404)

    api_abort("Invalid action", 400)


@router.post("/broadcasts", summary="Transmit Broadcast", tags=["FreeDATA"], responses={})
async def post_freedata_broadcast(
    payload: dict,
    ctx: AppContext = Depends(get_ctx)
):
    await enqueue_tx_command(ctx, command_norm.Norm, payload)
    return api_response({"message": f"broadcast transmitted", "status": "success"})
