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

import { settingsStore as settings } from "../store/settingsStore.js";

export function connectionFailed(endpoint, event) {
  stateStore.modem_connection = "disconnected";
}
export function stateDispatcher(data) {
  data = JSON.parse(data);
  console.log(data);
  if (data["type"] == "state-change" || data["type"] == "state") {
    stateStore.channel_busy = data["channel_busy"];
    stateStore.is_codec2_traffic = data["is_codec2_traffic"];
    stateStore.is_modem_running = data["is_modem_running"];
    stateStore.dbfs_level = Math.round(data["audio_dbfs"]);
    stateStore.dbfs_level_percent = Math.round(
      Math.pow(10, data["audio_dbfs"] / 20) * 100,
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
  console.info(data);

  if (data["scatter"] !== undefined) {
    stateStore.scatter = JSON.parse(data["scatter"]);
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

  var message = "";

  switch (data["type"]) {
    case "hello-client":
      message = "Connected to server";
      displayToast("success", "bi-ethernet", message, 5000);
      stateStore.modem_connection = "connected";
      return;

    case "arq":
      if (data["arq-transfer-outbound"]) {
        switch (data["arq-transfer-outbound"].state) {
          case "NEW":
            message = `Type: ${ev.type}, Session ID: ${ev["arq-transfer-outbound"].session_id}, DXCall: ${ev["arq-transfer-outbound"].dxcall}, Total Bytes: ${ev["arq-transfer-outbound"].total_bytes}, State: ${ev["arq-transfer-outbound"].state}`;
            displayToast("success", "bi-check-circle", message, 5000);
            return;
          case "OPEN_SENT":
            console.log("state OPEN_SENT needs to be implemented");
            return;

          case "INFO_SENT":
            console.log("state INFO_SENT needs to be implemented");
            return;

          case "BURST_SENT":
            message = `Type: ${ev.type}, Session ID: ${data["arq-transfer-outbound"].session_id}, DXCall: ${data["arq-transfer-outbound"].dxcall}, Received Bytes: ${data["arq-transfer-outbound"].received_bytes}/${data["arq-transfer-outbound"].total_bytes}, State: ${data["arq-transfer-outbound"].state}`;
            displayToast("info", "bi-info-circle", message, 5000);
            return;

          case "ABORTING":
            console.log("state ABORTING needs to be implemented");
            return;

          case "ABORTED":
            message = `Type: ${ev.type}, Session ID: ${
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
            message = `Type: ${ev.type}, Session ID: ${
              ev["arq-transfer-outbound"].session_id
            }, DXCall: ${ev["arq-transfer-outbound"].dxcall}, Total Bytes: ${
              ev["arq-transfer-outbound"].total_bytes
            }, Success: ${
              ev["arq-transfer-outbound"].success ? "Yes" : "No"
            }, State: ${ev["arq-transfer-outbound"].state}, Data: ${
              ev["arq-transfer-outbound"].data ? "Available" : "Not Available"
            }`;
            displayToast("danger", "bi-x-octagon", message, 5000);
            return;
        }
      }

      if (data["arq-transfer-inbound"]) {
        switch (data["arq-transfer-inbound"].state) {
          case "NEW":
            message = `Type: ${ev.type}, Session ID: ${ev["arq-transfer-outbound"].session_id}, DXCall: ${ev["arq-transfer-outbound"].dxcall}, State: ${ev["arq-transfer-outbound"].state}`;
            displayToast("info", "bi-info-circle", message, 5000);
            return;

          case "OPEN_ACK_SENT":
            message = `Session ID: ${data["arq-transfer-inbound"].session_id}, DXCall: ${data["arq-transfer-inbound"].dxcall}, Total Bytes: ${data["arq-transfer-inbound"].total_bytes}, State: ${data["arq-transfer-inbound"].state}`;
            displayToast("info", "bi-arrow-left-right", message, 5000);
            return;

          case "INFO_ACK_SENT":
            message = `Type: ${ev.type}, Session ID: ${data["arq-transfer-inbound"].session_id}, DXCall: ${data["arq-transfer-inbound"].dxcall}, Received Bytes: ${data["arq-transfer-inbound"].received_bytes}/${data["arq-transfer-inbound"].total_bytes}, State: ${data["arq-transfer-inbound"].state}`;
            displayToast("info", "bi-info-circle", message, 5000);
            return;

          case "BURST_REPLY_SENT":
            console.log("state BURST_REPLY_SENT needs to be implemented");
            return;

          case "ENDED":
            console.log("state ENDED needs to be implemented");
            return;

          case "ABORTED":
            console.log("state ABORTED needs to be implemented");
            return;

          case "FAILED":
            message = `Type: ${ev.type}, Session ID: ${data["arq-transfer-outbound"].session_id}, DXCall: ${data["arq-transfer-outbound"].dxcall}, Received Bytes: ${data["arq-transfer-outbound"].received_bytes}/${data["arq-transfer-outbound"].total_bytes}, State: ${data["arq-transfer-outbound"].state}`;
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
