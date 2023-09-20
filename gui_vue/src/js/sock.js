var net = require("net");
const path = require("path");
const FD = require("./src/js/freedata.js");
//import FD from './freedata.js';
import { newMessageReceived } from './chatHandler.js';

// ----------------- init pinia stores -------------
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);
import { useStateStore } from '../store/stateStore.js';
const stateStore = useStateStore(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
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
  stateStore.updateTncState(client.readyState)

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
    stateStore.updateTncState(client.readyState)

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
    stateStore.updateTncState(client.readyState)
    client.destroy();

    setTimeout(connectTNC, 500);
});

function writeTncCommand(command) {
  console.log(command)
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
};

client.on("data", function (socketdata) {
    stateStore.updateTncState(client.readyState)


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

      if (data["command"] == "tnc_state") {
        //console.log(data)
        // set length of RX Buffer to global variable
        rxBufferLengthTnc = data["rx_buffer_length"];
        //rxMsgBufferLengthTnc = data["rx_msg_buffer_length"];

        stateStore.frequency = data["frequency"]
        stateStore.busy_state = data["tnc_state"]
        stateStore.arq_state = data["arq_state"]
        stateStore.mode = data["mode"]
        stateStore.bandwidth = data["bandwidth"]
        stateStore.dbfs_level = data["audio_dbfs"]
        stateStore.ptt_state = data["ptt_state"]
        stateStore.speed_level = data["speed_level"]
        stateStore.fft = data["fft"]
        stateStore.channel_busy = data["channel_busy"]
        stateStore.channel_busy_slot = data["channel_busy_slot"]
        stateStore.scatter = data["scatter"]
        // s meter strength
        stateStore.s_meter_strength_raw = data["strength"]
        // https://www.moellerstudios.org/converting-amplitude-representations/
        var noise_level = Math.round(Math.pow(10, stateStore.s_meter_strength_raw / 20) * 100);
        stateStore.s_meter_strength_percent = noise_level

        stateStore.arq_total_bytes = data["total_bytes"]
        stateStore.heard_stations = data["stations"]
        stateStore.dxcallsign = data["dxcallsign"]
        stateStore.arq_session_state = data["arq_session"]
        stateStore.arq_state = data["arq_state"]
        stateStore.beacon_state = data["beacon_state"]
        stateStore.audio_recording = data["audio_recording"]

        stateStore.hamlib_status = data["hamlib_status"]
        stateStore.audio_level = data["audio_level"]
        stateStore.alc = data["alc"]
        stateStore.rf_level = data["rf_level"]

        stateStore.is_codec2_traffic = data["is_codec2_traffic"]

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
          arq_seconds_until_finish: data["arq_seconds_until_finish"],
          arq_compression_factor: data["arq_compression_factor"],
          arq_transmission_percent: data["arq_transmission_percent"],
          routing_table: data["routing_table"],
          mesh_signalling_table: data["mesh_signalling_table"],
          listen: data["listen"],
          speed_list: data["speed_list"],
          is_codec2_traffic: data["is_codec2_traffic"],
          //speed_table: [{"bpm" : 5200, "snr": -3, "timestamp":1673555399},{"bpm" : 2315, "snr": 12, "timestamp":1673555500}],
        };

        //continue to next for loop iteration, nothing else needs to be done here
        continue;
      }

      // ----------- catch tnc messages START -----------
      if (data["freedata"] == "tnc-message") {
        switch (data["fec"]) {
          case "is_writing":
            // RX'd FECiswriting
            break;

          case "broadcast":
            // RX'd FEC BROADCAST
            var encoded_data = FD.atob_FD(data["data"]);
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
            break;

          case "received":
            // CQ RECEIVED
            break;
        }

        switch (data["qrv"]) {
          case "transmitting":
            // QRV TRANSMITTING
            break;

          case "received":
            // QRV RECEIVED
            break;
        }

        switch (data["beacon"]) {
          case "transmitting":
            // BEACON TRANSMITTING
            break;

          case "received":
            // BEACON RECEIVED
            break;
        }

        switch (data["ping"]) {
          case "transmitting":
            // PING TRANSMITTING
            break;

          case "received":
            // PING RECEIVED
            break;

          case "acknowledge":
            // PING ACKNOWLEDGE
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
              break;

            case "opening":
              // ARQ Opening IRS/ISS
              if (data["irs"] == "False") {
                break;
              } else {
                break;

              }

              break;

            case "waiting":
              // ARQ waiting
              break;

            case "receiving":
              // ARQ RX
              break;

            case "failed":
              // ARQ TX Failed
              if (data["reason"] == "protocol version missmatch") {
                break;

              } else {
                break;
              }
              switch (data["irs"]) {
                case "True":
                  break;
                default:
                  break;
              }
              break;

            case "received":
              // ARQ data received

              console.log(data);
              // we need to encode here to do a deep check for checking if file or message
              //var encoded_data = atob(data['data'])
              var encoded_data = FD.atob_FD(data["data"]);
              var splitted_data = encoded_data.split(split_char);

              // new message received
              if (splitted_data[0] == "m") {
                console.log(splitted_data)
                newMessageReceived(splitted_data, data)


              }

              break;

            case "transmitting":
              // ARQ transmitting
              break;

            case "transmitted":
              // ARQ transmitted
              break;
          }
        }
      }


      // ----------- catch tnc info messages END -----------

      // if we manually checking for the rx buffer we are getting an array of multiple data
      if (data["command"] == "rx_buffer") {
        console.log(data);
        // iterate through buffer list and sort it to file or message array
        dataArray = [];
        messageArray = [];

        for (var i = 0; i < data["data-array"].length; i++) {
          try {
            // we need to encode here to do a deep check for checking if file or message
            //var encoded_data = atob(data['data-array'][i]['data'])
            var encoded_data = FD.atob_FD(data["data-array"][i]["data"]);
            var splitted_data = encoded_data.split(split_char);


            if (splitted_data[0] == "m") {
              messageArray.push(data["data-array"][i]);
            }
          } catch (e) {
            console.log(e);
          }
        }

        let Messages = {
          data: messageArray,
        };
        ////ipcRenderer.send('request-update-rx-msg-buffer', Messages);
        //ipcRenderer.send("request-new-msg-received", Messages);
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
function getTncState(){
  var command = '{"type" : "get", "command" : "tnc_state"}';
  writeTncCommand(command);
};

//Get DATA State
//exports.getDataState = function () {
function getDataState(){
  var command = '{"type" : "get", "command" : "data_state"}';
  //writeTncCommand(command)
};

// Send Ping
//exports.sendPing = function (dxcallsign) {
export function sendPing(dxcallsign){
  var command =
    '{"type" : "ping", "command" : "ping", "dxcallsign" : "' +
    dxcallsign +
    '"}';
  writeTncCommand(command);
};

// Send Mesh Ping
//exports.sendMeshPing = function (dxcallsign) {
function sendMeshPing(dxcallsign){
  command =
    '{"type" : "mesh", "command" : "ping", "dxcallsign" : "' +
    dxcallsign +
    '"}';
  writeTncCommand(command);
};

// Send CQ
//exports.sendCQ = function () {
export function sendCQ(){

  var command = '{"type" : "broadcast", "command" : "cqcqcq"}';
  writeTncCommand(command);
};

// Set AUDIO Level
export function setTxAudioLevel(value){
  var command =
    '{"type" : "set", "command" : "tx_audio_level", "value" : "' + value + '"}';
  writeTncCommand(command);
};

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
  data = FD.btoa_FD(data);

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
};

