//var net = require("net");
var net = require("node:net");

const path = require("path");
const { ipcRenderer } = require("electron");
// ----------------- init pinia stores -------------
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import { useAudioStore } from "../store/audioStore.js";
const audioStore = useAudioStore(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

var daemon = new net.Socket();
var socketchunk = ""; // Current message, per connection.

// global to keep track of daemon connection error emissions
var daemonShowConnectStateError = 1;

setTimeout(connectDAEMON, 500);

function connectDAEMON() {
  if (daemonShowConnectStateError == 1) {
    console.log("connecting to daemon");
  }

  //clear message buffer after reconnecting or initial connection
  socketchunk = "";

  daemon.connect(settings.daemon_port, settings.daemon_host);

  //client.setTimeout(5000);
}

daemon.on("connect", function (err) {
  console.log("daemon connection established");
  let Data = {
    daemon_connection: daemon.readyState,
  };
  ipcRenderer.send("request-update-daemon-connection", Data);

  daemonShowConnectStateError = 1;
});

daemon.on("error", function (err) {
  if (daemonShowConnectStateError == 1) {
    console.log("daemon connection error");
    console.log("Make sure the daemon is started.");
    console.log('Run "python daemon.py" in the tnc directory.');

    daemonShowConnectStateError = 0;
  }
  setTimeout(connectDAEMON, 500);
  daemon.destroy();
  let Data = {
    daemon_connection: daemon.readyState,
  };
  ipcRenderer.send("request-update-daemon-connection", Data);
});

/*
client.on('close', function(data) {
	console.log(' TNC connection closed');
    setTimeout(connectTNC, 2000)
    let Data = {
        daemon_connection: daemon.readyState,
    };
    ipcRenderer.send('request-update-daemon-connection', Data);
});
*/

daemon.on("end", function (data) {
  console.log("daemon connection ended");
  daemon.destroy();
  setTimeout(connectDAEMON, 500);
  let Data = {
    daemon_connection: daemon.readyState,
  };
  ipcRenderer.send("request-update-daemon-connection", Data);
});

//exports.writeDaemonCommand = function(command){
//writeDaemonCommand = function (command) {
function writeDaemonCommand(command) {
  // we use the writingCommand function to update our TCPIP state because we are calling this function a lot
  // if socket opened, we are able to run commands
  if (daemon.readyState == "open") {
    //uiMain.setDAEMONconnection('open')
    daemon.write(command + "\n");
  }

  if (daemon.readyState == "closed") {
    //uiMain.setDAEMONconnection('closed')
  }

  if (daemon.readyState == "opening") {
    //uiMain.setDAEMONconnection('opening')
  }

  let Data = {
    daemon_connection: daemon.readyState,
  };
  ipcRenderer.send("request-update-daemon-connection", Data);
}

// "https://stackoverflow.com/questions/9070700/nodejs-net-createserver-large-amount-of-data-coming-in"

daemon.on("data", function (socketdata) {
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
    data = JSON.parse(socketchunk[0]);

    // search for empty entries in socketchunk and remove them
    for (var i = 0; i < socketchunk.length; i++) {
      if (socketchunk[i] === "") {
        socketchunk.splice(i, 1);
      }
    }

    //iterate through socketchunks array to execute multiple commands in row
    for (i = 0; i < socketchunk.length; i++) {
      //check if data is not empty
      if (socketchunk[i].length > 0) {
        //try to parse JSON
        try {
          data = JSON.parse(socketchunk[i]);
        } catch (e) {
          console.log(e); // "SyntaxError
          daemonLog.debug(socketchunk[i]);
          socketchunk = "";
        }
      }

      console.log(data)
      if (data["command"] == "daemon_state") {

        // update audio devices by putting them to audio store
        audioStore.inputDevices = data["input_devices"];
        audioStore.outputDevices = data["output_devices"];
        settings.serial_devices = data["serial_devices"];
        state.python_version = data["python_version"]
        state.tnc_version = data["version"]
        state.tnc_running_state = data["daemon_state"][0]["status"];
        state.rigctld_started = data["rigctld_state"][0]["status"];
        //state.rigctld_process = data["daemon_state"][0]["rigctld_process"];


      }




      if (data["command"] == "test_hamlib") {
        let Data = {
          hamlib_result: data["result"],
        };
        ipcRenderer.send("request-update-hamlib-test", Data);
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

//exports.getDaemonState = function () {
function getDaemonState() {
  //function getDaemonState(){
  command = '{"type" : "get", "command" : "daemon_state"}';
  writeDaemonCommand(command);
}

// START TNC
// ` `== multi line string
export function startTNC() {
  var json_command = JSON.stringify({
    type: "set",
    command: "start_tnc",
    parameter: [
      {
        mycall: settings.mycall,
        mygrid: settings.mygrid,
        rx_audio: settings.rx_audio,
        tx_audio: settings.tx_audio,
        radiocontrol: settings.radiocontrol,
        devicename: settings.devicename,
        deviceport: settings.deviceport,
        pttprotocol: settings.pttprotocol,
        pttport: settings.pttport,
        serialspeed: settings.serialspeed,
        data_bits: settings.data_bits,
        stop_bits: settings.stop_bits,
        handshake: settings.handshake,
        rigctld_port: settings.rigctld_port,
        rigctld_ip: settings.rigctld_ip,
        enable_scatter: settings.enable_scatter,
        enable_fft: settings.enable_fft,
        enable_fsk: settings.enable_fsk,
        low_bandwidth_mode: settings.low_bandwidth_mode,
        tuning_range_fmin: settings.tuning_range_fmin,
        tuning_range_fmax: settings.tuning_range_fmax,
        tx_audio_level: settings.tx_audio_level,
        respond_to_cq: settings.respond_to_cq,
        rx_buffer_size: settings.rx_buffer_size,
        enable_explorer: settings.enable_explorer,
        enable_stats: settings.explorer_stats,
        enable_auto_tune: settings.auto_tune,
        tx_delay: settings.tx_delay,
        tci_ip: settings.tci_ip,
        tci_port: settings.tci_port,
        enable_mesh: settings.enable_mesh,
      },
    ],
  });

  console.log(json_command);
  writeDaemonCommand(json_command);
}

// STOP TNC
//exports.stopTNC = function () {
export function stopTNC() {
  var command = '{"type" : "set", "command": "stop_tnc" , "parameter": "---" }';
  writeDaemonCommand(command);
}

// TEST HAMLIB
function testHamlib(
  //exports.testHamlib = function (
  radiocontrol,
  devicename,
  deviceport,
  serialspeed,
  pttprotocol,
  pttport,
  data_bits,
  stop_bits,
  handshake,
  rigctld_ip,
  rigctld_port,
) {
  var json_command = JSON.stringify({
    type: "get",
    command: "test_hamlib",
    parameter: [
      {
        radiocontrol: radiocontrol,
        devicename: devicename,
        deviceport: deviceport,
        pttprotocol: pttprotocol,
        pttport: pttport,
        serialspeed: serialspeed,
        data_bits: data_bits,
        stop_bits: stop_bits,
        handshake: handshake,
        rigctld_port: rigctld_port,
        rigctld_ip: rigctld_ip,
      },
    ],
  });
  console.log(json_command);
  writeDaemonCommand(json_command);
}

export function startRigctld() {

  var json_command = JSON.stringify({
    type: "set",
    command: "start_rigctld",
    parameter: [
      {
      hamlib_deviceid: settings.hamlib_deviceid,
      hamlib_deviceport: settings.hamlib_deviceport,
      hamlib_stop_bits: settings.hamlib_stop_bits,
      hamlib_data_bits: settings.hamlib_data_bits,
      hamlib_handshake: settings.hamlib_handshake,
      hamlib_serialspeed: settings.hamlib_serialspeed,
      hamlib_dtrstate: settings.hamlib_dtrstate,
      hamlib_pttprotocol: settings.hamlib_pttprotocol,
      hamlib_ptt_port: settings.hamlib_ptt_port,
      hamlib_dcd: settings.hamlib_dcd,
      hamlbib_serialspeed_ptt: settings.hamlib_serialspeed,
      hamlib_rigctld_port: settings.hamlib_rigctld_port,
      hamlib_rigctld_ip: settings.hamlib_rigctld_ip,
      hamlib_rigctld_path: settings.hamlib_rigctld_path,
      hamlib_rigctld_server_port: settings.hamlib_rigctld_server_port,
      hamlib_rigctld_custom_args: settings.hamlib_rigctld_custom_args

      },
    ],
  });
  console.log(json_command);
  writeDaemonCommand(json_command);

}
export function stopRigctld(){
  let command = '{"type" : "set", "command": "stop_rigctld"}';
  writeDaemonCommand(command);

}



//Save myCall
function saveMyCall(callsign) {
  //exports.saveMyCall = function (callsign) {
  let command =
    '{"type" : "set", "command": "mycallsign" , "parameter": "' +
    callsign +
    '"}';
  writeDaemonCommand(command);
}

// Save myGrid
//exports.saveMyGrid = function (grid) {
function saveMyGrid(grid) {
  let command =
    '{"type" : "set", "command": "mygrid" , "parameter": "' + grid + '"}';
  writeDaemonCommand(command);
}


