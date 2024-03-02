/*
import {
  newMessageReceived,
  newBeaconReceived,
  updateTransmissionStatus,
  setStateSuccess,
  setStateFailed,
} from "./chatHandler";
*/
import { displayToast } from "./popupHandler";
import {
  getFreedataMessages,
  getModemState,
} from "./api";
import { processFreedataMessages } from "./messagesHandler.ts";
import { processRadioStatus } from "./radioHandler.ts";
import { loadAudioDevices, loadSerialDevices } from "./deviceFormHelper.ts";


// ----------------- init pinia stores -------------
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import { useStateStore } from "../store/stateStore.js";
const stateStore = useStateStore(pinia);

import {
  settingsStore as settings,
  getRemote,
} from "../store/settingsStore.js";

export function connectionFailed(endpoint, event) {
  stateStore.modem_connection = "disconnected";
}
export function stateDispatcher(data) {
  data = JSON.parse(data);
  //Leave commented when not needed, otherwise can lead to heap overflows due to the amount of data logged
  //console.debug(data);
  if (data["type"] == "state-change" || data["type"] == "state") {
    stateStore.modem_connection = "connected";

    stateStore.busy_state = data["is_modem_busy"];

    stateStore.channel_busy = data["channel_busy"];
    stateStore.is_codec2_traffic = data["is_codec2_traffic"];
    stateStore.is_modem_running = data["is_modem_running"];
    stateStore.dbfs_level = Math.round(data["audio_dbfs"]);
    stateStore.dbfs_level_percent = Math.round(
      Math.pow(10, data["audio_dbfs"] / 20) * 100,
    );

    stateStore.s_meter_strength_raw = Math.round(data["s_meter_strength"]);
    stateStore.s_meter_strength_percent = Math.round(
      Math.pow(10, data["s_meter_strength"] / 20) * 100,
    );

    stateStore.channel_busy_slot = data["channel_busy_slot"];
    stateStore.beacon_state = data["is_beacon_running"];
    stateStore.radio_status = data["radio_status"];
    stateStore.frequency = data["radio_frequency"];
    stateStore.mode = data["radio_mode"];
    //Reverse entries so most recent is first
    stateStore.activities = Object.entries(data["activities"]).reverse();
    build_HSL();
  }
}