// Send Message
export function sendMessage(
  dxcallsign,
  data,
  checksum,
  uuid,
  command,
) {
  data = FD.btoa_FD(
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
  var mode = 255
  var frames = 5


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
};

// Send Request message
//It would be then „m + split + request + split + request-type“
function sendRequest(dxcallsign, mode, frames, data, command) {
  data = FD.btoa_FD("m" + split_char + command + split_char + data);
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
  data = FD.btoa_FD("m" + split_char + command + split_char + data);
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
function sendRequestInfo(dxcallsign){
  //Command 0 = user/station information
  //Command 1 = shared folder list
  //Command 2 = shared file transfer
  sendRequest(dxcallsign, 255, 1, "0", "req");
};

//Send shared folder file list request
//exports.sendRequestSharedFolderList = function (dxcallsign) {
function sendRequestSharedFolderList(dxcallsign){

  //Command 0 = user/station information
  //Command 1 = shared folder list
  //Command 2 = shared file transfer
  sendRequest(dxcallsign, 255, 1, "1", "req");
};

//Send shared file request
//exports.sendRequestSharedFile = function (dxcallsign, file) {
function sendRequestSharedFile(dxcallsign, file){
  //Command 0 = user/station information
  //Command 1 = shared folder list
  //Command 2 = shared file transfer
  sendRequest(dxcallsign, 255, 1, "2" + file, "req");
};

//Send station info response
//exports.sendResponseInfo = function (dxcallsign, userinfo) {
function sendResponseInfo(dxcallsign, userinfo){
  //Command 0 = user/station information
  //Command 1 = shared folder list
  //Command 2 = shared file transfer
  sendResponse(dxcallsign, 255, 1, userinfo, "res-0");
};

//Send shared folder response
//exports.sendResponseSharedFolderList = function (dxcallsign, sharedFolderList) {
function sendResponseSharedFolderList(dxcallsign, sharedFolderList){
  //Command 0 = user/station information
  //Command 1 = shared folder list
  //Command 2 = shared file transfer
  sendResponse(dxcallsign, 255, 1, sharedFolderList, "res-1");
};

//Send shared file response
//exports.sendResponseSharedFile = function (
function sendResponseSharedFile(
  dxcallsign,
  sharedFile,
  sharedFileData,
) {
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
};

//STOP TRANSMISSION
export function stopTransmission(){
  var command = '{"type" : "arq", "command": "stop_transmission"}';
  writeTncCommand(command);
};

// Get RX BUffer
export function getRxBuffer(){
  var command = '{"type" : "get", "command" : "rx_buffer"}';

  // call command only if new data arrived
  if (rxBufferLengthGui != rxBufferLengthTnc) {
    writeTncCommand(command);
  }
};

// START BEACON
export function startBeacon(interval){
  var command =
    '{"type" : "broadcast", "command" : "start_beacon", "parameter": "' +
    interval +
    '"}';
  writeTncCommand(command);
};

// STOP BEACON
export function stopBeacon(){
  var command = '{"type" : "broadcast", "command" : "stop_beacon"}';
  writeTncCommand(command);
};

// OPEN ARQ SESSION
export function connectARQ(dxcallsign){
  command =
    '{"type" : "arq", "command" : "connect", "dxcallsign": "' +
    dxcallsign +
    '", "attempts": "10"}';
  writeTncCommand(command);
};

// CLOSE ARQ SESSION
export function disconnectARQ(){
  var command = '{"type" : "arq", "command" : "disconnect"}';
  writeTncCommand(command);
};

// SEND TEST FRAME
export function sendTestFrame(){
  var command = '{"type" : "set", "command" : "send_test_frame"}';
  writeTncCommand(command);
};

// SEND FEC
export function sendFEC(mode, payload){
  var command =
    '{"type" : "fec", "command" : "transmit", "mode" : "' +
    mode +
    '", "payload" : "' +
    payload +
    '"}';
  writeTncCommand(command);
};

// SEND FEC IS WRITING
export function sendFecIsWriting(mycallsign){
  var command =
    '{"type" : "fec", "command" : "transmit_is_writing", "mycallsign" : "' +
    mycallsign +
    '"}';
  writeTncCommand(command);
};

// SEND FEC TO BROADCASTCHANNEL
export function sendBroadcastChannel(channel, data_out, uuid){
  let checksum = "";
  let command = "";
  let data = FD.btoa_FD(
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
};

// RECORD AUDIO
export function record_audio(){
  var command = '{"type" : "set", "command" : "record_audio"}';
  writeTncCommand(command);
};

// SET FREQUENCY
export function set_frequency(frequency){
  var command =
    '{"type" : "set", "command" : "frequency", "frequency": ' + frequency + "}";
  writeTncCommand(command);
};

// SET MODE
export function set_mode(mode){
  var command = '{"type" : "set", "command" : "mode", "mode": "' + mode + '"}';
  writeTncCommand(command);
};

// SET rf_level
export function set_rf_level(rf_level){
  var command = '{"type" : "set", "command" : "rf_level", "rf_level": "' + rf_level + '"}';
  writeTncCommand(command);
};


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
