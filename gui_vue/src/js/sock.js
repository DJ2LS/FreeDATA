var net = require("net");
const path = require("path");
//const FD = require("./src/js/freedata.js");
import {atob_FD, btoa_FD} from "./freedata.js"
//import FD from './freedata.js';

        import {addDataToWaterfall} from "../js/waterfallHandler.js"


import {
  newMessageReceived,
  newBeaconReceived,
  updateTransmissionStatus,
  setStateSuccess,
  setStateFailed,
} from "./chatHandler.js";
import { displayToast } from "./popupHandler.js";

// ----------------- init pinia stores -------------
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import { useStateStore } from "../store/stateStore.js";
const stateStore = useStateStore(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

var client = new net.Socket();
var socketchunk = ""; // Current message, per connection.

// split character
//const split_char = "\0;\1;";
const split_char = "0;1;";

// globals for getting new data only if available so we are saving bandwidth
var rxBufferLengthTnc = 0;
var rxBufferLengthGui = 0;
//var rxMsgBufferLengthTnc = 0;
//var rxMsgBufferLengthGui = 0;

// global to keep track of TNC connection error emissions
var tncShowConnectStateError = 1;

// network connection Timeout
setTimeout(connectTNC, 2000);

function connectTNC() {
  //exports.connectTNC = function(){
  //console.log('connecting to TNC...')

  //clear message buffer after reconnecting or initial connection
  socketchunk = "";

  client.connect(settings.tnc_port, settings.tnc_host);
}

client.on("connect", function (data) {
  console.log("TNC connection established");

  stateStore.busy_state = "-";
  stateStore.arq_state = "-";
  stateStore.frequency = "-";
  stateStore.mode = "-";
  stateStore.bandwidth = "-";
  stateStore.dbfs_level = 0;
  stateStore.updateTncState(client.readyState);

  tncShowConnectStateError = 1;
});

client.on("error", function (data) {
  if (tncShowConnectStateError == 1) {
    console.log("TNC connection error");
    tncShowConnectStateError = 0;
  }
  setTimeout(connectTNC, 500);
  client.destroy();
  stateStore.busy_state = "-";
  stateStore.arq_state = "-";
  stateStore.frequency = "-";
  stateStore.mode = "-";
  stateStore.bandwidth = "-";
  stateStore.dbfs_level = 0;
  stateStore.updateTncState(client.readyState);
});

/*
client.on('close', function(data) {
	console.log(' TNC connection closed');
    setTimeout(connectTNC, 2000)
});
*/

client.on("end", function (data) {
  console.log("TNC connection ended");
  stateStore.busy_state = "-";
  stateStore.arq_state = "-";
  stateStore.frequency = "-";
  stateStore.mode = "-";
  stateStore.bandwidth = "-";
  stateStore.dbfs_level = 0;
  stateStore.updateTncState(client.readyState);
  client.destroy();

  setTimeout(connectTNC, 500);
});

function writeTncCommand(command) {
  console.log(command);
  // we use the writingCommand function to update our TCPIP state because we are calling this function a lot
  // if socket opened, we are able to run commands

  if (client.readyState == "open") {
    client.write(command + "\n");
  }

  if (client.readyState == "closed") {
    console.log("TNC SOCKET CONNECTION CLOSED!");
  }

  if (client.readyState == "opening") {
    console.log("connecting to TNC...");
  }
}

client.on("data", function (socketdata) {
  stateStore.updateTncState(client.readyState);

  /*
    inspired by:
    stackoverflow.com questions 9070700 nodejs-net-createserver-large-amount-of-data-coming-in
    */

  socketdata = socketdata.toString("utf8"); // convert data to string
  socketchunk += socketdata; // append data to buffer so we can stick long data together

  // check if we received begin and end of json data
  if (socketchunk.startsWith('{"') && socketchunk.endsWith('"}\n')) {
    var data = "";

    // split data into chunks if we received multiple commands
    socketchunk = socketchunk.split("\n");
    //don't think this is needed anymore
    //data = JSON.parse(socketchunk[0])

    // search for empty entries in socketchunk and remove them
    for (var i = 0; i < socketchunk.length; i++) {
      if (socketchunk[i] === "") {
        socketchunk.splice(i, 1);
      }
    }

    //iterate through socketchunks array to execute multiple commands in row
    for (var i = 0; i < socketchunk.length; i++) {
      //check if data is not empty
      if (socketchunk[i].length > 0) {
        //try to parse JSON
        try {
          data = JSON.parse(socketchunk[i]);
        } catch (e) {
          console.log("Throwing away data!!!!\n" + e); // "SyntaxError
          //console.log(e); // "SyntaxError
          console.log(socketchunk[i]);
          socketchunk = "";
          //If we're here, I don't think we want to process any data that may be in data variable
          continue;
        }
      }
        console.log(data)
      if (data["command"] == "tnc_state") {
        //console.log(data)
        // set length of RX Buffer to global variable
        rxBufferLengthTnc = data["rx_buffer_length"];
        //rxMsgBufferLengthTnc = data["rx_msg_buffer_length"];

        stateStore.frequency = data["frequency"];
        stateStore.busy_state = data["tnc_state"];
        stateStore.arq_state = data["arq_state"];
        stateStore.mode = data["mode"];
        stateStore.bandwidth = data["bandwidth"];
        stateStore.dbfs_level = data["audio_dbfs"];
        stateStore.ptt_state = data["ptt_state"];
        stateStore.speed_level = data["speed_level"];
        stateStore.fft = JSON.parse(data["fft"]);
        stateStore.channel_busy = data["channel_busy"];
        stateStore.channel_busy_slot = data["channel_busy_slot"];

        addDataToWaterfall(JSON.parse(data["fft"]))



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
        stateStore.heard_stations = data["stations"];
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
        stateStore.arq_seconds_until_timeout =
          data["arq_seconds_until_timeout"];
        stateStore.arq_seconds_until_timeout_percent =
          (stateStore.arq_seconds_until_timeout / 180) * 100;

        if (data["speed_list"].length > 0) {
          prepareStatsDataForStore(data["speed_list"]);
        }

        // TODO: Remove ported objects
        let Data = {
          mycallsign: data["mycallsign"],
          mygrid: data["mygrid"],
          //channel_state: data['CHANNEL_STATE'],

          info: data["info"],
          rx_buffer_length: data["rx_buffer_length"],
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

        //continue to next for loop iteration, nothing else needs to be done here
        continue;
      }

      // ----------- catch tnc messages START -----------
      //init message variable
      var message = "";
      if (data["freedata"] == "tnc-message") {
        // break early if we received a dummy callsign
        // thats a kind of hotfix, as long as the tnc isnt handling this better
        if (data["dxcallsign"] == "AA0AA-0" || data["dxcallsign"] == "ZZ9YY-0") {
          break;
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
            displayToast(
              "success",
              "bi-arrow-left-right",
              "transmitting CQ",
              5000,
            );
            break;

          case "received":
            // CQ RECEIVED
            message = "CQ from " + data["dxcallsign"];
            displayToast("success", "bi-arrow-left-right", message, 5000);
            break;
        }

        switch (data["qrv"]) {
          case "transmitting":
            // QRV TRANSMITTING
            displayToast(
              "success",
              "bi-arrow-left-right",
              "transmitting QRV ",
              5000,
            );
            break;

          case "received":
            // QRV RECEIVED
            message = "QRV from " + data["dxcallsign"] + " | " + data["dxgrid"];
            displayToast("success", "bi-arrow-left-right", message, 5000);
            break;
        }

        switch (data["beacon"]) {
          case "transmitting":
            // BEACON TRANSMITTING
            displayToast("success", "bi-arrow-left-right", "BEACON... ", 5000);
            break;

          case "received":
            // BEACON RECEIVED
            newBeaconReceived(data);

            message =
              "BEACON from " + data["dxcallsign"] + " | " + data["dxgrid"];
            displayToast("success", "bi-arrow-left-right", message, 5000);
            break;
        }

        switch (data["ping"]) {
          case "transmitting":
            // PING TRANSMITTING
            message = "PING to " + data["dxcallsign"];
            displayToast("success", "bi-arrow-left-right", message, 5000);
            break;

          case "received":
            // PING RECEIVED
            message =
              "PING from " + data["dxcallsign"] + " | " + data["dxgrid"];
            displayToast("success", "bi-arrow-left-right", message, 5000);
            break;

          case "acknowledge":
            // PING ACKNOWLEDGE
            message =
              "PING ACK from " + data["dxcallsign"] + " | " + data["dxgrid"];
            displayToast("success", "bi-arrow-left-right", message, 5000);
            break;
        }

        // ARQ SESSION && freedata == tnc-message
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
        // ARQ TRANSMISSION && freedata == tnc-message
        if (data["arq"] == "transmission") {
          switch (data["status"]) {
            case "opened":
              // ARQ Open
              message = "ARQ session opened:" + data["dxcallsign"];
              displayToast("success", "bi-arrow-left-right", message, 5000);
              break;

            case "opening":
              // ARQ Opening IRS/ISS
              if (data["irs"] == "False") {
                message = "ARQ session opening:" + data["dxcallsign"];
                displayToast("success", "bi-arrow-left-right", message, 5000);
                break;
              } else {
                message = data["dxcallsign"] + "is requesting an ARQ session";
                displayToast("success", "bi-arrow-left-right", message, 5000);
                break;
              }

              break;

            case "waiting":
              // ARQ waiting
              message = "busy channel | ARQ protocol is waiting";
              displayToast("success", "bi-arrow-left-right", message, 5000);
              break;

            case "receiving":
              // ARQ RX
              break;

            case "failed":
              // ARQ TX Failed
              if (data["reason"] == "protocol version missmatch") {
                message = "protocol version missmatch";
                displayToast("success", "bi-arrow-left-right", message, 5000);
                setStateFailed();

                break;
              } else {
                message = "transmission failed";
                displayToast("success", "bi-arrow-left-right", message, 5000);
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
              message = "data transmitted";
              displayToast("success", "bi-arrow-left-right", message, 5000);
              updateTransmissionStatus(data);
              setStateSuccess();

              break;
          }
        }
      }

    }

    //finally delete message buffer
    socketchunk = "";
  }
});

function hexToBytes(hex) {
  for (var bytes = [], c = 0; c < hex.length; c += 2)
    bytes.push(parseInt(hex.substr(c, 2), 16));
  return bytes;
}

//Get TNC State
//exports.getTncState = function () {
function getTncState() {
  var command = '{"type" : "get", "command" : "tnc_state"}';
  writeTncCommand(command);
}

//Get DATA State
//exports.getDataState = function () {
function getDataState() {
  var command = '{"type" : "get", "command" : "data_state"}';
  //writeTncCommand(command)
}

// Send Ping
//exports.sendPing = function (dxcallsign) {
export function sendPing(dxcallsign) {
  var command =
    '{"type" : "ping", "command" : "ping", "dxcallsign" : "' +
    dxcallsign +
    '"}';
  writeTncCommand(command);
}

// Send Mesh Ping
//exports.sendMeshPing = function (dxcallsign) {
function sendMeshPing(dxcallsign) {
  command =
    '{"type" : "mesh", "command" : "ping", "dxcallsign" : "' +
    dxcallsign +
    '"}';
  writeTncCommand(command);
}

// Send CQ
//exports.sendCQ = function () {
export function sendCQ() {
  var command = '{"type" : "broadcast", "command" : "cqcqcq"}';
  writeTncCommand(command);
}

// Set AUDIO Level
export function setTxAudioLevel(value) {
  var command =
    '{"type" : "set", "command" : "tx_audio_level", "value" : "' + value + '"}';
  writeTncCommand(command);
}

// Send File
//exports.sendFile = function (
function sendFile(
  dxcallsign,
  mode,
  frames,
  filename,
  filetype,
  data,
  checksum,
) {
  console.log(data);
  console.log(filetype);
  console.log(filename);

  var datatype = "f";

  data =
    datatype +
    split_char +
    filename +
    split_char +
    filetype +
    split_char +
    checksum +
    split_char +
    data;
  console.log(data);
  //console.log(btoa(data))
  //Btoa / atob will not work with charsets > 8 bits (i.e. the emojis); should probably move away from using it
  //TODO:  Will need to update anyother occurences and throughly test
  //data = btoa(data)
  data = btoa_FD(data);

  command =
    '{"type" : "arq", "command" : "send_raw",  "parameter" : [{"dxcallsign" : "' +
    dxcallsign +
    '", "mode" : "' +
    mode +
    '", "n_frames" : "' +
    frames +
    '", "data" : "' +
    data +
    '"}]}';
  writeTncCommand(command);
}

// Send Message
export function sendMessage(dxcallsign, data, checksum, uuid, command) {
  data = btoa_FD(
    "m" +
      split_char +
      command +
      split_char +
      checksum +
      split_char +
      uuid +
      split_char +
      data,
  );

  // TODO: REMOVE mode and frames from TNC!
  var mode = 255;
  var frames = 5;

  command =
    '{"type" : "arq", "command" : "send_raw",  "uuid" : "' +
    uuid +
    '", "parameter" : [{"dxcallsign" : "' +
    dxcallsign +
    '", "mode" : "' +
    mode +
    '", "n_frames" : "' +
    frames +
    '", "data" : "' +
    data +
    '", "attempts": "10"}]}';
  console.log(command);
  writeTncCommand(command);
}

// Send Request message
//It would be then „m + split + request + split + request-type“
function sendRequest(dxcallsign, mode, frames, data, command) {
  data = btoa_FD("m" + split_char + command + split_char + data);
  command =
    '{"type" : "arq", "command" : "send_raw", "parameter" : [{"dxcallsign" : "' +
    dxcallsign +
    '", "mode" : "' +
    mode +
    '", "n_frames" : "' +
    frames +
    '", "data" : "' +
    data +
    '", "attempts": "10"}]}';
  console.log(command);
  console.log("--------------REQ--------------------");
  writeTncCommand(command);
}

// Send Response message
//It would be then „m + split + request + split + request-type“
function sendResponse(dxcallsign, mode, frames, data, command) {
  data = btoa_FD("m" + split_char + command + split_char + data);
  command =
    '{"type" : "arq", "command" : "send_raw", "parameter" : [{"dxcallsign" : "' +
    dxcallsign +
    '", "mode" : "' +
    mode +
    '", "n_frames" : "' +
    frames +
    '", "data" : "' +
    data +
    '", "attempts": "10"}]}';
  console.log(command);
  console.log("--------------RES--------------------");
  writeTncCommand(command);
}

//Send station info request
//exports.sendRequestInfo = function (dxcallsign) {
function sendRequestInfo(dxcallsign) {
  //Command 0 = user/station information
  //Command 1 = shared folder list
  //Command 2 = shared file transfer
  sendRequest(dxcallsign, 255, 1, "0", "req");
}

//Send shared folder file list request
//exports.sendRequestSharedFolderList = function (dxcallsign) {
function sendRequestSharedFolderList(dxcallsign) {
  //Command 0 = user/station information
  //Command 1 = shared folder list
  //Command 2 = shared file transfer
  sendRequest(dxcallsign, 255, 1, "1", "req");
}

//Send shared file request
//exports.sendRequestSharedFile = function (dxcallsign, file) {
function sendRequestSharedFile(dxcallsign, file) {
  //Command 0 = user/station information
  //Command 1 = shared folder list
  //Command 2 = shared file transfer
  sendRequest(dxcallsign, 255, 1, "2" + file, "req");
}

//Send station info response
//exports.sendResponseInfo = function (dxcallsign, userinfo) {
function sendResponseInfo(dxcallsign, userinfo) {
  //Command 0 = user/station information
  //Command 1 = shared folder list
  //Command 2 = shared file transfer
  sendResponse(dxcallsign, 255, 1, userinfo, "res-0");
}

//Send shared folder response
//exports.sendResponseSharedFolderList = function (dxcallsign, sharedFolderList) {
function sendResponseSharedFolderList(dxcallsign, sharedFolderList) {
  //Command 0 = user/station information
  //Command 1 = shared folder list
  //Command 2 = shared file transfer
  sendResponse(dxcallsign, 255, 1, sharedFolderList, "res-1");
}

//Send shared file response
//exports.sendResponseSharedFile = function (
function sendResponseSharedFile(dxcallsign, sharedFile, sharedFileData) {
  console.log(
    "In sendResponseSharedFile",
    dxcallsign,
    sharedFile,
    sharedFileData,
  );
  //Command 0 = user/station information
  //Command 1 = shared folder list
  //Command 2 = shared file transfer
  sendResponse(dxcallsign, 255, 1, sharedFile + "/" + sharedFileData, "res-2");
}

//STOP TRANSMISSION
export function stopTransmission() {
  var command = '{"type" : "arq", "command": "stop_transmission"}';
  writeTncCommand(command);
}

// Get RX BUffer
export function getRxBuffer() {
  var command = '{"type" : "get", "command" : "rx_buffer"}';

    writeTncCommand(command);

}

// START BEACON
export function startBeacon(interval) {
  var command =
    '{"type" : "broadcast", "command" : "start_beacon", "parameter": "' +
    interval +
    '"}';
  writeTncCommand(command);
}

// STOP BEACON
export function stopBeacon() {
  var command = '{"type" : "broadcast", "command" : "stop_beacon"}';
  writeTncCommand(command);
}

// OPEN ARQ SESSION
export function connectARQ(dxcallsign) {
  command =
    '{"type" : "arq", "command" : "connect", "dxcallsign": "' +
    dxcallsign +
    '", "attempts": "10"}';
  writeTncCommand(command);
}

// CLOSE ARQ SESSION
export function disconnectARQ() {
  var command = '{"type" : "arq", "command" : "disconnect"}';
  writeTncCommand(command);
}

// SEND TEST FRAME
export function sendTestFrame() {
  var command = '{"type" : "set", "command" : "send_test_frame"}';
  writeTncCommand(command);
}

// SEND FEC
export function sendFEC(mode, payload) {
  var command =
    '{"type" : "fec", "command" : "transmit", "mode" : "' +
    mode +
    '", "payload" : "' +
    payload +
    '"}';
  writeTncCommand(command);
}

// SEND FEC IS WRITING
export function sendFecIsWriting(mycallsign) {
  var command =
    '{"type" : "fec", "command" : "transmit_is_writing", "mycallsign" : "' +
    mycallsign +
    '"}';
  writeTncCommand(command);
}

// SEND FEC TO BROADCASTCHANNEL
export function sendBroadcastChannel(channel, data_out, uuid) {
  let checksum = "";
  let command = "";
  let data = btoa_FD(
    "m" +
      split_char +
      channel +
      //split_char +
      //checksum +
      split_char +
      uuid +
      split_char +
      data_out,
  );
  console.log(data.length);
  let payload = data;
  command =
    '{"type" : "fec", "command" : "transmit", "mode": "datac4", "wakeup": "True", "payload" : "' +
    payload +
    '"}';
  writeTncCommand(command);
}

// RECORD AUDIO
export function record_audio() {
  var command = '{"type" : "set", "command" : "record_audio"}';
  writeTncCommand(command);
}

// SET FREQUENCY
export function set_frequency(frequency) {
  var command =
    '{"type" : "set", "command" : "frequency", "frequency": ' + frequency + "}";
  writeTncCommand(command);
}

// SET MODE
export function set_mode(mode) {
  var command = '{"type" : "set", "command" : "mode", "mode": "' + mode + '"}';
  writeTncCommand(command);
}

// SET rf_level
export function set_rf_level(rf_level) {
  var command =
    '{"type" : "set", "command" : "rf_level", "rf_level": "' + rf_level + '"}';
  writeTncCommand(command);
}

// https://stackoverflow.com/a/50579690
// crc32 calculation
//console.log(crc32('abc'));
//console.log(crc32('abc').toString(16).toUpperCase()); // hex

var crc32 = function (r) {
  for (var a, o = [], c = 0; c < 256; c++) {
    a = c;
    for (var f = 0; f < 8; f++) a = 1 & a ? 3988292384 ^ (a >>> 1) : a >>> 1;
    o[c] = a;
  }
  for (var n = -1, t = 0; t < r.length; t++)
    n = (n >>> 8) ^ o[255 & (n ^ r.charCodeAt(t))];
  return (-1 ^ n) >>> 0;
};

// TODO: Maybe moving this to another module
function prepareStatsDataForStore(data) {
  // dummy data
  //state.arq_speed_list = [{"snr":0.0,"bpm":104,"timestamp":1696189769},{"snr":0.0,"bpm":80,"timestamp":1696189778},{"snr":0.0,"bpm":70,"timestamp":1696189783},{"snr":0.0,"bpm":58,"timestamp":1696189792},{"snr":0.0,"bpm":52,"timestamp":1696189797},{"snr":"NaN","bpm":42,"timestamp":1696189811},{"snr":0.0,"bpm":22,"timestamp":1696189875},{"snr":0.0,"bpm":21,"timestamp":1696189881},{"snr":0.0,"bpm":17,"timestamp":1696189913},{"snr":0.0,"bpm":15,"timestamp":1696189932},{"snr":0.0,"bpm":15,"timestamp":1696189937},{"snr":0.0,"bpm":14,"timestamp":1696189946},{"snr":-6.1,"bpm":14,"timestamp":1696189954},{"snr":-6.1,"bpm":14,"timestamp":1696189955},{"snr":-5.5,"bpm":28,"timestamp":1696189963},{"snr":-5.5,"bpm":27,"timestamp":1696189963}]

  if (typeof data == "undefined") {
    var speed_listSize = 0;
  } else {
    var speed_listSize = data.length;
  }

  var speed_list_bpm = [];

  for (var i = 0; i < speed_listSize; i++) {
    speed_list_bpm.push(data[i].bpm);
  }

  var speed_list_timestamp = [];

  for (var i = 0; i < speed_listSize; i++) {
    var timestamp = data[i].timestamp * 1000;
    var h = new Date(timestamp).getHours();
    var m = new Date(timestamp).getMinutes();
    var s = new Date(timestamp).getSeconds();
    var time = h + ":" + m + ":" + s;
    speed_list_timestamp.push(time);
  }

  var speed_list_snr = [];
  for (var i = 0; i < speed_listSize; i++) {
    let snr = NaN;
    if (data[i].snr !== 0) {
      snr = data[i].snr;
    } else {
      snr = NaN;
    }
    speed_list_snr.push(snr);
  }

  stateStore.arq_speed_list_bpm = speed_list_bpm;
  stateStore.arq_speed_list_timestamp = speed_list_timestamp;
  stateStore.arq_speed_list_snr = speed_list_snr;
}
