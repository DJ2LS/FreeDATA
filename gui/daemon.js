var net = require("net");
const path = require("path");
const { ipcRenderer } = require("electron");
const log = require("electron-log");
const daemonLog = log.scope("daemon");

// https://stackoverflow.com/a/26227660
var appDataFolder =
  process.env.APPDATA ||
  (process.platform == "darwin"
    ? process.env.HOME + "/Library/Application Support"
    : process.env.HOME + "/.config");
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, "config.json");
const config = require(configPath);

var daemon = new net.Socket();
var socketchunk = ""; // Current message, per connection.

// global to keep track of daemon connection error emissions
var daemonShowConnectStateError = 1;

// global for storing ip information
var daemon_port = config.daemon_port;
var daemon_host = config.daemon_host;

setTimeout(connectDAEMON, 500);

function connectDAEMON() {
  if (daemonShowConnectStateError == 1) {
    daemonLog.info("connecting to daemon");
  }

  //clear message buffer after reconnecting or initial connection
  socketchunk = "";

  if (config.tnclocation == "localhost") {
    daemon.connect(3001, "127.0.0.1");
  } else {
    daemon.connect(daemon_port, daemon_host);
  }

  //client.setTimeout(5000);
}

daemon.on("connect", function (err) {
  daemonLog.info("daemon connection established");
  let Data = {
    daemon_connection: daemon.readyState,
  };
  ipcRenderer.send("request-update-daemon-connection", Data);

  daemonShowConnectStateError = 1;
});

daemon.on("error", function (err) {
  if (daemonShowConnectStateError == 1) {
    daemonLog.error("daemon connection error");
    daemonLog.info("Make sure the daemon is started.");
    daemonLog.info('Run "python daemon.py" in the tnc directory.');

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
  daemonLog.warn("daemon connection ended");
  daemon.destroy();
  setTimeout(connectDAEMON, 500);
  let Data = {
    daemon_connection: daemon.readyState,
  };
  ipcRenderer.send("request-update-daemon-connection", Data);
});

//exports.writeCommand = function(command){
writeDaemonCommand = function (command) {
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
};

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
    for (i = 0; i < socketchunk.length; i++) {
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
          daemonLog.error(e);
          daemonLog.debug(socketchunk[i]);
          socketchunk = "";
        }
      }

      if (data["command"] == "daemon_state") {
        let Data = {
          input_devices: data["input_devices"],
          output_devices: data["output_devices"],
          python_version: data["python_version"],
          hamlib_version: data["hamlib_version"],
          serial_devices: data["serial_devices"],
          tnc_running_state: data["daemon_state"][0]["status"],
          ram_usage: data["ram"],
          cpu_usage: data["cpu"],
          version: data["version"],
        };
        ipcRenderer.send("request-update-daemon-state", Data);
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

exports.getDaemonState = function () {
  //function getDaemonState(){
  command = '{"type" : "get", "command" : "daemon_state"}';
  writeDaemonCommand(command);
};

// START TNC
// ` `== multi line string

exports.startTNC = function (
  mycall,
  mygrid,
  rx_audio,
  tx_audio,
  radiocontrol,
  devicename,
  deviceport,
  pttprotocol,
  pttport,
  serialspeed,
  data_bits,
  stop_bits,
  handshake,
  rigctld_ip,
  rigctld_port,
  enable_fft,
  enable_scatter,
  low_bandwidth_mode,
  tuning_range_fmin,
  tuning_range_fmax,
  enable_fsk,
  tx_audio_level,
  respond_to_cq,
  rx_buffer_size,
  enable_explorer,
  explorer_stats,
  auto_tune,
  tx_delay,
  tci_ip,
  tci_port
) {
  var json_command = JSON.stringify({
    type: "set",
    command: "start_tnc",
    parameter: [
      {
        mycall: mycall,
        mygrid: mygrid,
        rx_audio: rx_audio,
        tx_audio: tx_audio,
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
        enable_scatter: enable_scatter,
        enable_fft: enable_fft,
        enable_fsk: enable_fsk,
        low_bandwidth_mode: low_bandwidth_mode,
        tuning_range_fmin: tuning_range_fmin,
        tuning_range_fmax: tuning_range_fmax,
        tx_audio_level: tx_audio_level,
        respond_to_cq: respond_to_cq,
        rx_buffer_size: rx_buffer_size,
        enable_explorer: enable_explorer,
        enable_stats: explorer_stats,
        enable_auto_tune: auto_tune,
        tx_delay: tx_delay,
        tci_ip: tci_ip,
        tci_port: tci_port,
      },
    ],
  });

  daemonLog.debug(json_command);
  writeDaemonCommand(json_command);
};

// STOP TNC
exports.stopTNC = function () {
  command = '{"type" : "set", "command": "stop_tnc" , "parameter": "---" }';
  writeDaemonCommand(command);
};

// TEST HAMLIB
exports.testHamlib = function (
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
  rigctld_port
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
  daemonLog.debug(json_command);
  writeDaemonCommand(json_command);
};

//Save myCall
exports.saveMyCall = function (callsign) {
  command =
    '{"type" : "set", "command": "mycallsign" , "parameter": "' +
    callsign +
    '"}';
  writeDaemonCommand(command);
};

// Save myGrid
exports.saveMyGrid = function (grid) {
  command =
    '{"type" : "set", "command": "mygrid" , "parameter": "' + grid + '"}';
  writeDaemonCommand(command);
};

ipcRenderer.on("action-update-daemon-ip", (event, arg) => {
  daemon.destroy();
  let Data = {
    busy_state: "-",
    arq_state: "-",
    //channel_state: "-",
    frequency: "-",
    mode: "-",
    bandwidth: "-",
    dbfs_level: 0,
  };
  ipcRenderer.send("request-update-tnc-state", Data);
  daemon_port = arg.port;
  daemon_host = arg.adress;
  connectDAEMON();
});