export function eventDispatcher(data) {
  data = JSON.parse(data);
  console.debug(data);

  if (data["scatter"] !== undefined) {
    stateStore.scatter = JSON.parse(data["scatter"]);
    return;
  }

  switch (data["message-db"]) {
    case "changed":
      console.log("fetching new messages...");
      var messages = getFreedataMessages();
      processFreedataMessages(messages);
      return;
  }

  switch (data["ptt"]) {
    case true:
    case false:
      // get ptt state as a first test
      //console.warn("PTT state true")
      stateStore.ptt_state = data.ptt;
      return;
  }

  switch (data["modem"]) {
    case "started":
      displayToast("success", "bi-arrow-left-right", "Modem started", 5000);
      getModemState();
      getRemote();
      loadAudioDevices();
      loadSerialDevices();
      getFreedataMessages();
      processRadioStatus();
      return;

    case "stopped":
      displayToast("warning", "bi-arrow-left-right", "Modem stopped", 5000);
      return;

    case "restarted":
      displayToast("secondary", "bi-bootstrap-reboot", "Modem restarted", 5000);
      getModemState();
      getRemote();
      loadAudioDevices();
      loadSerialDevices();
      getFreedataMessages();
      processRadioStatus();
      return;

    case "failed":
      displayToast(
        "danger",
        "bi-bootstrap-reboot",
        "Modem startup failed | bad config?",
        5000,
      );
      return;
  }

  var message = "";

  switch (data["type"]) {
    case "hello-client":
      message = "Connected to server";
      displayToast("success", "bi-ethernet", message, 5000);
      stateStore.modem_connection = "connected";

      getRemote().then(() => {
        //initConnections();
        getModemState();
      });

      //getRemote();
      getModemState();
      getOverallHealth();
      loadAudioDevices();
      loadSerialDevices();
      getFreedataMessages();
      processFreedataMessages();
      processRadioStatus();

      return;

      switch (data["received"]) {
        case "PING":
          message = `Ping request from: ${data.dxcallsign}, SNR: ${data.snr}`;
          displayToast("success", "bi-check-circle", message, 5000);
          return;

        case "PING_ACK":
          message = `Ping acknowledged from: ${data.dxcallsign}, SNR: ${data.snr}`;
          displayToast("success", "bi-check-circle", message, 5000);
          return;
      }

    case "arq":
      if (data["arq-transfer-outbound"]) {
        switch (data["arq-transfer-outbound"].state) {
          case "NEW":
            message = `Type: ${data.type}, Session ID: ${data["arq-transfer-outbound"].session_id}, DXCall: ${data["arq-transfer-outbound"].dxcall}, Total Bytes: ${data["arq-transfer-outbound"].total_bytes}, State: ${data["arq-transfer-outbound"].state}`;
            displayToast("success", "bi-check-circle", message, 5000);
            stateStore.dxcallsign = data["arq-transfer-outbound"].dxcall;
            stateStore.arq_transmission_percent = 0;
            stateStore.arq_total_bytes = 0;
            return;
          case "OPEN_SENT":
            console.info("state OPEN_SENT needs to be implemented");
            return;

          case "INFO_SENT":
            console.info("state INFO_SENT needs to be implemented");
            return;

          case "BURST_SENT":
            message = `Type: ${data.type}, Session ID: ${data["arq-transfer-outbound"].session_id}, DXCall: ${data["arq-transfer-outbound"].dxcall}, Received Bytes: ${data["arq-transfer-outbound"].received_bytes}/${data["arq-transfer-outbound"].total_bytes}, State: ${data["arq-transfer-outbound"].state}`;
            displayToast("info", "bi-info-circle", message, 5000);
            stateStore.arq_transmission_percent =
              (data["arq-transfer-outbound"].received_bytes /
                data["arq-transfer-outbound"].total_bytes) *
              100;
            stateStore.arq_total_bytes =
              data["arq-transfer-outbound"].received_bytes;
            stateStore.arq_speed_list_timestamp =
              data["arq-transfer-outbound"].statistics.time_histogram;
            stateStore.arq_speed_list_bpm =
              data["arq-transfer-outbound"].statistics.bpm_histogram;
            stateStore.arq_speed_list_snr =
              data["arq-transfer-outbound"].statistics.snr_histogram;
            return;

          case "ABORTING":
            console.info("state ABORTING needs to be implemented");
            return;

          case "ABORTED":
            message = `Type: ${data.type}, Session ID: ${
              data["arq-transfer-outbound"].session_id
            }, DXCall: ${data["arq-transfer-outbound"].dxcall}, Total Bytes: ${
              data["arq-transfer-outbound"].total_bytes
            }, Success: ${
              data["arq-transfer-outbound"].success ? "Yes" : "No"
            }, State: ${data["arq-transfer-outbound"].state}, Data: ${
              data["arq-transfer-outbound"].data ? "Available" : "Not Available"
            }`;
            displayToast("warning", "bi-exclamation-triangle", message, 5000);
            return;

          case "FAILED":
            message = `Type: ${data.type}, Session ID: ${
              data["arq-transfer-outbound"].session_id
            }, DXCall: ${data["arq-transfer-outbound"].dxcall}, Total Bytes: ${
              data["arq-transfer-outbound"].total_bytes
            }, Success: ${
              data["arq-transfer-outbound"].success ? "Yes" : "No"
            }, State: ${data["arq-transfer-outbound"].state}, Data: ${
              data["arq-transfer-outbound"].data ? "Available" : "Not Available"
            }`;
            displayToast("danger", "bi-x-octagon", message, 5000);
            return;
        }
      }

      if (data["arq-transfer-inbound"]) {
        switch (data["arq-transfer-inbound"].state) {
          case "NEW":
            message = `Type: ${data.type}, Session ID: ${data["arq-transfer-inbound"].session_id}, DXCall: ${data["arq-transfer-inbound"].dxcall}, State: ${data["arq-transfer-inbound"].state}`;
            displayToast("info", "bi-info-circle", message, 5000);
            stateStore.dxcallsign = data["arq-transfer-inbound"].dxcall;
            stateStore.arq_transmission_percent = 0;
            stateStore.arq_total_bytes = 0;
            stateStore.arq_speed_list_timestamp =
              data["arq-transfer-inbound"].statistics.time_histogram;
            stateStore.arq_speed_list_bpm =
              data["arq-transfer-inbound"].statistics.bpm_histogram;
            stateStore.arq_speed_list_snr =
              data["arq-transfer-inbound"].statistics.snr_histogram;

            return;

          case "OPEN_ACK_SENT":
            message = `Session ID: ${data["arq-transfer-inbound"].session_id}, DXCall: ${data["arq-transfer-inbound"].dxcall}, Total Bytes: ${data["arq-transfer-inbound"].total_bytes}, State: ${data["arq-transfer-inbound"].state}`;
            displayToast("info", "bi-arrow-left-right", message, 5000);
            stateStore.arq_transmission_percent =
              (data["arq-transfer-inbound"].received_bytes /
                data["arq-transfer-inbound"].total_bytes) *
              100;
            stateStore.arq_total_bytes =
              data["arq-transfer-inbound"].received_bytes;
            return;

          case "INFO_ACK_SENT":
            message = `Type: ${data.type}, Session ID: ${data["arq-transfer-inbound"].session_id}, DXCall: ${data["arq-transfer-inbound"].dxcall}, Received Bytes: ${data["arq-transfer-inbound"].received_bytes}/${data["arq-transfer-inbound"].total_bytes}, State: ${data["arq-transfer-inbound"].state}`;
            displayToast("info", "bi-info-circle", message, 5000);
            stateStore.arq_transmission_percent =
              (data["arq-transfer-inbound"].received_bytes /
                data["arq-transfer-inbound"].total_bytes) *
              100;
            stateStore.arq_total_bytes =
              data["arq-transfer-inbound"].received_bytes;
            return;

          case "BURST_REPLY_SENT":
            message = `Type: ${data.type}, Session ID: ${data["arq-transfer-inbound"].session_id}, DXCall: ${data["arq-transfer-inbound"].dxcall}, Received Bytes: ${data["arq-transfer-inbound"].received_bytes}/${data["arq-transfer-inbound"].total_bytes}, State: ${data["arq-transfer-inbound"].state}`;
            displayToast("info", "bi-info-circle", message, 5000);
            stateStore.arq_transmission_percent =
              (data["arq-transfer-inbound"].received_bytes /
                data["arq-transfer-inbound"].total_bytes) *
              100;
            stateStore.arq_total_bytes =
              data["arq-transfer-inbound"].received_bytes;
            return;

          case "ENDED":
            message = `Type: ${data.type}, Session ID: ${data["arq-transfer-inbound"].session_id}, DXCall: ${data["arq-transfer-inbound"].dxcall}, Received Bytes: ${data["arq-transfer-inbound"].received_bytes}/${data["arq-transfer-inbound"].total_bytes}, State: ${data["arq-transfer-inbound"].state}`;
            displayToast("info", "bi-info-circle", message, 5000);
            // Forward data to chat module
            newMessageReceived(
              data["arq-transfer-inbound"].data,
              data["arq-transfer-inbound"],
            );
            stateStore.arq_transmission_percent =
              (data["arq-transfer-inbound"].received_bytes /
                data["arq-transfer-inbound"].total_bytes) *
              100;
            stateStore.arq_total_bytes =
              data["arq-transfer-inbound"].received_bytes;
            return;

          case "ABORTED":
            console.info("state ABORTED needs to be implemented");
            return;

          case "FAILED":
            message = `Type: ${data.type}, Session ID: ${data["arq-transfer-outbound"].session_id}, DXCall: ${data["arq-transfer-outbound"].dxcall}, Received Bytes: ${data["arq-transfer-outbound"].received_bytes}/${data["arq-transfer-outbound"].total_bytes}, State: ${data["arq-transfer-outbound"].state}`;
            displayToast("info", "bi-info-circle", message, 5000);
            return;
        }
      }
      return;
  }
}

