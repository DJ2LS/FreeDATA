#!/usr/bin/env python
# encoding: utf-8
import structlog
import ujson as json
log = structlog.get_logger("REST")

from global_instances import ARQ, AudioParam, HamlibParam, ModemParam, Station, TCIParam, Modem, MeshParam
encoding = "utf-8"


def get_running_config():
    # get running config
    try:
        dict_running_config = {
            "AUDIO":
                {
                    "auto_tune":AudioParam.audio_auto_tune,
                    "rx":AudioParam.audio_input_device,
                    "rxaudiolevel":AudioParam.rx_audio_level,
                    "tx":AudioParam.audio_output_device,
                    "txaudiolevel":AudioParam.tx_audio_level
                },
            "MESH":
                {
                    "enable_protocol":MeshParam.enable_protocol
                },
            "Modem":
                {
                    "explorer":Modem.enable_explorer,
                    "fft":AudioParam.enable_fft,
                    "fmax":ModemParam.tuning_range_fmax,
                    "fmin":ModemParam.tuning_range_fmin,
                    "fsk":Modem.enable_fsk,
                    "narrowband":Modem.low_bandwidth_mode,
                    "qrv":Modem.respond_to_cq,
                    "rx_buffer_size":ARQ.rx_buffer_size,
                    "scatter":ModemParam.enable_scatter,
                    "stats": Modem.enable_stats,
                    "transmit_morse_identifier":Modem.transmit_morse_identifier,
                    "tx_delay":ModemParam.tx_delay
                },
            "NETWORK":
                {
                    "modemport":Modem.port
                },
            "RADIO":{
                "radiocontrol":HamlibParam.hamlib_radiocontrol,
                "rigctld_ip":HamlibParam.hamlib_rigctld_ip,
                "rigctld_port":HamlibParam.hamlib_rigctld_port
            },
            "STATION":
                {
                    "mycall": str(Station.mycallsign, encoding),
                    "mygrid": str(Station.mygrid, encoding),
                    "ssid_list": json.dumps(Station.ssid_list),
                },
            "TCI":
                {
                    "ip": TCIParam.ip,
                    "port": TCIParam.port
                }
        }

        return dict_running_config
    except Exception as e:
        log.warning("[REST] error while processing running config", e=e)