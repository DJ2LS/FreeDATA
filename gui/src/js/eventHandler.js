import { addDataToWaterfall } from "../js/waterfallHandler.js";

import {
  newMessageReceived,
  newBeaconReceived,
  updateTransmissionStatus,
  setStateSuccess,
  setStateFailed,
} from "./chatHandler";
import { displayToast } from "./popupHandler";

// ----------------- init pinia stores -------------
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import { useStateStore } from "../store/stateStore.js";
const stateStore = useStateStore(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

export function eventDispatcher(data) {
  data = JSON.parse(data);

  // get ptt state as a first test
  // Todo we might use a switch function for data dispatching
  stateStore.ptt_state = data.ptt;



    // copied directly from sock.js We need to implement these variables step by step
  if (data["command"] == "modem_state") {
    //console.log(data)

    stateStore.rx_buffer_length = data["rx_buffer_length"];
    stateStore.frequency = data["frequency"];
    stateStore.busy_state = data["modem_state"];
    stateStore.arq_state = data["arq_state"];
    stateStore.mode = data["mode"];
    stateStore.bandwidth = data["bandwidth"];
    stateStore.tx_audio_level = data["tx_audio_level"];
    stateStore.rx_audio_level = data["rx_audio_level"];
    // if audio level is different from config one, send new audio level to modem
    //console.log(parseInt(stateStore.tx_audio_level))
    //console.log(parseInt(settings.tx_audio_level))
    if (
      parseInt(stateStore.tx_audio_level) !==
        parseInt(settings.tx_audio_level) &&
      setTxAudioLevelOnce === true
    ) {
      setTxAudioLevelOnce = false;
      console.log(setTxAudioLevelOnce);
      setTxAudioLevel(settings.tx_audio_level);
    }

    if (
      parseInt(stateStore.rx_audio_level) !==
        parseInt(settings.rx_audio_level) &&
      setRxAudioLevelOnce === true
    ) {
      setRxAudioLevelOnce = false;
      console.log(setRxAudioLevelOnce);
      setRxAudioLevel(settings.rx_audio_level);
    }

    stateStore.dbfs_level = data["audio_dbfs"];
    stateStore.ptt_state = data["ptt_state"];
    stateStore.speed_level = data["speed_level"];
    stateStore.fft = JSON.parse(data["fft"]);
    stateStore.channel_busy = data["channel_busy"];
    stateStore.channel_busy_slot = data["channel_busy_slot"];

    addDataToWaterfall(JSON.parse(data["fft"]));

    if (data["scatter"].length > 0) {
      stateStore.scatter = data["scatter"];
    }
    // s meter strength
    stateStore.s_meter_strength_raw = data["strength"];
    if (stateStore.s_meter_strength_raw == "") {
      stateStore.s_meter_strength_raw = "Unsupported";
      stateStore.s_meter_strength_percent = 0;
    } else {
      // https://www.moellerstudios.org/converting-amplitude-representations/
      stateStore.s_meter_strength_percent = Math.round(
        Math.pow(10, stateStore.s_meter_strength_raw / 20) * 100,
      );
    }

    stateStore.dbfs_level_percent = Math.round(
      Math.pow(10, stateStore.dbfs_level / 20) * 100,
    );
    stateStore.dbfs_level = Math.round(stateStore.dbfs_level);

    stateStore.arq_total_bytes = data["total_bytes"];
    stateStore.heard_stations = data["stations"].sort(
      sortByPropertyDesc("timestamp"),
    );
    stateStore.dxcallsign = data["dxcallsign"];

    stateStore.beacon_state = data["beacon_state"];
    stateStore.audio_recording = data["audio_recording"];

    stateStore.hamlib_status = data["hamlib_status"];
    stateStore.alc = data["alc"];
    stateStore.rf_level = data["rf_level"];

    stateStore.is_codec2_traffic = data["is_codec2_traffic"];

    stateStore.arq_session_state = data["arq_session"];
    stateStore.arq_state = data["arq_state"];
    stateStore.arq_transmission_percent = data["arq_transmission_percent"];
    stateStore.arq_seconds_until_finish = data["arq_seconds_until_finish"];
    stateStore.arq_seconds_until_timeout = data["arq_seconds_until_timeout"];
    stateStore.arq_seconds_until_timeout_percent =
      (stateStore.arq_seconds_until_timeout / 180) * 100;

    if (data["speed_list"].length > 0) {
      prepareStatsDataForStore(data["speed_list"]);
    }

    // TODO: Remove ported objects
    /*
        let Data = {
          mycallsign: data["mycallsign"],
          mygrid: data["mygrid"],
          //channel_state: data['CHANNEL_STATE'],

          info: data["info"],
          rx_msg_buffer_length: data["rx_msg_buffer_length"],
          tx_n_max_retries: data["tx_n_max_retries"],
          arq_tx_n_frames_per_burst: data["arq_tx_n_frames_per_burst"],
          arq_tx_n_bursts: data["arq_tx_n_bursts"],
          arq_tx_n_current_arq_frame: data["arq_tx_n_current_arq_frame"],
          arq_tx_n_total_arq_frames: data["arq_tx_n_total_arq_frames"],
          arq_rx_frame_n_bursts: data["arq_rx_frame_n_bursts"],
          arq_rx_n_current_arq_frame: data["arq_rx_n_current_arq_frame"],
          arq_n_arq_frames_per_data_frame:
          data["arq_n_arq_frames_per_data_frame"],
          arq_bytes_per_minute: data["arq_bytes_per_minute"],
          arq_compression_factor: data["arq_compression_factor"],
          routing_table: data["routing_table"],
          mesh_signalling_table: data["mesh_signalling_table"],
          listen: data["listen"],
          //speed_table: [{"bpm" : 5200, "snr": -3, "timestamp":1673555399},{"bpm" : 2315, "snr": 12, "timestamp":1673555500}],
        };
        */
  }

  var message = "";
  if (data["freedata"] == "modem-message") {
    // break early if we received a dummy callsign
    // thats a kind of hotfix, as long as the modem isnt handling this better
    if (data["dxcallsign"] == "AA0AA-0" || data["dxcallsign"] == "ZZ9YY-0") {
      return;
    }

    console.log(data);

    switch (data["fec"]) {
      case "is_writing":
        // RX'd FECiswriting
        break;

      case "broadcast":
        // RX'd FEC BROADCAST
        var encoded_data = atob_FD(data["data"]);
        var splitted_data = encoded_data.split(split_char);
        var messageArray = [];
        if (splitted_data[0] == "m") {
          messageArray.push(data);
          console.log(data);
        }
        break;
    }

    switch (data["cq"]) {
      case "transmitting":
        // CQ TRANSMITTING
        displayToast("success", "bi-arrow-left-right", "Transmitting CQ", 5000);
        break;

      case "received":
        // CQ RECEIVED
        message = "CQ from " + data["dxcallsign"];
        displayToast("success", "bi-person-arms-up", message, 5000);
        break;
    }

    switch (data["qrv"]) {
      case "transmitting":
        // QRV TRANSMITTING
        displayToast(
          "info",
          "bi-person-raised-hand",
          "Transmitting QRV ",
          5000,
        );
        break;

      case "received":
        // QRV RECEIVED
        message = "QRV from " + data["dxcallsign"] + " | " + data["dxgrid"];
        displayToast("success", "bi-person-raised-hand", message, 5000);
        break;
    }

    switch (data["beacon"]) {
      case "transmitting":
        // BEACON TRANSMITTING
        displayToast(
          "success",
          "bi-broadcast-pin",
          "Transmitting beacon",
          5000,
        );
        break;

      case "received":
        // BEACON RECEIVED
        newBeaconReceived(data);

        message = "Beacon from " + data["dxcallsign"] + " | " + data["dxgrid"];
        displayToast("info", "bi-broadcast", message, 5000);
        break;
    }

    switch (data["ping"]) {
      case "transmitting":
        // PING TRANSMITTING
        message = "Sending ping to " + data["dxcallsign"];
        displayToast("success", "bi-arrow-right", message, 5000);
        break;

      case "received":
        // PING RECEIVED
        message =
          "Ping request from " + data["dxcallsign"] + " | " + data["dxgrid"];
        displayToast("success", "bi-arrow-right-short", message, 5000);
        break;

      case "acknowledge":
        // PING ACKNOWLEDGE
        message =
          "Received ping-ack from " +
          data["dxcallsign"] +
          " | " +
          data["dxgrid"];
        displayToast("success", "bi-arrow-left-right", message, 5000);
        break;
    }

    // ARQ SESSION && freedata == modem-message
    if (data["arq"] == "session") {
      switch (data["status"]) {
        case "connecting":
          // ARQ Open
          break;

        case "connected":
          // ARQ Opening
          break;

        case "waiting":
          // ARQ Opening
          break;

        case "close":
          // ARQ Closing
          break;

        case "failed":
          // ARQ Failed
          break;
      }
    }
    // ARQ TRANSMISSION && freedata == modem-message
    if (data["arq"] == "transmission") {
      switch (data["status"]) {
        case "opened":
          // ARQ Open
          message = "ARQ session opened: " + data["dxcallsign"];
          displayToast("success", "bi-arrow-left-right", message, 5000);
          break;

        case "opening":
          // ARQ Opening IRS/ISS
          if (data["irs"] == "False") {
            message = "ARQ session opening: " + data["dxcallsign"];
            displayToast("info", "bi-arrow-left-right", message, 5000);
            break;
          } else {
            message = "ARQ sesson request from: " + data["dxcallsign"];
            displayToast("success", "bi-arrow-left-right", message, 5000);
            break;
          }

        case "waiting":
          // ARQ waiting
          message = "Channel busy | ARQ protocol is waiting";
          displayToast("warning", "bi-hourglass-split", message, 5000);
          break;

        case "receiving":
          // ARQ RX
          break;

        case "failed":
          // ARQ TX Failed
          if (data["reason"] == "protocol version missmatch") {
            message = "Protocol version mismatch!";
            displayToast("danger", "bi-chevron-bar-expand", message, 5000);
            setStateFailed();

            break;
          } else {
            message = "Transmission failed";
            displayToast("danger", "bi-x-octagon", message, 5000);
            updateTransmissionStatus(data);
            setStateFailed();
            break;
          }
          switch (data["irs"]) {
            case "True":
              updateTransmissionStatus(data);

              break;
            default:
              updateTransmissionStatus(data);
              break;
          }
          break;

        case "received":
          // ARQ data received

          console.log(data);
          // we need to encode here to do a deep check for checking if file or message
          //var encoded_data = atob(data['data'])
          var encoded_data = atob_FD(data["data"]);
          var splitted_data = encoded_data.split(split_char);

          // new message received
          if (splitted_data[0] == "m") {
            console.log(splitted_data);
            newMessageReceived(splitted_data, data);
          }

          break;

        case "transmitting":
          // ARQ transmitting
          updateTransmissionStatus(data);
          break;

        case "transmitted":
          // ARQ transmitted
          message = "Data transmitted";
          displayToast("success", "bi-check-sqaure", message, 5000);
          updateTransmissionStatus(data);
          setStateSuccess();

          break;
      }
    }
  }
}