function build_HSL() {
  //Use data from activities to build HSL list
  for (let i = 0; i < stateStore.activities.length; i++) {
    if (
      stateStore.activities[i][1].direction != "received" ||
      stateStore.activities[i][1].origin == undefined
    ) {
      //Ignore stations without origin and not received type
      //console.warn("HSL: Ignoring " + stateStore.activities[i][0]);
      continue;
    }
    let found = false;
    for (let ii = 0; ii < stateStore.heard_stations.length; ii++) {
      if (
        stateStore.heard_stations[ii].origin ==
        stateStore.activities[i][1].origin
      ) {
        //Station already in HSL, check if newer than one in HSL
        found = true;
        if (
          stateStore.heard_stations[ii].timestamp <
          stateStore.activities[i][1].timestamp
        ) {
          //Update existing entry in HSL
          stateStore.heard_stations[ii] = stateStore.activities[i][1];
        }
      }
    }
    if (found == false) {
      //Station not in HSL, let us add it
      stateStore.heard_stations.push(stateStore.activities[i][1]);
    }
  }
  stateStore.heard_stations.sort((a, b) => b.timestamp - a.timestamp); // b - a for reverse sort
}

export function getOverallHealth() {
  //Return a number indicating health for icon bg color; lower the number the healthier
  let health = 0;
  if (stateStore.modem_connection !== "connected") {
    health += 5;
    stateStore.is_modem_running = false;
    stateStore.radio_status = false;
  }
  if (!stateStore.is_modem_running) health += 3;
  if (stateStore.radio_status === false) health += 2;
  if (process.env.FDUpdateAvail === "1") health += 1;
  return health;
}
