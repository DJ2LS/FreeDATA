const path = require("path");
const { ipcRenderer, shell, clipboard } = require("electron");
const exec = require("child_process").spawn;
const sock = require("./sock.js");
const daemon = require("./daemon.js");
const fs = require("fs");
const {
  locatorToLatLng,
  distance,
  bearingDistance,
  latLngToLocator,
} = require("qth-locator");

const { v4: uuidv4 } = require("uuid");

const os = require("os");

// split character used for appending additional data to files
const split_char = "\0;";

// https://stackoverflow.com/a/26227660
var appDataFolder =
  process.env.APPDATA ||
  (process.platform == "darwin"
    ? process.env.HOME + "/Library/Application Support"
    : process.env.HOME + "/.config");
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, "config.json");
const config = require(configPath);
const contrib = [
  "DK5SM",
  "DL4IAZ",
  "DB1UJ",
  "EI3HIB",
  "VK5DGR",
  "EI7IG",
  "N2KIQ",
  "KT4WO",
  "DF7MH",
  "G0HWW",
  "N1QM",
];

//let elements = document.querySelectorAll('[id^="hamlib_"]'); // get all elements starting with...
const hamlib_elements = [
  "hamlib_deviceid",
  "hamlib_deviceport",
  "hamlib_stop_bits",
  "hamlib_data_bits",
  "hamlib_handshake",
  "hamlib_serialspeed",
  "hamlib_dtrstate",
  "hamlib_pttprotocol",
  "hamlib_ptt_port",
  "hamlib_dcd",
  "hamlib_rigctld_port",
  "hamlib_rigctld_ip",
  "hamlib_rigctld_path",
  "hamlib_rigctld_server_port",
  "hamlib_rigctld_custom_args",
];

// SET dbfs LEVEL GLOBAL
// this is an attempt of reducing CPU LOAD
// we are going to check if we have unequal values before we start calculating again
var dbfs_level_raw = 0;
var noise_level_raw = 0;

//Global version variable
var appVer = null;

// START INTERVALL COMMAND EXECUTION FOR STATES
//setInterval(sock.getRxBuffer, 1000);

// WINDOW LISTENER
window.addEventListener("DOMContentLoaded", () => {
  // save frequency event listener
  document.getElementById("saveFrequency").addEventListener("click", () => {
    var freq = document.getElementById("newFrequency").value;
    console.log(freq);
    let Data = {
      type: "set",
      command: "frequency",
      frequency: freq,
    };
    ipcRenderer.send("run-tnc-command", Data);
  });

  // enter button for input field
  document
    .getElementById("newFrequency")
    .addEventListener("keypress", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        document.getElementById("saveFrequency").click();
      }
    });

  // save mode event listener
  document.getElementById("saveModePKTUSB").addEventListener("click", () => {
    let Data = {
      type: "set",
      command: "mode",
      mode: "PKTUSB",
    };
    ipcRenderer.send("run-tnc-command", Data);
  });

  // save mode event listener
  document.getElementById("saveModeUSB").addEventListener("click", () => {
    let Data = {
      type: "set",
      command: "mode",
      mode: "USB",
    };
    ipcRenderer.send("run-tnc-command", Data);
  });

  // save mode event listener
  document.getElementById("saveModeLSB").addEventListener("click", () => {
    let Data = {
      type: "set",
      command: "mode",
      mode: "LSB",
    };
    ipcRenderer.send("run-tnc-command", Data);
  });

  // save mode event listener
  document.getElementById("saveModeAM").addEventListener("click", () => {
    let Data = {
      type: "set",
      command: "mode",
      mode: "AM",
    };
    ipcRenderer.send("run-tnc-command", Data);
  });

  // save mode event listener
  document.getElementById("saveModeFM").addEventListener("click", () => {
    let Data = {
      type: "set",
      command: "mode",
      mode: "FM",
    };
    ipcRenderer.send("run-tnc-command", Data);
  });

  // start stop audio recording event listener
  document
    .getElementById("startStopRecording")
    .addEventListener("click", () => {
      let Data = {
        type: "set",
        command: "record_audio",
      };
      ipcRenderer.send("run-tnc-command", Data);
    });

  document
    .getElementById("received_files_folder")
    .addEventListener("click", () => {
      ipcRenderer.send("get-folder-path", {
        title: "Title",
      });

      ipcRenderer.on("return-folder-paths", (event, data) => {
        document.getElementById("received_files_folder").value =
          data.path.filePaths[0];
        config.received_files_folder = data.path.filePaths[0];
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
      });
    });

  document
    .getElementById("openReceivedFilesFolder")
    .addEventListener("click", () => {
      ipcRenderer.send("open-folder", {
        path: config.received_files_folder,
      });
    });

  /*
    // ENABLE BOOTSTRAP POPOVERS EVERYWHERE
    // https://getbootstrap.com/docs/5.0/components/popovers/#example-enable-popovers-everywhere
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl)
    })
*/

  // ENABLE TOOLTIPS EVERYWHERE
  // https://getbootstrap.com/docs/5.1/components/tooltips/
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // LOAD SETTINGS

  // load settings by function
  loadSettings(hamlib_elements);

  document.getElementById("tnc_adress").value = config.tnc_host;
  document.getElementById("tnc_port").value = config.tnc_port;

  callsign_and_ssid = config.mycall.split("-");
  callsign = callsign_and_ssid[0];
  ssid = callsign_and_ssid[1];

  document.getElementById("myCall").value = callsign;
  //document.title = document.title + ' - Call: ' + config.mycall;
  updateTitle();

  document.getElementById("myCallSSID").value = ssid;
  document.getElementById("myGrid").value = config.mygrid;

  // hamlib settings
  document.getElementById("hamlib_deviceid").value = config.hamlib_deviceid;

  document.getElementById("hamlib_rigctld_ip").value = config.hamlib_rigctld_ip;
  document.getElementById("hamlib_rigctld_port").value =
    config.hamlib_rigctld_port;
  document.getElementById("hamlib_rigctld_path").value =
    config.hamlib_rigctld_path;
  document.getElementById("hamlib_rigctld_server_port").value =
    config.hamlib_rigctld_server_port;

  document.getElementById("beaconInterval").value = config.beacon_interval;

  document.getElementById("scatterSwitch").value = config.enable_scatter;
  document.getElementById("fftSwitch").value = config.enable_fft;

  document.getElementById("received_files_folder").value =
    config.received_files_folder;

  if (config.enable_scatter == "True") {
    document.getElementById("scatterSwitch").checked = true;
  } else {
    document.getElementById("scatterSwitch").checked = false;
  }

  if (config.enable_is_writing == "True") {
    document.getElementById("enable_is_writing").checked = true;
  } else {
    document.getElementById("enable_is_writing").checked = false;
  }

  if (config.enable_fft == "True") {
    document.getElementById("fftSwitch").checked = true;
  } else {
    document.getElementById("fftSwitch").checked = false;
  }

  if (config.low_bandwidth_mode == "True") {
    document.getElementById("500HzModeSwitch").checked = true;
  } else {
    document.getElementById("500HzModeSwitch").checked = false;
  }

  if (config.high_graphics == "True") {
    document.getElementById("GraphicsSwitch").checked = true;
  } else {
    document.getElementById("GraphicsSwitch").checked = false;
  }

  if (config.enable_fsk == "True") {
    document.getElementById("fskModeSwitch").checked = true;
  } else {
    document.getElementById("fskModeSwitch").checked = false;
  }

  if (config.respond_to_cq == "True") {
    document.getElementById("respondCQSwitch").checked = true;
  } else {
    document.getElementById("respondCQSwitch").checked = false;
  }

  if (config.enable_explorer == "True") {
    document.getElementById("ExplorerSwitch").checked = true;
  } else {
    document.getElementById("ExplorerSwitch").checked = false;
  }

  if (config.explorer_stats.toLowerCase() == "true") {
    document.getElementById("ExplorerStatsSwitch").checked = true;
  } else {
    document.getElementById("ExplorerStatsSwitch").checked = false;
  }

  if (config.auto_tune == "True") {
    document.getElementById("autoTuneSwitch").checked = true;
  } else {
    document.getElementById("autoTuneSwitch").checked = false;
  }
  // theme selector

  if (config.theme != "default") {
    var theme_path =
      "../node_modules/bootswatch/dist/" + config.theme + "/bootstrap.min.css";
    document.getElementById("theme_selector").value = config.theme;
    document.getElementById("bootstrap_theme").href = escape(theme_path);
  } else {
    var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
    document.getElementById("theme_selector").value = "default";
    document.getElementById("bootstrap_theme").href = escape(theme_path);
  }

  // Update channel selector
  document.getElementById("update_channel_selector").value =
    config.update_channel;
  document.getElementById("updater_channel").innerHTML = escape(
    config.update_channel
  );

  // Update tuning range fmin fmax
  document.getElementById("tuning_range_fmin").value = config.tuning_range_fmin;
  document.getElementById("tuning_range_fmax").value = config.tuning_range_fmax;

  // Update TX Audio Level
  document.getElementById("audioLevelTXvalue").innerHTML = parseInt(
    config.tx_audio_level
  );
  document.getElementById("audioLevelTX").value = parseInt(
    config.tx_audio_level
  );

  // Update RX Buffer Size
  document.getElementById("rx_buffer_size").value = config.rx_buffer_size;

  if (config.spectrum == "waterfall") {
    document.getElementById("waterfall-scatter-switch1").checked = true;
    document.getElementById("waterfall-scatter-switch2").checked = false;
    document.getElementById("waterfall-scatter-switch3").checked = false;

    document.getElementById("waterfall").style.visibility = "visible";
    document.getElementById("waterfall").style.height = "100%";
    document.getElementById("waterfall").style.display = "block";

    document.getElementById("scatter").style.height = "0px";
    document.getElementById("scatter").style.visibility = "hidden";
    document.getElementById("scatter").style.display = "none";

    document.getElementById("chart").style.height = "0px";
    document.getElementById("chart").style.visibility = "hidden";
    document.getElementById("chart").style.display = "none";
  } else if (config.spectrum == "scatter") {
    document.getElementById("waterfall-scatter-switch1").checked = false;
    document.getElementById("waterfall-scatter-switch2").checked = true;
    document.getElementById("waterfall-scatter-switch3").checked = false;

    document.getElementById("waterfall").style.visibility = "hidden";
    document.getElementById("waterfall").style.height = "0px";
    document.getElementById("waterfall").style.display = "none";

    document.getElementById("scatter").style.height = "100%";
    document.getElementById("scatter").style.visibility = "visible";
    document.getElementById("scatter").style.display = "block";

    document.getElementById("chart").style.visibility = "hidden";
    document.getElementById("chart").style.height = "0px";
    document.getElementById("chart").style.display = "none";
  } else {
    document.getElementById("waterfall-scatter-switch1").checked = false;
    document.getElementById("waterfall-scatter-switch2").checked = false;
    document.getElementById("waterfall-scatter-switch3").checked = true;

    document.getElementById("waterfall").style.visibility = "hidden";
    document.getElementById("waterfall").style.height = "0px";
    document.getElementById("waterfall").style.display = "none";

    document.getElementById("scatter").style.height = "0px";
    document.getElementById("scatter").style.visibility = "hidden";
    document.getElementById("scatter").style.display = "none";

    document.getElementById("chart").style.visibility = "visible";
    document.getElementById("chart").style.height = "100%";
    document.getElementById("chart").style.display = "block";
  }

  // radio control element
  if (config.radiocontrol == "rigctld") {
    document.getElementById("radio-control-switch-disabled").checked = false;
    document.getElementById("radio-control-switch-rigctld").checked = true;
    document.getElementById("radio-control-switch-help").checked = false;

    document.getElementById("radio-control-disabled").style.visibility =
      "hidden";
    document.getElementById("radio-control-disabled").style.display = "none";

    document.getElementById("radio-control-help").style.visibility = "hidden";
    document.getElementById("radio-control-help").style.display = "none";

    document.getElementById("radio-control-rigctld").style.visibility =
      "visible";
    document.getElementById("radio-control-rigctld").style.display = "block";
  } else {
    document.getElementById("radio-control-switch-disabled").checked = true;
    document.getElementById("radio-control-switch-help").checked = false;
    document.getElementById("radio-control-switch-rigctld").checked = false;

    document.getElementById("radio-control-help").style.display = "none";
    document.getElementById("radio-control-help").style.visibility = "hidden";

    document.getElementById("radio-control-rigctld").style.visibility =
      "hidden";
    document.getElementById("radio-control-rigctld").style.display = "none";
  }

  // remote tnc
  if (config.tnclocation == "remote") {
    document.getElementById("local-remote-switch1").checked = false;
    document.getElementById("local-remote-switch2").checked = true;
    document.getElementById("remote-tnc-field").style.visibility = "visible";
    toggleClass("remote-tnc-field", "d-none", false);
  } else {
    document.getElementById("local-remote-switch1").checked = true;
    document.getElementById("local-remote-switch2").checked = false;
    document.getElementById("remote-tnc-field").style.visibility = "hidden";
    toggleClass("remote-tnc-field", "d-none", true);
  }

  // Create spectrum object on canvas with ID "waterfall"
  global.spectrum = new Spectrum("waterfall", {
    spectrumPercent: 0,
    wf_rows: 192, //Assuming 1 row = 1 pixe1, 192 is the height of the spectrum container
  });

  //Set waterfalltheme
  document.getElementById("wftheme_selector").value = config.wftheme;
  spectrum.setColorMap(config.wftheme);

  document.getElementById("btnAbout").addEventListener("click", () => {
    document.getElementById("aboutVersion").innerText = appVer;
    let maxcol = 3;
    let col = 2;
    let shuffled = contrib
      .map((value) => ({ value, sort: Math.random() }))
      .sort((a, b) => a.sort - b.sort)
      .map(({ value }) => value);
    let list = "<li>DJ2LS</li>";
    let list2 = "";
    let list3 = "";
    shuffled.forEach((element) => {
      switch (col) {
        case 1:
          list += "<li>" + element + "</li>";
          break;
        case 2:
          list2 += "<li>" + element + "</li>";
          break;
        case 3:
          list3 += "<li>" + element + "</li>";
          break;
      }
      col = col + 1;
      if (col > maxcol) {
        col = 1;
      }
    });
    //list+="</ul>";
    divContrib.innerHTML = "<ul>" + list + "</ul>";
    divContrib2.innerHTML = "<ul>" + list2 + "</ul>";
    divContrib3.innerHTML = "<ul>" + list3 + "</ul>";
    //console.log(shuffled)
  });

  // on click radio control toggle view
  // disabled
  document
    .getElementById("radio-control-switch-disabled")
    .addEventListener("click", () => {
      //document.getElementById("hamlib_info_field").innerHTML =
      //  "Disables TNC rig control";

      document.getElementById("radio-control-disabled").style.display = "block";
      document.getElementById("radio-control-disabled").style.visibility =
        "visible";

      document.getElementById("radio-control-help").style.display = "none";
      document.getElementById("radio-control-help").style.visibility = "hidden";

      document.getElementById("radio-control-rigctld").style.visibility =
        "hidden";
      document.getElementById("radio-control-rigctld").style.display = "none";

      config.radiocontrol = "disabled";
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

  // // radio settings 'network' event listener
  document
    .getElementById("radio-control-switch-help")
    .addEventListener("click", () => {
      //document.getElementById("hamlib_info_field").innerHTML =
      //  "Set the ip and port of a rigctld session";

      document.getElementById("radio-control-disabled").style.display = "none";
      document.getElementById("radio-control-disabled").style.visibility =
        "hidden";

      document.getElementById("radio-control-help").style.display = "block";
      document.getElementById("radio-control-help").style.visibility =
        "visible";

      document.getElementById("radio-control-rigctld").style.visibility =
        "hidden";
      document.getElementById("radio-control-rigctld").style.display = "none";

      config.radiocontrol = "rigctld";
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

  // // radio settings 'rigctld' event listener
  document
    .getElementById("radio-control-switch-rigctld")
    .addEventListener("click", () => {
      //document.getElementById("hamlib_info_field").innerHTML =
      //  "Edit your rigctld settings and start and stop rigctld .";

      document.getElementById("radio-control-disabled").style.display = "none";
      document.getElementById("radio-control-disabled").style.visibility =
        "hidden";

      document.getElementById("radio-control-help").style.display = "none";
      document.getElementById("radio-control-help").style.visibility = "hidden";

      document.getElementById("radio-control-rigctld").style.visibility =
        "visible";
      document.getElementById("radio-control-rigctld").style.display = "block";

      config.radiocontrol = "rigctld";
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

  document
    .getElementById("btnHamlibCopyCommand")
    .addEventListener("click", () => {
      hamlib_params();
      let rigctld = document.getElementById("hamlib_rigctld_path").value;
      rigctld += " " + document.getElementById("hamlib_rigctld_command").value;
      document.getElementById("btnHamlibCopyCommandBi").classList =
        "bi bi-clipboard2-check-fill";
      clipboard.writeText(rigctld);

      setTimeout(function () {
        document.getElementById("btnHamlibCopyCommandBi").classList =
          "bi bi-clipboard";
      }, 2000);
    });

  document
    .getElementById("hamlib_rigctld_path")
    .addEventListener("click", () => {
      ipcRenderer.send("get-file-path", {
        title: "Title",
      });

      ipcRenderer.on("return-file-paths", (event, data) => {
        rigctldPath = data.path.filePaths[0];
        document.getElementById("hamlib_rigctld_path").value = rigctldPath;
        config.hamlib_rigctld_path = rigctldPath;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        hamlib_params();
      });
    });

  // radio settings 'hamlib_rigctld_server_port' event listener
  document
    .getElementById("hamlib_rigctld_server_port")
    .addEventListener("change", () => {
      config.hamlib_rigctld_server_port = document.getElementById(
        "hamlib_rigctld_server_port"
      ).value;
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
      hamlib_params();
    });

  // hamlib bulk event listener for saving settings
  hamlib_elements.forEach(function (elem) {
    try {
      document.getElementById(elem).addEventListener("change", function () {
        config[elem] = document.getElementById(elem).value;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        console.log(config);
        hamlib_params();
      });
    } catch (e) {
      console.log(e);
      console.log(elem);
    }
  });

  document
    .getElementById("hamlib_rigctld_start")
    .addEventListener("click", () => {
      var rigctldPath = document.getElementById("hamlib_rigctld_path").value;
      var paramList = hamlib_params();

      let Data = {
        path: rigctldPath,
        parameters: paramList,
      };
      ipcRenderer.send("request-start-rigctld", Data);
    });

  hamlib_params = function () {
    var paramList = [];

    var hamlib_deviceid = document.getElementById("hamlib_deviceid").value;
    paramList = paramList.concat("--model=" + hamlib_deviceid);

    // hamlib deviceport setting
    if (document.getElementById("hamlib_deviceport").value !== "ignore") {
      var hamlib_deviceport =
        document.getElementById("hamlib_deviceport").value;
      paramList = paramList.concat("--rig-file=" + hamlib_deviceport);
    }

    // hamlib serialspeed setting
    if (document.getElementById("hamlib_serialspeed").value !== "ignore") {
      var hamlib_serialspeed =
        document.getElementById("hamlib_serialspeed").value;
      paramList = paramList.concat("--serial-speed=" + hamlib_serialspeed);
    }

    // hamlib databits setting
    if (document.getElementById("hamlib_data_bits").value !== "ignore") {
      var hamlib_data_bits = document.getElementById("hamlib_data_bits").value;
      paramList = paramList.concat("--set-conf=data_bits=" + hamlib_data_bits);
    }

    // hamlib stopbits setting
    if (document.getElementById("hamlib_stop_bits").value !== "ignore") {
      var hamlib_stop_bits = document.getElementById("hamlib_stop_bits").value;
      paramList = paramList.concat("--set-conf=stop_bits=" + hamlib_stop_bits);
    }

    // hamlib handshake setting
    if (document.getElementById("hamlib_handshake").value !== "ignore") {
      var hamlib_handshake = document.getElementById("hamlib_handshake").value;
      paramList = paramList.concat(
        "--set-conf=serial_handshake=" + hamlib_handshake
      );
    }

    // hamlib dcd setting
    if (document.getElementById("hamlib_dcd").value !== "ignore") {
      var hamlib_dcd = document.getElementById("hamlib_dcd").value;
      paramList = paramList.concat("--dcd-type=" + hamlib_dcd);
    }

    // hamlib ptt port
    if (document.getElementById("hamlib_ptt_port").value !== "ignore") {
      var hamlib_ptt_port = document.getElementById("hamlib_ptt_port").value;
      paramList = paramList.concat("--ptt-file=" + hamlib_ptt_port);
    }

    // hamlib ptt type
    if (document.getElementById("hamlib_pttprotocol").value !== "ignore") {
      var hamlib_ptt_type = document.getElementById("hamlib_pttprotocol").value;
      paramList = paramList.concat("--ptt-type=" + hamlib_ptt_type);
    }

    // hamlib dtr state
    if (document.getElementById("hamlib_dtrstate").value !== "ignore") {
      var hamlib_dtrstate = document.getElementById("hamlib_dtrstate").value;
      paramList = paramList.concat("--set-conf=dtr_state=" + hamlib_dtrstate);
    }

    var hamlib_rigctld_server_port = document.getElementById(
      "hamlib_rigctld_server_port"
    ).value;
    paramList = paramList.concat("--port=" + hamlib_rigctld_server_port);

    //Custom rigctld arguments to pass to rigctld
    var hamlib_rigctld_custom_args = document.getElementById(
      "hamlib_rigctld_custom_args"
    ).value;
    paramList = paramList.concat(hamlib_rigctld_custom_args);

    document.getElementById("hamlib_rigctld_command").value =
      paramList.join(" "); // join removes the commas

    console.log(paramList);
    //console.log(rigctldPath);
    return paramList;
  };

  document
    .getElementById("hamlib_rigctld_stop")
    .addEventListener("click", () => {
      ipcRenderer.send("request-stop-rigctld", {
        path: "123",
        parameters: "--version",
      });
    });

  // on click waterfall scatter toggle view
  // waterfall
  document
    .getElementById("waterfall-scatter-switch1")
    .addEventListener("click", () => {
      document.getElementById("chart").style.visibility = "hidden";
      document.getElementById("chart").style.display = "none";
      document.getElementById("chart").style.height = "0px";

      document.getElementById("scatter").style.height = "0px";
      document.getElementById("scatter").style.display = "none";
      document.getElementById("scatter").style.visibility = "hidden";

      document.getElementById("waterfall").style.display = "block";
      document.getElementById("waterfall").style.visibility = "visible";
      document.getElementById("waterfall").style.height = "100%";

      config.spectrum = "waterfall";
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
  // scatter
  document
    .getElementById("waterfall-scatter-switch2")
    .addEventListener("click", () => {
      document.getElementById("scatter").style.display = "block";
      document.getElementById("scatter").style.visibility = "visible";
      document.getElementById("scatter").style.height = "100%";

      document.getElementById("waterfall").style.visibility = "hidden";
      document.getElementById("waterfall").style.height = "0px";
      document.getElementById("waterfall").style.display = "none";

      document.getElementById("chart").style.visibility = "hidden";
      document.getElementById("chart").style.height = "0px";
      document.getElementById("chart").style.display = "none";

      config.spectrum = "scatter";
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
  // chart
  document
    .getElementById("waterfall-scatter-switch3")
    .addEventListener("click", () => {
      document.getElementById("waterfall").style.visibility = "hidden";
      document.getElementById("waterfall").style.height = "0px";
      document.getElementById("waterfall").style.display = "none";

      document.getElementById("scatter").style.height = "0px";
      document.getElementById("scatter").style.visibility = "hidden";
      document.getElementById("scatter").style.display = "none";

      document.getElementById("chart").style.height = "100%";
      document.getElementById("chart").style.display = "block";
      document.getElementById("chart").style.visibility = "visible";

      config.spectrum = "chart";
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

  // on click remote tnc toggle view
  document
    .getElementById("local-remote-switch1")
    .addEventListener("click", () => {
      document.getElementById("local-remote-switch1").checked = true;
      document.getElementById("local-remote-switch2").checked = false;
      document.getElementById("remote-tnc-field").style.visibility = "hidden";
      config.tnclocation = "localhost";
      toggleClass("remote-tnc-field", "d-none", true);
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
  document
    .getElementById("local-remote-switch2")
    .addEventListener("click", () => {
      document.getElementById("local-remote-switch1").checked = false;
      document.getElementById("local-remote-switch2").checked = true;
      document.getElementById("remote-tnc-field").style.visibility = "visible";
      config.tnclocation = "remote";
      toggleClass("remote-tnc-field", "d-none", false);
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

  // on change ping callsign
  document.getElementById("dxCall").addEventListener("change", () => {
    document.getElementById("dataModalDxCall").value =
      document.getElementById("dxCall").value;
  });
  // on change ping callsign
  document.getElementById("dataModalDxCall").addEventListener("change", () => {
    document.getElementById("dxCall").value =
      document.getElementById("dataModalDxCall").value;
  });

  // on change port and host
  document.getElementById("tnc_adress").addEventListener("change", () => {
    console.log(document.getElementById("tnc_adress").value);
    config.tnc_host = document.getElementById("tnc_adress").value;
    config.daemon_host = document.getElementById("tnc_adress").value;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    let Data = {
      port: document.getElementById("tnc_port").value,
      adress: document.getElementById("tnc_adress").value,
    };
    ipcRenderer.send("request-update-tnc-ip", Data);

    Data = {
      port: parseInt(document.getElementById("tnc_port").value) + 1,
      adress: document.getElementById("tnc_adress").value,
    };
    ipcRenderer.send("request-update-daemon-ip", Data);
  });

  // on change tnc port
  document.getElementById("tnc_port").addEventListener("change", () => {
    config.tnc_port = document.getElementById("tnc_port").value;
    config.daemon_port =
      parseInt(document.getElementById("tnc_port").value) + 1;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    let Data = {
      port: document.getElementById("tnc_port").value,
      adress: document.getElementById("tnc_adress").value,
    };
    ipcRenderer.send("request-update-tnc-ip", Data);

    Data = {
      port: parseInt(document.getElementById("tnc_port").value) + 1,
      adress: document.getElementById("tnc_adress").value,
    };
    ipcRenderer.send("request-update-daemon-ip", Data);
  });

  // on change audio TX Level
  document.getElementById("audioLevelTX").addEventListener("change", () => {
    var tx_audio_level = parseInt(
      document.getElementById("audioLevelTX").value
    );
    document.getElementById("audioLevelTXvalue").innerHTML = tx_audio_level;
    config.tx_audio_level = tx_audio_level;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    let Data = {
      command: "set_tx_audio_level",
      tx_audio_level: tx_audio_level,
    };
    ipcRenderer.send("run-tnc-command", Data);
  });
  document.getElementById("sendTestFrame").addEventListener("click", () => {
    let Data = {
      type: "set",
      command: "send_test_frame",
    };
    ipcRenderer.send("run-tnc-command", Data);
  });
  // saveMyCall button clicked
  document.getElementById("myCall").addEventListener("input", () => {
    callsign = document.getElementById("myCall").value;
    ssid = document.getElementById("myCallSSID").value;
    callsign_ssid = callsign.toUpperCase() + "-" + ssid;
    config.mycall = callsign_ssid;
    // split document title by looking for Call then split and update it
    //var documentTitle = document.title.split('Call:')
    //document.title = documentTitle[0] + 'Call: ' + callsign_ssid;
    updateTitle(callsign_ssid);
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    daemon.saveMyCall(callsign_ssid);
  });

  // saveMyGrid button clicked
  document.getElementById("myGrid").addEventListener("input", () => {
    grid = document.getElementById("myGrid").value;
    config.mygrid = grid;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    daemon.saveMyGrid(grid);
  });

  // startPing button clicked
  document.getElementById("sendPing").addEventListener("click", () => {
    var dxcallsign = document.getElementById("dxCall").value.toUpperCase();
    if (dxcallsign == "" || dxcallsign == null || dxcallsign == undefined)
      return;
    pauseButton(document.getElementById("sendPing"), 2000);
    sock.sendPing(dxcallsign);
  });

  // dataModalstartPing button clicked
  document.getElementById("dataModalSendPing").addEventListener("click", () => {
    var dxcallsign = document.getElementById("dataModalDxCall").value;
    dxcallsign = dxcallsign.toUpperCase();
    sock.sendPing(dxcallsign);
  });

  // close app, update and restart
  document
    .getElementById("update_and_install")
    .addEventListener("click", () => {
      ipcRenderer.send("request-restart-and-install");
    });

  /*disabled because it's causing confusion TODO: remove entire code some day
  // open arq session
  document.getElementById("openARQSession").addEventListener("click", () => {
    var dxcallsign = document.getElementById("dataModalDxCall").value;
    dxcallsign = dxcallsign.toUpperCase();
    sock.connectARQ(dxcallsign);
  });

  // close arq session
  document.getElementById("closeARQSession").addEventListener("click", () => {
    sock.disconnectARQ();
  });
*/
  // sendCQ button clicked
  document.getElementById("sendCQ").addEventListener("click", () => {
    pauseButton(document.getElementById("sendCQ"), 2000);
    sock.sendCQ();
  });

  // Start beacon button clicked
  document.getElementById("startBeacon").addEventListener("click", () => {
    let bcn = document.getElementById("startBeacon");
    bcn.disabled = true;
    interval = document.getElementById("beaconInterval").value;
    //Use class list to determine state of beacon, secondary == off
    if (bcn.className.toLowerCase().indexOf("secondary") > 0) {
      //Stopped; let us start it
      sock.startBeacon(interval);
    } else {
      sock.stopBeacon();
    }
    config.beacon_interval = interval;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    bcn.disabled = false;
  });

  // sendscatter Switch clicked
  document.getElementById("scatterSwitch").addEventListener("click", () => {
    console.log(document.getElementById("scatterSwitch").checked);
    if (document.getElementById("scatterSwitch").checked == true) {
      config.enable_scatter = "True";
    } else {
      config.enable_scatter = "False";
    }
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  // sendfft Switch clicked
  document.getElementById("fftSwitch").addEventListener("click", () => {
    if (document.getElementById("fftSwitch").checked == true) {
      config.enable_fft = "True";
    } else {
      config.enable_fft = "False";
    }
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  // enable 500z Switch clicked
  document.getElementById("500HzModeSwitch").addEventListener("click", () => {
    if (document.getElementById("500HzModeSwitch").checked == true) {
      config.low_bandwidth_mode = "True";
    } else {
      config.low_bandwidth_mode = "False";
    }
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  // enable response to cq clicked
  document.getElementById("respondCQSwitch").addEventListener("click", () => {
    if (document.getElementById("respondCQSwitch").checked == true) {
      config.respond_to_cq = "True";
    } else {
      config.respond_to_cq = "False";
    }
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  // enable explorer Switch clicked
  document.getElementById("ExplorerSwitch").addEventListener("click", () => {
    if (document.getElementById("ExplorerSwitch").checked == true) {
      config.enable_explorer = "True";
    } else {
      config.enable_explorer = "False";
    }
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });
  // enable explorer stats Switch clicked
  document
    .getElementById("ExplorerStatsSwitch")
    .addEventListener("click", () => {
      if (document.getElementById("ExplorerStatsSwitch").checked == true) {
        config.explorer_stats = "True";
      } else {
        config.explorer_stats = "False";
      }
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
  // enable autotune Switch clicked
  document.getElementById("autoTuneSwitch").addEventListener("click", () => {
    if (document.getElementById("autoTuneSwitch").checked == true) {
      config.auto_tune = "True";
    } else {
      config.auto_tune = "False";
    }
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });
  document.getElementById("GraphicsSwitch").addEventListener("click", () => {
    if (document.getElementById("GraphicsSwitch").checked == true) {
      config.high_graphics = "True";
    } else {
      config.high_graphics = "False";
    }
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    set_CPU_mode();
  });

  // enable fsk Switch clicked
  document.getElementById("fskModeSwitch").addEventListener("click", () => {
    if (document.getElementById("fskModeSwitch").checked == true) {
      config.enable_fsk = "True";
    } else {
      config.enable_fsk = "False";
    }
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  // enable is writing switch clicked
  document.getElementById("enable_is_writing").addEventListener("click", () => {
    if (document.getElementById("enable_is_writing").checked == true) {
      config.enable_is_writing = "True";
    } else {
      config.enable_is_writing = "False";
    }
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  // Tuning range clicked
  document.getElementById("tuning_range_fmin").addEventListener("click", () => {
    var tuning_range_fmin = document.getElementById("tuning_range_fmin").value;
    config.tuning_range_fmin = tuning_range_fmin;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  document.getElementById("tuning_range_fmax").addEventListener("click", () => {
    var tuning_range_fmax = document.getElementById("tuning_range_fmax").value;
    config.tuning_range_fmax = tuning_range_fmax;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  // Theme selector clicked
  document.getElementById("theme_selector").addEventListener("change", () => {
    var theme = document.getElementById("theme_selector").value;
    if (theme != "default") {
      var theme_path =
        "../node_modules/bootswatch/dist/" + theme + "/bootstrap.min.css";
    } else {
      var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
    }

    //update path to css file
    document.getElementById("bootstrap_theme").href = escape(theme_path);

    config.theme = theme;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  // Waterfall theme selector changed
  document.getElementById("wftheme_selector").addEventListener("change", () => {
    var wftheme = document.getElementById("wftheme_selector").value;
    spectrum.setColorMap(wftheme);
    config.wftheme = wftheme;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  // Update channel selector changed
  document
    .getElementById("update_channel_selector")
    .addEventListener("change", () => {
      config.update_channel = document.getElementById(
        "update_channel_selector"
      ).value;
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
      console.log("Autoupdate channel changed to ", config.update_channel);
    });

  // rx buffer size selector clicked
  document.getElementById("rx_buffer_size").addEventListener("click", () => {
    var rx_buffer_size = document.getElementById("rx_buffer_size").value;
    config.rx_buffer_size = rx_buffer_size;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  //screen size
  window.addEventListener("resize", () => {
    config.screen_height = window.innerHeight;
    config.screen_width = window.innerWidth;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  });

  // Explorer button clicked
  document.getElementById("openExplorer").addEventListener("click", () => {
    shell.openExternal(
      "https://explorer.freedata.app/?myCall=" +
        document.getElementById("myCall").value
    );
  });

  // Stats button clicked
  document.getElementById("btnStats").addEventListener("click", () => {
    shell.openExternal("https://statistics.freedata.app");
  });
  // GH Link clicked
  document.getElementById("fdWww").addEventListener("click", () => {
    shell.openExternal("https://freedata.app");
  });
  // GH Link clicked
  document.getElementById("ghUrl").addEventListener("click", () => {
    shell.openExternal("https://github.com/DJ2LS/FreeDATA");
  });
  // Wiki Link clicked
  document.getElementById("wikiUrl").addEventListener("click", () => {
    shell.openExternal("https://wiki.freedata.app");
  });
  // Groups.io Link clicked
  document.getElementById("groupsioUrl").addEventListener("click", () => {
    shell.openExternal("https://groups.io/g/freedata");
  });
  // Discord Link clicked
  document.getElementById("discordUrl").addEventListener("click", () => {
    shell.openExternal("https://discord.gg/jnADeDtxUF");
  });
  // startTNC button clicked
  document.getElementById("startTNC").addEventListener("click", () => {
    var tuning_range_fmin = document.getElementById("tuning_range_fmin").value;
    var tuning_range_fmax = document.getElementById("tuning_range_fmax").value;

    var rigctld_ip = document.getElementById("hamlib_rigctld_ip").value;
    var rigctld_port = document.getElementById("hamlib_rigctld_port").value;
    var hamlib_rigctld_server_port = document.getElementById(
      "hamlib_rigctld_server_port"
    ).value;

    var deviceid = document.getElementById("hamlib_deviceid").value;
    var deviceport = document.getElementById("hamlib_deviceport").value;
    var serialspeed = document.getElementById("hamlib_serialspeed").value;
    var pttprotocol = document.getElementById("hamlib_pttprotocol").value;
    var hamlib_dcd = document.getElementById("hamlib_dcd").value;

    var mycall = document.getElementById("myCall").value;
    var ssid = document.getElementById("myCallSSID").value;
    callsign_ssid = mycall.toUpperCase() + "-" + ssid;

    var mygrid = document.getElementById("myGrid").value;

    var rx_audio = document.getElementById("audio_input_selectbox").value;
    var tx_audio = document.getElementById("audio_output_selectbox").value;

    var pttport = document.getElementById("hamlib_ptt_port").value;
    var data_bits = document.getElementById("hamlib_data_bits").value;
    var stop_bits = document.getElementById("hamlib_stop_bits").value;
    var handshake = document.getElementById("hamlib_handshake").value;

    if (document.getElementById("scatterSwitch").checked == true) {
      var enable_scatter = "True";
    } else {
      var enable_scatter = "False";
    }

    if (document.getElementById("fftSwitch").checked == true) {
      var enable_fft = "True";
    } else {
      var enable_fft = "False";
    }

    if (document.getElementById("500HzModeSwitch").checked == true) {
      var low_bandwidth_mode = "True";
    } else {
      var low_bandwidth_mode = "False";
    }

    if (document.getElementById("fskModeSwitch").checked == true) {
      var enable_fsk = "True";
    } else {
      var enable_fsk = "False";
    }

    if (document.getElementById("respondCQSwitch").checked == true) {
      var respond_to_cq = "True";
    } else {
      var respond_to_cq = "False";
    }

    if (document.getElementById("ExplorerSwitch").checked == true) {
      var enable_explorer = "True";
    } else {
      var enable_explorer = "False";
    }

    if (document.getElementById("ExplorerStatsSwitch").checked == true) {
      var explorer_stats = "True";
    } else {
      var explorer_stats = "False";
    }

    if (document.getElementById("autoTuneSwitch").checked == true) {
      var auto_tune = "True";
    } else {
      var auto_tune = "False";
    }
    // loop through audio device list and select
    for (
      i = 0;
      i < document.getElementById("audio_input_selectbox").length;
      i++
    ) {
      device = document.getElementById("audio_input_selectbox")[i];

      if (device.value == rx_audio) {
        console.log(device.text);
        config.rx_audio = device.text;
      }
    }

    // loop through audio device list and select
    for (
      i = 0;
      i < document.getElementById("audio_output_selectbox").length;
      i++
    ) {
      device = document.getElementById("audio_output_selectbox")[i];

      if (device.value == tx_audio) {
        console.log(device.text);
        config.tx_audio = device.text;
      }
    }

    if (!document.getElementById("radio-control-switch-disabled").checked) {
      var radiocontrol = "rigctld";
    } else {
      var radiocontrol = "disabled";
    }

    var tx_audio_level = document.getElementById("audioLevelTX").value;
    var rx_buffer_size = document.getElementById("rx_buffer_size").value;

    config.radiocontrol = radiocontrol;
    config.mycall = callsign_ssid;
    config.mygrid = mygrid;
    config.hamlib_deviceid = deviceid;
    config.hamlib_deviceport = deviceport;
    config.hamlib_serialspeed = serialspeed;
    config.hamlib_pttprotocol = pttprotocol;
    config.hamlib_ptt_port = pttport;
    config.hamlib_data_bits = data_bits;
    config.hamlib_stop_bits = stop_bits;
    config.hamlib_handshake = handshake;
    config.hamlib_dcd = hamlib_dcd;
    config.hamlib_rigctld_port = rigctld_port;
    config.hamlib_rigctld_ip = rigctld_ip;
    config.hamlib_rigctld_server_port = hamlib_rigctld_server_port;
    config.enable_scatter = enable_scatter;
    config.enable_fft = enable_fft;
    config.enable_fsk = enable_fsk;
    config.low_bandwidth_mode = low_bandwidth_mode;
    config.tx_audio_level = tx_audio_level;
    config.respond_to_cq = respond_to_cq;
    config.rx_buffer_size = rx_buffer_size;
    config.enable_explorer = enable_explorer;
    config.explorer_stats = explorer_stats;
    config.auto_tune = auto_tune;

    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    daemon.startTNC(
      callsign_ssid,
      mygrid,
      rx_audio,
      tx_audio,
      radiocontrol,
      deviceid,
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
      auto_tune
    );
  });

  document.getElementById("tncLog").addEventListener("click", () => {
    ipcRenderer.send("request-open-tnc-log");
  });

  // stopTNC button clicked
  document.getElementById("stopTNC").addEventListener("click", () => {
    if (!confirm("Stop the TNC?")) return;

    daemon.stopTNC();
  });

  // TEST HAMLIB
  document.getElementById("testHamlib").addEventListener("click", () => {
    var data_bits = document.getElementById("hamlib_data_bits").value;
    var stop_bits = document.getElementById("hamlib_stop_bits").value;
    var handshake = document.getElementById("hamlib_handshake").value;
    var pttport = document.getElementById("hamlib_ptt_port").value;

    var rigctld_ip = document.getElementById("hamlib_rigctld_ip").value;
    var rigctld_port = document.getElementById("hamlib_rigctld_port").value;

    var deviceid = document.getElementById("hamlib_deviceid").value;
    var deviceport = document.getElementById("hamlib_deviceport").value;
    var serialspeed = document.getElementById("hamlib_serialspeed").value;
    var pttprotocol = document.getElementById("hamlib_pttprotocol").value;

    if (document.getElementById("radio-control-switch-disabled").checked) {
      var radiocontrol = "disabled";
    } else {
      var radiocontrol = "rigctld";
    }

    daemon.testHamlib(
      radiocontrol,
      deviceid,
      deviceport,
      serialspeed,
      pttprotocol,
      pttport,
      data_bits,
      stop_bits,
      handshake,
      rigctld_ip,
      rigctld_port
    );
  });

  // START TRANSMISSION
  document.getElementById("startTransmission").addEventListener("click", () => {
    var fileList = document.getElementById("dataModalFile").files;
    console.log(fileList);
    var reader = new FileReader();
    reader.readAsBinaryString(fileList[0]);
    //reader.readAsDataURL(fileList[0]);

    reader.onload = function (e) {
      // binary data

      var data = e.target.result;
      console.log(data);

      let Data = {
        command: "send_file",
        dxcallsign: document
          .getElementById("dataModalDxCall")
          .value.toUpperCase(),
        mode: document.getElementById("datamode").value,
        frames: document.getElementById("framesperburst").value,
        filetype: fileList[0].type,
        filename: fileList[0].name,
        data: data,
        checksum: "123123123",
      };
      // only send command if dxcallsign entered and we have a file selected
      if (document.getElementById("dataModalDxCall").value.length > 0) {
        ipcRenderer.send("run-tnc-command", Data);
      }
    };
    reader.onerror = function (e) {
      // error occurred
      console.log("Error : " + e.type);
    };
  });
  // STOP TRANSMISSION
  document.getElementById("stopTransmission").addEventListener("click", () => {
    let Data = {
      command: "stop_transmission",
    };
    ipcRenderer.send("run-tnc-command", Data);
  });

  // STOP TRANSMISSION AND CONNECRTION
  document
    .getElementById("stop_transmission_connection")
    .addEventListener("click", () => {
      let Data = {
        command: "stop_transmission",
      };
      ipcRenderer.send("run-tnc-command", Data);
      sock.disconnectARQ();
    });

  // OPEN CHAT MODULE
  document.getElementById("openRFChat").addEventListener("click", () => {
    let Data = {
      command: "openRFChat",
    };
    ipcRenderer.send("request-show-chat-window", Data);
  });
});

function connectedStation(data) {
  if (typeof data.dxcallsign == "undefined") {
    return;
  }
  if (
    !(typeof data.arq == "undefined") &&
    data.arq.toLowerCase() == "session"
  ) {
    var prefix = "w/ ";
  } else {
    switch (data.irs) {
      case "True":
        //We are receiving station
        var prefix = "de ";
        break;
      case "False":
        //We are sending station
        var prefix = "to ";
        break;
      default:
        //Shouldn't happen
        console.trace("No data.irs data in tnc-message");
        var prefix = "";
        break;
    }
  }
  document.getElementById("txtConnectedWith").textContent =
    prefix + data.dxcallsign;
}

//Listen for events caused by tnc 'tnc-message' rx
ipcRenderer.on("action-update-reception-status", (event, arg) => {
  var data = arg["data"][0];
  var txprog = document.getElementById("transmission_progress");
  ipcRenderer.send("request-show-electron-progressbar", data.percent);
  txprog.setAttribute("aria-valuenow", data.percent);
  txprog.setAttribute("style", "width:" + data.percent + "%;");

  // SET TIME LEFT UNTIL FINIHED
  if (typeof data.finished == "undefined") {
    var time_left = "time left: estimating";
  } else {
    var arq_seconds_until_finish = data.finished;
    var hours = Math.floor(arq_seconds_until_finish / 3600);
    var minutes = Math.floor((arq_seconds_until_finish % 3600) / 60);
    var seconds = arq_seconds_until_finish % 60;
    if (hours < 0) {
      hours = 0;
    }
    if (minutes < 0) {
      minutes = 0;
    }
    if (seconds < 0) {
      seconds = 0;
    }
    if (hours > 0) {
      time_left =
        "time left: ~" +
        hours.toString().padStart(2, "0") +
        ":" +
        minutes.toString().padStart(2, "0") +
        "." +
        seconds.toString().padStart(2, "0");
    } else {
      time_left =
        "time left: ~" +
        minutes.toString().padStart(2, "0") +
        "." +
        seconds.toString().padStart(2, "0");
    }
  }
  var time_left = "<strong>" + time_left + " || Speed/min: ";

  // SET BYTES PER MINUTE
  if (typeof data.bytesperminute == "undefined") {
    var arq_bytes_per_minute = 0;
  } else {
    var arq_bytes_per_minute = data.bytesperminute;
  }

  // SET BYTES PER MINUTE COMPRESSED
  var compress = data.compression;
  if (isNaN(compress)) {
    compress = 1;
  }
  var arq_bytes_per_minute_compressed = Math.round(
    arq_bytes_per_minute * compress
  );

  time_left +=
    formatBytes(arq_bytes_per_minute, 1) +
    " (comp: " +
    formatBytes(arq_bytes_per_minute_compressed, 1) +
    ")</strong>";

  document.getElementById("transmission_timeleft").innerHTML = time_left;
  connectedStation(data);
});

//Listen for events caused by tnc 'tnc-message's tx
ipcRenderer.on("action-update-transmission-status", (event, arg) => {
  var data = arg["data"][0];
  var txprog = document.getElementById("transmission_progress");
  ipcRenderer.send("request-show-electron-progressbar", data.percent);
  txprog.setAttribute("aria-valuenow", data.percent);
  txprog.setAttribute("style", "width:" + data.percent + "%;");

  // SET TIME LEFT UNTIL FINIHED
  if (typeof data.finished == "undefined") {
    var time_left = "time left: estimating";
  } else {
    var arq_seconds_until_finish = data.finished;
    var hours = Math.floor(arq_seconds_until_finish / 3600);
    var minutes = Math.floor((arq_seconds_until_finish % 3600) / 60);
    var seconds = arq_seconds_until_finish % 60;
    if (hours < 0) {
      hours = 0;
    }
    if (minutes < 0) {
      minutes = 0;
    }
    if (seconds < 0) {
      seconds = 0;
    }
    if (hours > 0) {
      time_left =
        "time left: ~" +
        hours.toString().padStart(2, "0") +
        ":" +
        minutes.toString().padStart(2, "0") +
        "." +
        seconds.toString().padStart(2, "0");
    } else {
      time_left =
        "time left: ~" +
        minutes.toString().padStart(2, "0") +
        "." +
        seconds.toString().padStart(2, "0");
    }
  }
  var time_left = "<strong>" + time_left + " || Speed/min: ";

  // SET BYTES PER MINUTE
  if (typeof data.bytesperminute == "undefined") {
    var arq_bytes_per_minute = 0;
  } else {
    var arq_bytes_per_minute = data.bytesperminute;
  }

  // SET BYTES PER MINUTE COMPRESSED
  var compress = data.compression;
  if (isNaN(compress)) {
    compress = 1;
  }
  var arq_bytes_per_minute_compressed = Math.round(
    arq_bytes_per_minute * compress
  );

  time_left +=
    formatBytes(arq_bytes_per_minute, 1) +
    " (comp: " +
    formatBytes(arq_bytes_per_minute_compressed, 1) +
    ")</strong>";
  document.getElementById("transmission_timeleft").innerHTML = time_left;
  connectedStation(data);
});

//Just some stuff I want to experiment with - n1qm
//https://gist.github.com/senseisimple/002cdba344de92748695a371cef0176a
function signal_quality_perc_quad(rssi, perfect_rssi = 10, worst_rssi = -150) {
  nominal_rssi = perfect_rssi - worst_rssi;
  signal_quality =
    (100 * (perfect_rssi - worst_rssi) * (perfect_rssi - worst_rssi) -
      (perfect_rssi - rssi) *
        (15 * (perfect_rssi - worst_rssi) + 62 * (perfect_rssi - rssi))) /
    ((perfect_rssi - worst_rssi) * (perfect_rssi - worst_rssi));

  if (signal_quality > 100) {
    signal_quality = 100;
  } else if (signal_quality < 1) {
    signal_quality = 0;
  }
  return Math.ceil(signal_quality);
}

var lastHeard = "";
ipcRenderer.on("action-update-tnc-state", (event, arg) => {
  // update FFT
  if (typeof arg.fft !== "undefined") {
    var array = JSON.parse("[" + arg.fft + "]");
    spectrum.addData(array[0]);
  }

  if (typeof arg.mycallsign !== "undefined") {
    updateTitle(arg.mycallsign);
  }

  // update mygrid information with data from tnc
  if (typeof arg.mygrid !== "undefined") {
    document.getElementById("myGrid").value = arg.mygrid;
  }

  // DATA STATE
  global.rxBufferLengthTnc = arg.rx_buffer_length;

  // START OF SCATTER CHART
  if (typeof arg.scatter == "undefined") {
    var scatterSize = 0;
  } else {
    var scatterSize = arg.scatter.length;
  }

  if (scatterSize > 0 && global.scatterData != newScatterData) {
    const scatterConfig = {
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: false,
        },
        annotation: {
          annotations: {
            line1: {
              type: "line",
              yMin: 0,
              yMax: 0,
              borderColor: "rgb(255, 99, 132)",
              borderWidth: 2,
            },
            line2: {
              type: "line",
              xMin: 0,
              xMax: 0,
              borderColor: "rgb(255, 99, 132)",
              borderWidth: 2,
            },
          },
        },
      },
      animations: false,
      scales: {
        x: {
          type: "linear",
          position: "bottom",
          display: true,
          min: -80,
          max: 80,
          ticks: {
            display: false,
          },
        },
        y: {
          display: true,
          min: -80,
          max: 80,
          ticks: {
            display: false,
          },
        },
      },
    };
    var scatterData = arg.scatter;
    var newScatterData = {
      datasets: [
        {
          //label: 'constellation diagram',
          data: scatterData,
          options: scatterConfig,
          backgroundColor: "rgb(255, 99, 132)",
        },
      ],
    };

    global.scatterData = newScatterData;

    if (typeof global.scatterChart == "undefined") {
      var scatterCtx = document.getElementById("scatter").getContext("2d");
      global.scatterChart = new Chart(scatterCtx, {
        type: "scatter",
        data: global.scatterData,
        options: scatterConfig,
      });
    } else {
      global.scatterChart.data = global.scatterData;
      global.scatterChart.update();
    }
  }
  // END OF SCATTER CHART

  // START OF SPEED CHART
  var speedDataTime = [];

  if (typeof arg.speed_list == "undefined") {
    var speed_listSize = 0;
  } else {
    var speed_listSize = arg.speed_list.length;
  }

  for (var i = 0; i < speed_listSize; i++) {
    var timestamp = arg.speed_list[i].timestamp * 1000;
    var h = new Date(timestamp).getHours();
    var m = new Date(timestamp).getMinutes();
    var s = new Date(timestamp).getSeconds();
    var time = h + ":" + m + ":" + s;
    speedDataTime.push(time);
  }

  var speedDataBpm = [];
  for (var i = 0; i < speed_listSize; i++) {
    speedDataBpm.push(arg.speed_list[i].bpm);
  }

  var speedDataSnr = [];
  for (var i = 0; i < speed_listSize; i++) {
    let snr = NaN;
    if (arg.speed_list[i].snr !== 0) {
      snr = arg.speed_list[i].snr;
    } else {
      snr = NaN;
    }
    speedDataSnr.push(snr);
  }

  var speedChartConfig = {
    type: "line",
  };

  // https://www.chartjs.org/docs/latest/samples/line/segments.html
  const skipped = (speedCtx, value) =>
    speedCtx.p0.skip || speedCtx.p1.skip ? value : undefined;
  const down = (speedCtx, value) =>
    speedCtx.p0.parsed.y > speedCtx.p1.parsed.y ? value : undefined;

  var newSpeedData = {
    labels: speedDataTime,
    datasets: [
      {
        type: "line",
        label: "SNR[dB]",
        data: speedDataSnr,
        borderColor: "rgb(75, 192, 192, 1.0)",
        pointRadius: 1,
        segment: {
          borderColor: (speedCtx) =>
            skipped(speedCtx, "rgb(0,0,0,0.4)") ||
            down(speedCtx, "rgb(192,75,75)"),
          borderDash: (speedCtx) => skipped(speedCtx, [3, 3]),
        },
        spanGaps: true,
        backgroundColor: "rgba(75, 192, 192, 0.2)",
        order: 1,
        yAxisID: "SNR",
      },
      {
        type: "bar",
        label: "Speed[bpm]",
        data: speedDataBpm,
        borderColor: "rgb(120, 100, 120, 1.0)",
        backgroundColor: "rgba(120, 100, 120, 0.2)",
        order: 0,
        yAxisID: "SPEED",
      },
    ],
  };

  var speedChartOptions = {
    responsive: true,
    animations: true,
    cubicInterpolationMode: "monotone",
    tension: 0.4,
    scales: {
      SNR: {
        type: "linear",
        ticks: { beginAtZero: false, color: "rgb(255, 99, 132)" },
        position: "right",
      },
      SPEED: {
        type: "linear",
        ticks: { beginAtZero: false, color: "rgb(120, 100, 120)" },
        position: "left",
        grid: {
          drawOnChartArea: false, // only want the grid lines for one axis to show up
        },
      },
      x: { ticks: { beginAtZero: true } },
    },
  };

  if (typeof global.speedChart == "undefined") {
    var speedCtx = document.getElementById("chart").getContext("2d");
    global.speedChart = new Chart(speedCtx, {
      data: newSpeedData,
      options: speedChartOptions,
    });
  } else {
    if (speedDataSnr.length > 0) {
      global.speedChart.data = newSpeedData;
      global.speedChart.update();
    }
  }
  // END OF SPEED CHART

  // PTT STATE
  switch (arg.ptt_state) {
    case "True":
      document.getElementById("ptt_state").className = "btn btn-sm btn-danger";
      break;
    case "False":
      document.getElementById("ptt_state").className = "btn btn-sm btn-success";
      break;
    default:
      document.getElementById("ptt_state").className =
        "btn btn-sm btn-secondary";
      break;
  }

  // AUDIO RECORDING
  if (arg.audio_recording == "True") {
    document.getElementById("startStopRecording").textContent = "Stop Rec";
  } else {
    document.getElementById("startStopRecording").textContent = "Start Rec";
  }
  //CHANNEL CODEC2 BUSY STATE
  if (arg.is_codec2_traffic == "True") {
    document.getElementById("c2_busy").className = "btn btn-sm btn-success";
  } else {
    document.getElementById("c2_busy").className =
      "btn btn-sm btn-outline-secondary";
  }
  // CHANNEL BUSY STATE
  switch (arg.channel_busy) {
    case "True":
      document.getElementById("channel_busy").className =
        "btn btn-sm btn-danger";
      break;
    case "False":
      document.getElementById("channel_busy").className =
        "btn btn-sm btn-success";
      break;
    default:
      document.getElementById("channel_busy").className =
        "btn btn-sm btn-secondary";
      break;
  }

  // BUSY STATE
  switch (arg.busy_state) {
    case "BUSY":
      document.getElementById("busy_state").className = "btn btn-sm btn-danger";
      //Seems to be no longer user accessible
      //document.getElementById("startTransmission").disabled = true;
      break;
    case "IDLE":
      document.getElementById("busy_state").className =
        "btn btn-sm btn-success";
      break;
    default:
      document.getElementById("busy_state").className =
        "btn btn-sm btn-secondary";
      //Seems to be no longer user accessible
      //document.getElementById("startTransmission").disabled = true;
      break;
  }

  // ARQ STATE
  switch (arg.arq_state) {
    case "True":
      document.getElementById("arq_state").className = "btn btn-sm btn-warning";
      //Seems to be no longer user accessible
      //document.getElementById("startTransmission").disabled = false;
      break;
    default:
      document.getElementById("arq_state").className =
        "btn btn-sm btn-secondary";
      //Seems to be no longer user accessible
      //document.getElementById("startTransmission").disabled = false;
      break;
  }

  // ARQ SESSION
  switch (arg.arq_session) {
    case "True":
      document.getElementById("arq_session").className =
        "btn btn-sm btn-warning";
      break;
    default:
      document.getElementById("arq_session").className =
        "btn btn-sm btn-secondary";
      break;
  }

  if (arg.arq_state == "True" || arg.arq_session == "True") {
    document.getElementById("spnConnectedWith").className =
      "bi bi-chat-fill text-success";
  } else {
    document.getElementById("spnConnectedWith").className = "bi bi-chat-fill";
  }

  // HAMLIB STATUS
  if (arg.hamlib_status == "connected") {
    document.getElementById("rigctld_state").className =
      "btn btn-success btn-sm";
  } else {
    document.getElementById("rigctld_state").className =
      "btn btn-secondary btn-sm";
  }

  // BEACON
  switch (arg.beacon_state) {
    case "True":
      document.getElementById("startBeacon").className =
        "btn btn-sm btn-success";
      if (document.getElementById("beaconInterval").disabled == false) {
        document.getElementById("beaconInterval").disabled = true;
      }
      break;
    default:
      document.getElementById("startBeacon").className =
        "btn btn-sm btn-outline-secondary";
      if (document.getElementById("beaconInterval").disabled == true) {
        document.getElementById("beaconInterval").disabled = false;
      }
      break;
  }
  // dbfs
  // https://www.moellerstudios.org/converting-amplitude-representations/
  if (
    arg.dbfs_level.length != 0 &&
    !isNaN(arg.dbfs_level) &&
    dbfs_level_raw != arg.dbfs_level
  ) {
    dbfs_level_raw = arg.dbfs_level;
    dbfs_level = Math.pow(10, arg.dbfs_level / 20) * 100;

    document.getElementById("dbfs_level_value").textContent =
      Math.round(arg.dbfs_level) + " dBFS (Audio Level)";
    var dbfscntrl = document.getElementById("dbfs_level");
    dbfscntrl.setAttribute("aria-valuenow", dbfs_level);
    dbfscntrl.style = "width:" + dbfs_level + "%;";
    //dbfscntrl.setAttribute("style", "width:" + dbfs_level + "%;");
  }

  // noise / strength
  // https://www.moellerstudios.org/converting-amplitude-representations/

  if (
    arg.strength.length != 0 &&
    !isNaN(arg.strength) &&
    noise_level_raw != arg.strength
  ) {
    //console.log(arg.strength);
    noise_level_raw = arg.strength;
    noise_level = Math.pow(10, arg.strength / 20) * 100;

    document.getElementById("noise_level_value").textContent =
      Math.round(arg.strength) + " dB (S-Meter)";
    var noisecntrl = document.getElementById("noise_level");
    noisecntrl.setAttribute("aria-valuenow", noise_level);
    noisecntrl.style = "width:" + noise_level + "%;";
    //noisecntrl.setAttribute("style", "width:" + noise_level + "%;");
  }

  // SET FREQUENCY
  // https://stackoverflow.com/a/2901298
  var freq = arg.frequency.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  document.getElementById("frequency").textContent = freq;
  //document.getElementById("newFrequency").value = arg.frequency;

  // SET MODE
  document.getElementById("mode").textContent = arg.mode;

  // SET bandwidth
  document.getElementById("bandwidth").textContent = arg.bandwidth;

  // SET SPEED LEVEL
  switch (arg.speed_level) {
    case "0":
      document.getElementById("speed_level").className = "bi bi-reception-1";
      break;
    case "1":
      document.getElementById("speed_level").className = "bi bi-reception-2";
      break;
    case "2":
      document.getElementById("speed_level").className = "bi bi-reception-3";
      break;
    default:
      document.getElementById("speed_level").className = "bi bi-reception-4";
      break;
  }

  // SET TOTAL BYTES
  if (typeof arg.total_bytes == "undefined") {
    var total_bytes = 0;
  } else {
    var total_bytes = arg.total_bytes;
  }
  document.getElementById("total_bytes").textContent = total_bytes;

  //Check if heard station list has changed
  if (
    typeof arg.stations != "undefined" &&
    arg.stations.length > 0 &&
    JSON.stringify(arg.stations) != lastHeard
  ) {
    //console.log("Updating last heard stations");
    lastHeard = JSON.stringify(arg.stations);
    updateHeardStations(arg);
  }
});

function updateHeardStations(arg) {
  // UPDATE HEARD STATIONS

  var tbl = document.getElementById("heardstations");
  tbl.innerHTML = "";

  if (typeof arg.stations == "undefined") {
    var heardStationsLength = 0;
  } else {
    var heardStationsLength = arg.stations.length;
  }

  for (i = 0; i < heardStationsLength; i++) {
    // first we update the PING window
    if (
      arg.stations[i]["dxcallsign"] ==
      document.getElementById("dxCall").value.toUpperCase()
    ) {
      var dxGrid = arg.stations[i]["dxgrid"];
      var myGrid = document.getElementById("myGrid").value;
      try {
        var dist = parseInt(distance(myGrid, dxGrid)) + " km";
        document.getElementById("dataModalPingDistance").textContent = dist;
      } catch {
        document.getElementById("dataModalPingDistance").textContent = "---";
      }
      document.getElementById("dataModalPingDB").textContent =
        arg.stations[i]["snr"];
    }

    // now we update the heard stations list
    var row = document.createElement("tr");
    //https://stackoverflow.com/q/51421470

    //https://stackoverflow.com/a/847196
    timestampRaw = arg.stations[i]["timestamp"];
    var date = new Date(timestampRaw * 1000);
    var hours = date.getHours();
    var minutes = "0" + date.getMinutes();
    var seconds = "0" + date.getSeconds();
    var datetime = hours + ":" + minutes.substr(-2) + ":" + seconds.substr(-2);

    var timestamp = document.createElement("td");
    var timestampText = document.createElement("span");
    timestampText.innerText = datetime;
    timestamp.appendChild(timestampText);

    var frequency = document.createElement("td");
    var frequencyText = document.createElement("span");
    frequencyText.innerText = arg.stations[i]["frequency"];
    frequency.appendChild(frequencyText);

    var dxCall = document.createElement("td");
    var dxCallText = document.createElement("span");
    dxCallText.innerText = arg.stations[i]["dxcallsign"];
    let dxCallTextCall = dxCallText.innerText;
    let dxCallTextShort = dxCallTextCall.split("-", 1)[0];
    row.addEventListener("click", function () {
      document.getElementById("dxCall").value = dxCallTextCall;
    });
    dxCall.appendChild(dxCallText);

    var dxGrid = document.createElement("td");
    var dxGridText = document.createElement("span");
    dxGridText.innerText = arg.stations[i]["dxgrid"];
    dxGrid.appendChild(dxGridText);

    var gridDistance = document.createElement("td");
    var gridDistanceText = document.createElement("span");

    try {
      if (arg.stations[i]["dxgrid"].toString() != "------") {
        gridDistanceText.innerText =
          parseInt(
            distance(
              document.getElementById("myGrid").value,
              arg.stations[i]["dxgrid"]
            )
          ) + " km";
      } else {
        gridDistanceText.innerText = "---";
      }
    } catch {
      gridDistanceText.innerText = "---";
    }
    gridDistance.appendChild(gridDistanceText);

    var dataType = document.createElement("td");
    var dataTypeText = document.createElement("span");
    dataTypeText.innerText = arg.stations[i]["datatype"];
    dataType.appendChild(dataTypeText);

    switch (dataTypeText.innerText) {
      case "CQ CQ CQ":
        dataTypeText.textContent = "CQ CQ";
        row.classList.add("table-success");
        break;
      case "DATA-CHANNEL":
        dataTypeText.innerHTML =
          '<i title="Data Channel" class="bi bi-file-earmark-binary-fill"></i>';
        row.classList.add("table-warning");
        break;
      case "BEACON":
        dataTypeText.textContent = "BCN";
        row.classList.add("table-light");
        break;
      case "PING":
        row.classList.add("table-info");
        break;
      case "PING-ACK":
        row.classList.add("table-primary");
        break;
      case "SESSION-HB":
        dataTypeText.innerHTML =
          '<i title="Heartbeat" class="bi bi-heart-pulse-fill"></i>';
        //dataType.appendChild(dataTypeText);
        break;
    }
    var snr = document.createElement("td");
    var snrText = document.createElement("span");
    snrText.innerText = arg.stations[i]["snr"];
    snr.appendChild(snrText);

    var offset = document.createElement("td");
    var offsetText = "&nbsp;";
    if (contrib.indexOf(dxCallTextShort) >= 0) {
      var offsetText =
        '<i title="Yeah baby, yeah!!!!" class="bi bi-award-fill text-primary"></i>';
    } else {
      if (dxCallTextShort == "DJ2LS") {
        var offsetText =
          '<i title="Yeah FreeDATA, yeah!!!!" class="bi bi-emoji-wink-fill text-warning"></i>';
      }
    }
    offset.innerHTML = offsetText;

    row.appendChild(timestamp);
    row.appendChild(frequency);
    row.appendChild(offset);
    row.appendChild(dxCall);
    row.appendChild(dxGrid);
    row.appendChild(gridDistance);
    row.appendChild(dataType);
    row.appendChild(snr);

    tbl.appendChild(row);
  }
}

ipcRenderer.on("action-update-daemon-state", (event, arg) => {
  /*
    // deactivetd RAM und CPU view so we dont get errors. We need to find a new place for this feature
    // RAM
    document.getElementById("progressbar_ram").setAttribute("aria-valuenow", arg.ram_usage)
    document.getElementById("progressbar_ram").setAttribute("style", "width:" + arg.ram_usage + "%;")
    document.getElementById("progressbar_ram_value").innerHTML = arg.ram_usage + "%"

    // CPU
    document.getElementById("progressbar_cpu").setAttribute("aria-valuenow", arg.cpu_usage)
    document.getElementById("progressbar_cpu").setAttribute("style", "width:" + arg.cpu_usage + "%;")
    document.getElementById("progressbar_cpu_value").innerHTML = arg.cpu_usage + "%"
    */
  /*
    document.getElementById("ram_load").innerHTML = arg.ram_usage + "%"    
    document.getElementById("cpu_load").innerHTML = arg.cpu_usage + "%"
    */
  // OPERATING SYSTEM
  //document.getElementById("operating_system").innerHTML = "OS " + os.type()

  /*
    // PYTHON VERSION
    document.getElementById("python_version").innerHTML = "Python " + arg.python_version
    document.getElementById("python_version").className = "btn btn-sm btn-success";    
    */
  /*
    // HAMLIB VERSION
    document.getElementById("hamlib_version").innerHTML = "Hamlib " + arg.hamlib_version
    document.getElementById("hamlib_version").className = "btn btn-sm btn-success";
    */
  /*
    // NODE VERSION
    document.getElementById("node_version").innerHTML = "Node " + process.version
    document.getElementById("node_version").className = "btn btn-sm btn-success";
    */

  // UPDATE AUDIO INPUT
  if (arg.tnc_running_state == "stopped") {
    if (
      document.getElementById("audio_input_selectbox").length !=
      arg.input_devices.length
    ) {
      document.getElementById("audio_input_selectbox").innerHTML = "";
      for (i = 0; i < arg.input_devices.length; i++) {
        var option = document.createElement("option");
        option.text = arg.input_devices[i]["name"];
        option.value = arg.input_devices[i]["id"];
        // set device from config if available

        if (config.rx_audio == option.text) {
          option.setAttribute("selected", true);
        }
        document.getElementById("audio_input_selectbox").add(option);
      }
    }
  }
  // UPDATE AUDIO OUTPUT
  if (arg.tnc_running_state == "stopped") {
    if (
      document.getElementById("audio_output_selectbox").length !=
      arg.output_devices.length
    ) {
      document.getElementById("audio_output_selectbox").innerHTML = "";
      for (i = 0; i < arg.output_devices.length; i++) {
        var option = document.createElement("option");
        option.text = arg.output_devices[i]["name"];
        option.value = arg.output_devices[i]["id"];
        // set device from config if available
        if (config.tx_audio == option.text) {
          option.setAttribute("selected", true);
        }
        document.getElementById("audio_output_selectbox").add(option);
      }
    }
  }

  // UPDATE SERIAL DEVICES
  if (arg.tnc_running_state == "stopped") {
    if (
      document.getElementById("hamlib_deviceport").length !=
      arg.serial_devices.length
    ) {
      document.getElementById("hamlib_deviceport").innerHTML = "";
      var ignore = document.createElement("option");
      ignore.text = "-- ignore --";
      ignore.value = "ignore";
      document.getElementById("hamlib_deviceport").add(ignore);
      for (i = 0; i < arg.serial_devices.length; i++) {
        var option = document.createElement("option");
        option.text =
          arg.serial_devices[i]["port"] +
          " -- " +
          arg.serial_devices[i]["description"];
        option.value = arg.serial_devices[i]["port"];
        document.getElementById("hamlib_deviceport").add(option);
      }
      // set device from config if available
      document.getElementById("hamlib_deviceport").value =
        config.hamlib_deviceport;
    }
  }

  if (arg.tnc_running_state == "stopped") {
    if (
      document.getElementById("hamlib_ptt_port").length !=
      arg.serial_devices.length
    ) {
      document.getElementById("hamlib_ptt_port").innerHTML = "";
      var ignore = document.createElement("option");
      ignore.text = "-- ignore --";
      ignore.value = "ignore";
      document.getElementById("hamlib_ptt_port").add(ignore);
      for (i = 0; i < arg.serial_devices.length; i++) {
        var option = document.createElement("option");
        option.text =
          arg.serial_devices[i]["port"] +
          " -- " +
          arg.serial_devices[i]["description"];
        option.value = arg.serial_devices[i]["port"];
        document.getElementById("hamlib_ptt_port").add(option);
      }
      // set device from config if available
      document.getElementById("hamlib_ptt_port").value = config.hamlib_ptt_port;
    }
  }
});

// ACTION UPDATE HAMLIB TEST
ipcRenderer.on("action-update-hamlib-test", (event, arg) => {
  console.log(arg.hamlib_result);
  if (arg.hamlib_result == "SUCCESS") {
    document.getElementById("testHamlib").className = "btn btn-sm btn-success";
    // BUTTON HAS BEEN REMOVED
    //document.getElementById("testHamlibAdvanced").className = "btn btn-sm btn-success";
  }
  if (arg.hamlib_result == "NOSUCCESS") {
    document.getElementById("testHamlib").className = "btn btn-sm btn-warning";
    // BUTTON HAS BEEN REMOVED
    //document.getElementById("testHamlibAdvanced").className = "btn btn-sm btn-warning";
  }
  if (arg.hamlib_result == "FAILED") {
    document.getElementById("testHamlib").className = "btn btn-sm btn-danger";
    // BUTTON HAS BEEN REMOVED
    //document.getElementById("testHamlibAdvanced").className = "btn btn-sm btn-danger";
  }
});

ipcRenderer.on("action-update-daemon-connection", (event, arg) => {
  if (arg.daemon_connection == "open") {
    document.getElementById("daemon_connection_state").className =
      "btn btn-success";
    //document.getElementById("blurdiv").style.webkitFilter = "blur(0px)";
  }
  if (arg.daemon_connection == "opening") {
    document.getElementById("daemon_connection_state").className =
      "btn btn-warning";
    //document.getElementById("blurdiv").style.webkitFilter = "blur(10px)";
  }
  if (arg.daemon_connection == "closed") {
    document.getElementById("daemon_connection_state").className =
      "btn btn-danger";
    //document.getElementById("blurdiv").style.webkitFilter = "blur(10px)";
  }
});

ipcRenderer.on("action-update-tnc-connection", (event, arg) => {
  if (arg.tnc_connection == "open") {
    /*
        document.getElementById('hamlib_deviceid').disabled = true;
        document.getElementById('hamlib_deviceport').disabled = true;
        document.getElementById('testHamlib').disabled = true;
        document.getElementById('hamlib_ptt_protocol').disabled = true;
        document.getElementById('audio_input_selectbox').disabled = true;
        document.getElementById('audio_output_selectbox').disabled = true;
        //document.getElementById('stopTNC').disabled = false;
        document.getElementById('startTNC').disabled = true;
        document.getElementById('dxCall').disabled = false;
        document.getElementById("hamlib_serialspeed").disabled = true;
        document.getElementById("openDataModule").disabled = false;
        */

    // collapse settings screen
    var collapseFirstRow = new bootstrap.Collapse(
      document.getElementById("collapseFirstRow"),
      { toggle: false }
    );
    collapseFirstRow.hide();
    var collapseSecondRow = new bootstrap.Collapse(
      document.getElementById("collapseSecondRow"),
      { toggle: false }
    );
    collapseSecondRow.hide();
    var collapseThirdRow = new bootstrap.Collapse(
      document.getElementById("collapseThirdRow"),
      { toggle: false }
    );
    collapseThirdRow.show();
    var collapseFourthRow = new bootstrap.Collapse(
      document.getElementById("collapseFourthRow"),
      { toggle: false }
    );
    collapseFourthRow.show();

    //Set tuning for fancy graphics mode (high/low CPU)
    set_CPU_mode();
  } else {
    /*
        document.getElementById('hamlib_deviceid').disabled = false;
        document.getElementById('hamlib_deviceport').disabled = false;
        document.getElementById('testHamlib').disabled = false;
        document.getElementById('hamlib_ptt_protocol').disabled = false;
        document.getElementById('audio_input_selectbox').disabled = false;
        document.getElementById('audio_output_selectbox').disabled = false;
        //document.getElementById('stopTNC').disabled = true;
        document.getElementById('startTNC').disabled = false;
        document.getElementById('dxCall').disabled = true;
        document.getElementById("hamlib_serialspeed").disabled = false;
        document.getElementById("openDataModule").disabled = true;
        */
    // collapse settings screen
    var collapseFirstRow = new bootstrap.Collapse(
      document.getElementById("collapseFirstRow"),
      { toggle: false }
    );
    collapseFirstRow.show();
    var collapseSecondRow = new bootstrap.Collapse(
      document.getElementById("collapseSecondRow"),
      { toggle: false }
    );
    collapseSecondRow.show();
    var collapseThirdRow = new bootstrap.Collapse(
      document.getElementById("collapseThirdRow"),
      { toggle: false }
    );
    collapseThirdRow.hide();
    var collapseFourthRow = new bootstrap.Collapse(
      document.getElementById("collapseFourthRow"),
      { toggle: false }
    );
    collapseFourthRow.hide();
  }
});

ipcRenderer.on("action-update-rx-buffer", (event, arg) => {
  var data = arg.data["data"];

  var tbl = document.getElementById("rx-data");
  document.getElementById("rx-data").innerHTML = "";

  for (i = 0; i < arg.data.length; i++) {
    // first we update the PING window
    if (
      arg.data[i]["dxcallsign"] ==
      document.getElementById("dxCall").value.toUpperCase()
    ) {
      /*
        // if we are sending data without doing a ping before, we don't have a grid locator available. This could be a future feature for the TNC!
        if(arg.data[i]['DXGRID'] != ''){
            document.getElementById("pingDistance").innerHTML = arg.stations[i]['DXGRID']
        }
        */
      //document.getElementById("pingDB").innerHTML = arg.stations[i]['snr'];
      document.getElementById("dataModalPingDB").innerHTML =
        arg.stations[i]["snr"];
    }

    // now we update the received files list

    var row = document.createElement("tr");
    //https://stackoverflow.com/q/51421470

    //https://stackoverflow.com/a/847196
    timestampRaw = arg.data[i]["timestamp"];
    var date = new Date(timestampRaw * 1000);
    var hours = date.getHours();
    var minutes = "0" + date.getMinutes();
    var seconds = "0" + date.getSeconds();
    var datetime = hours + ":" + minutes.substr(-2) + ":" + seconds.substr(-2);

    var timestamp = document.createElement("td");
    var timestampText = document.createElement("span");
    timestampText.innerText = datetime;
    timestamp.appendChild(timestampText);

    var dxCall = document.createElement("td");
    var dxCallText = document.createElement("span");
    dxCallText.innerText = arg.data[i]["dxcallsign"];
    dxCall.appendChild(dxCallText);

    /*
    var dxGrid = document.createElement("td");
    var dxGridText = document.createElement('span');
    dxGridText.innerText = arg.data[i]['DXGRID']
    dxGrid.appendChild(dxGridText);
    */

    console.log(arg.data);

    var encoded_data = atob(arg.data[i]["data"]);
    var splitted_data = encoded_data.split(split_char);
    console.log(splitted_data);

    var fileName = document.createElement("td");
    var fileNameText = document.createElement("span");
    //var fileNameString = arg.data[i]['data'][0]['fn'];
    var fileNameString = splitted_data[1];

    fileNameText.innerText = fileNameString;
    fileName.appendChild(fileNameText);

    row.appendChild(timestamp);
    row.appendChild(dxCall);
    //      row.appendChild(dxGrid);
    row.appendChild(fileName);
    tbl.appendChild(row);

    // https://stackoverflow.com/a/26227660
    //var appDataFolder = process.env.HOME;
    //console.log("appDataFolder:" + appDataFolder);
    //var applicationFolder = path.join(appDataFolder, "FreeDATA");
    //console.log(applicationFolder);
    //var receivedFilesFolder = path.join(applicationFolder, "receivedFiles");
    var receivedFilesFolder = path.join(config.received_files_folder);

    console.log("receivedFilesFolder: " + receivedFilesFolder);
    // Creates receivedFiles folder if not exists
    // https://stackoverflow.com/a/13544465
    fs.mkdir(
      receivedFilesFolder,
      {
        recursive: true,
      },
      function (err) {
        console.log(err);
      }
    );

    // write file to data folder
    ////var base64String = arg.data[i]['data'][0]['d']
    // remove header from base64 String
    // https://www.codeblocq.com/2016/04/Convert-a-base64-string-to-a-file-in-Node/
    ////var base64Data = base64String.split(';base64,').pop()
    //write data to file
    var base64Data = splitted_data[4];
    var receivedFile = path.join(receivedFilesFolder, fileNameString);
    console.log(receivedFile);

    require("fs").writeFile(receivedFile, base64Data, "binary", function (err) {
      //require("fs").writeFile(receivedFile, base64Data, 'base64', function(err) {
      console.log(err);
    });
  }
});
ipcRenderer.on("run-tnc-command-fec-iswriting", (event) => {
  //console.log("Sending sendFecIsWriting");
  sock.sendFecIsWriting(config.mycall);
});

ipcRenderer.on("run-tnc-command", (event, arg) => {
  if (arg.command == "save_my_call") {
    sock.saveMyCall(arg.callsign);
  }
  if (arg.command == "save_my_grid") {
    sock.saveMyGrid(arg.grid);
  }
  if (arg.command == "ping") {
    sock.sendPing(arg.dxcallsign);
  }

  if (arg.command == "send_file") {
    sock.sendFile(
      arg.dxcallsign,
      arg.mode,
      arg.frames,
      arg.filename,
      arg.filetype,
      arg.data,
      arg.checksum
    );
  }
  if (arg.command == "send_message") {
    sock.sendMessage(
      arg.dxcallsign,
      arg.mode,
      arg.frames,
      arg.data,
      arg.checksum,
      arg.uuid,
      arg.command
    );
  }
  if (arg.command == "stop_transmission") {
    sock.stopTransmission();
  }
  if (arg.command == "set_tx_audio_level") {
    sock.setTxAudioLevel(arg.tx_audio_level);
  }
  if (arg.command == "record_audio") {
    sock.record_audio();
  }
  if (arg.command == "send_test_frame") {
    sock.sendTestFrame();
  }

  if (arg.command == "frequency") {
    sock.set_frequency(arg.frequency);
  }

  if (arg.command == "mode") {
    sock.set_mode(arg.mode);
  }

  if (arg.command == "requestUserInfo") {
    sock.sendRequestInfo(arg.dxcallsign);
  }

  if (arg.command == "responseUserInfo") {
    sock.sendResponseInfo(arg.dxcallsign, arg.userinfo);
  }
});

// IPC ACTION FOR AUTO UPDATER
ipcRenderer.on("action-updater", (event, arg) => {
  if (arg.status == "download-progress") {
    var progressinfo =
      "(" +
      Math.round(arg.progress.transferred / 1024) +
      "kB /" +
      Math.round(arg.progress.total / 1024) +
      "kB)" +
      " @ " +
      Math.round(arg.progress.bytesPerSecond / 1024) +
      "kByte/s";
    document.getElementById("UpdateProgressInfo").innerHTML = progressinfo;

    document
      .getElementById("UpdateProgressBar")
      .setAttribute("aria-valuenow", arg.progress.percent);
    document
      .getElementById("UpdateProgressBar")
      .setAttribute("style", "width:" + arg.progress.percent + "%;");
  }

  if (arg.status == "checking-for-update") {
    //document.title = document.title + ' - v' + arg.version;
    updateTitle(
      config.myCall,
      config.tnc_host,
      config.tnc_port,
      " -v " + arg.version
    );
    document.getElementById("updater_status").innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';

    document.getElementById("updater_status").className =
      "btn btn-secondary btn-sm";
    document.getElementById("update_and_install").style.display = "none";
  }
  if (arg.status == "update-downloaded") {
    document.getElementById("update_and_install").removeAttribute("style");
    document.getElementById("updater_status").innerHTML =
      '<i class="bi bi-cloud-download ms-1 me-1" style="color: white;"></i>';
    document.getElementById("updater_status").className =
      "btn btn-success btn-sm";

    // HERE WE NEED TO RUN THIS SOMEHOW...
    //mainLog.info('quit application and install update');
    //autoUpdater.quitAndInstall();
  }
  if (arg.status == "update-not-available") {
    document.getElementById("updater_status").innerHTML =
      '<i class="bi bi-check2-square ms-1 me-1" style="color: white;"></i>';
    document.getElementById("updater_status").className =
      "btn btn-success btn-sm";
    document.getElementById("update_and_install").style.display = "none";
  }
  if (arg.status == "update-available") {
    document.getElementById("updater_status").innerHTML =
      '<i class="bi bi-hourglass-split ms-1 me-1" style="color: white;"></i>';
    document.getElementById("updater_status").className =
      "btn btn-warning btn-sm";
    document.getElementById("update_and_install").style.display = "none";
  }

  if (arg.status == "error") {
    document.getElementById("updater_status").innerHTML =
      '<i class="bi bi-exclamation-square ms-1 me-1" style="color: white;"></i>';
    document.getElementById("updater_status").className =
      "btn btn-danger btn-sm";
    document.getElementById("update_and_install").style.display = "none";
  }
});

// ----------- INFO MODAL ACTIONS -------------------------------

// CQ TRANSMITTING
ipcRenderer.on("action-show-cq-toast-transmitting", (event, data) => {
  displayToast(
    (type = "success"),
    (icon = "bi-broadcast"),
    (content = "transmitting cq"),
    (duration = 5000)
  );
});
// fec iswriting received
ipcRenderer.on("action-show-fec-toast-iswriting", (event, data) => {
  let dxcallsign = data["data"][0]["dxcallsign"];
  let content = `${dxcallsign}</strong> is typing`;
  displayToast(
    (type = "success"),
    (icon = "bi-pencil-fill"),
    (content = content),
    (duration = 5000)
  );
});
// CQ RECEIVED
ipcRenderer.on("action-show-cq-toast-received", (event, data) => {
  let dxcallsign = data["data"][0]["dxcallsign"];
  let dxgrid = data["data"][0]["dxgrid"];
  let content = `cq from <strong>${dxcallsign}</strong> (${dxgrid})`;

  displayToast(
    (type = "success"),
    (icon = "bi-broadcast"),
    (content = content),
    (duration = 5000)
  );
});

// QRV TRANSMITTING
ipcRenderer.on("action-show-qrv-toast-transmitting", (event, data) => {
  displayToast(
    (type = "success"),
    (icon = "bi-broadcast"),
    (content = "transmitting qrv"),
    (duration = 5000)
  );
});

// QRV RECEIVED
ipcRenderer.on("action-show-qrv-toast-received", (event, data) => {
  console.log(data["data"][0]);
  let dxcallsign = data["data"][0]["dxcallsign"];
  let dxgrid = data["data"][0]["dxgrid"];
  let content = `received qrv from <strong>${dxcallsign}</strong> (${dxgrid})`;

  displayToast(
    (type = "success"),
    (icon = "bi-broadcast"),
    (content = content),
    (duration = 5000)
  );
});

// BEACON TRANSMITTING
ipcRenderer.on("action-show-beacon-toast-transmitting", (event, data) => {
  displayToast(
    (type = "info"),
    (icon = "bi-broadcast"),
    (content = "transmitting beacon"),
    (duration = 5000)
  );
});

// BEACON RECEIVED
ipcRenderer.on("action-show-beacon-toast-received", (event, data) => {
  console.log(data["data"][0]);
  let dxcallsign = data["data"][0]["dxcallsign"];
  let dxgrid = data["data"][0]["dxgrid"];
  let content = `beacon from <strong>${dxcallsign}</strong> (${dxgrid})`;
  displayToast(
    (type = "info"),
    (icon = "bi-broadcast"),
    (content = content),
    (duration = 5000)
  );
});

// PING TRANSMITTING
ipcRenderer.on("action-show-ping-toast-transmitting", (event, data) => {
  displayToast(
    (type = "success"),
    (icon = "bi-broadcast"),
    (content = "transmitting ping"),
    (duration = 5000)
  );
});

// PING RECEIVED
ipcRenderer.on("action-show-ping-toast-received", (event, data) => {
  console.log(data["data"][0]);
  let dxcallsign = data["data"][0]["dxcallsign"];
  let content = `ping from <strong>${dxcallsign}</strong>`;
  displayToast(
    (type = "success"),
    (icon = "bi-broadcast"),
    (content = content),
    (duration = 5000)
  );
});

// PING RECEIVED ACK
ipcRenderer.on("action-show-ping-toast-received-ack", (event, data) => {
  console.log(data["data"][0]);
  let dxcallsign = data["data"][0]["dxcallsign"];
  let dxgrid = data["data"][0]["dxgrid"];
  let content = `ping ACK from <strong>${dxcallsign}</strong> (${dxgrid})`;
  displayToast(
    (type = "success"),
    (icon = "bi-check"),
    (content = content),
    (duration = 5000)
  );
});

// DATA CHANNEL OPENING TOAST
ipcRenderer.on("action-show-arq-toast-datachannel-opening", (event, data) => {
  console.log(data["data"][0]);
  let dxcallsign = data["data"][0]["dxcallsign"];
  let content = `opening datachannel with <strong>${dxcallsign}</strong>`;
  displayToast(
    (type = "secondary"),
    (icon = "bi-arrow-left-right"),
    (content = content),
    (duration = 5000)
  );
});

// DATA CHANNEL WAITING TOAST
ipcRenderer.on("action-show-arq-toast-datachannel-waiting", (event, data) => {
  displayToast(
    (type = "warning"),
    (icon = "bi-smartwatch"),
    (content = "channel busy - waiting..."),
    (duration = 5000)
  );
});

// DATA CHANNEL OPEN TOAST
ipcRenderer.on("action-show-arq-toast-datachannel-open", (event, data) => {
  displayToast(
    (type = "success"),
    (icon = "bi-arrow-left-right"),
    (content = "datachannel open"),
    (duration = 5000)
  );
});

// DATA CHANNEL RECEIVED OPENER TOAST
ipcRenderer.on(
  "action-show-arq-toast-datachannel-received-opener",
  (event, data) => {
    console.log(data["data"][0]);
    let dxcallsign = data["data"][0]["dxcallsign"];
    let content = `datachannel requested by <strong>${dxcallsign}</strong>`;
    displayToast(
      (type = "success"),
      (icon = "bi-arrow-left-right"),
      (content = content),
      (duration = 5000)
    );
  }
);

// ARQ TRANSMISSION FAILED
// TODO: use for both - transmitting and receiving --> we need to change the IDs
ipcRenderer.on("action-show-arq-toast-transmission-failed", (event, data) => {
  displayToast(
    (type = "danger"),
    (icon = "bi-arrow-left-right"),
    (content = "transmission failed"),
    (duration = 5000)
  );
});

// ARQ TRANSMISSION FAILED (Version mismatch)
ipcRenderer.on(
  "action-show-arq-toast-transmission-failed-ver",
  (event, data) => {
    displayToast(
      (type = "danger"),
      (icon = "bi-broadcast"),
      (content = "protocol version missmatch"),
      (duration = 5000)
    );
  }
);

// ARQ TRANSMISSION STOPPED
// TODO: RENAME ID -- WRONG
ipcRenderer.on("action-show-arq-toast-transmission-stopped", (event, data) => {
  displayToast(
    (type = "success"),
    (icon = "bi-arrow-left-right"),
    (content = "transmission stopped"),
    (duration = 5000)
  );
});

// ARQ TRANSMISSION FAILED
// TODO: USE FOR TX AND RX
ipcRenderer.on("action-show-arq-toast-transmission-failed", (event, data) => {
  displayToast(
    (type = "danger"),
    (icon = "bi-broadcast"),
    (content = "arq transmission failed"),
    (duration = 5000)
  );
});

// ARQ TRANSMISSION TRANSMITTED
ipcRenderer.on(
  "action-show-arq-toast-transmission-transmitted",
  (event, data) => {
    console.log(data["data"][0]);
    //let content = `received cq from <strong>${dxcallsign}</strong> (${dxgrid})`;
    displayToast(
      (type = "success"),
      (icon = "bi-broadcast"),
      (content = "data transmitted"),
      (duration = 5000)
    );
  }
);

// ARQ TRANSMISSION TRANSMITTING
ipcRenderer.on(
  "action-show-arq-toast-transmission-transmitting",
  (event, data) => {
    var irs_snr = data["data"][0].irs_snr;

    if (irs_snr <= 0) {
      displayToast(
        (type = "warning"),
        (icon = "bi-broadcast"),
        (content = "low link margin: <strong>" + irs_snr + " dB</strong>"),
        (duration = 5000)
      );
    } else if (irs_snr > 0 && irs_snr <= 5) {
      displayToast(
        (type = "warning"),
        (icon = "bi-broadcast"),
        (content = "medium link margin: <strong>" + irs_snr + " dB</strong>"),
        (duration = 5000)
      );
    } else if (irs_snr > 5 && irs_snr < 12.7) {
      displayToast(
        (type = "success"),
        (icon = "bi-broadcast"),
        (content = "high link margin: <strong>" + irs_snr + " dB</strong>"),
        (duration = 5000)
      );
    } else if (irs_snr >= 12.7) {
      displayToast(
        (type = "success"),
        (icon = "bi-broadcast"),
        (content =
          "very high link margin: <strong>" + irs_snr + " dB</strong>"),
        (duration = 5000)
      );
    } else {
      //displayToast(type='info', icon='bi-broadcast', content='no snr information', duration=5000);
    }
  }
);

// ARQ TRANSMISSION RECEIVED
ipcRenderer.on("action-show-arq-toast-transmission-received", (event, data) => {
  console.log(data["data"][0]);
  displayToast(
    (type = "success"),
    (icon = "bi-check-circle"),
    (content = "all data received"),
    (duration = 5000)
  );
});

// ARQ TRANSMISSION RECEIVING
ipcRenderer.on(
  "action-show-arq-toast-transmission-receiving",
  (event, data) => {
    displayToast(
      (type = "primary"),
      (icon = "bi-arrow-left-right"),
      (content = "session receiving"),
      (duration = 5000)
    );
  }
);

// ARQ SESSION CONNECTING
ipcRenderer.on("action-show-arq-toast-session-connecting", (event, data) => {
  displayToast(
    (type = "primary"),
    (icon = "bi-arrow-left-right"),
    (content = "connecting..."),
    (duration = 5000)
  );
});

// ARQ SESSION CONNECTED
ipcRenderer.on("action-show-arq-toast-session-connected", (event, data) => {
  displayToast(
    (type = "success"),
    (icon = "bi-arrow-left-right"),
    (content = "session connected"),
    (duration = 5000)
  );
});

// ARQ SESSION CONNECTED
ipcRenderer.on("action-show-arq-toast-session-waiting", (event, data) => {
  displayToast(
    (type = "warning"),
    (icon = "bi-smartwatch"),
    (content = "session waiting..."),
    (duration = 5000)
  );
});

// ARQ SESSION CLOSE
ipcRenderer.on("action-show-arq-toast-session-close", (event, data) => {
  displayToast(
    (type = "warning"),
    (icon = "bi-arrow-left-right"),
    (content = "session close"),
    (duration = 5000)
  );
});

// ARQ SESSION FAILED
ipcRenderer.on("action-show-arq-toast-session-failed", (event, data) => {
  displayToast(
    (type = "danger"),
    (icon = "bi-arrow-left-right"),
    (content = "session failed"),
    (duration = 5000)
  );
});

// enable or disable a setting by given switch and element
// not used at this time
function enable_setting(enable_switch, enable_object) {
  if (document.getElementById(enable_switch).checked) {
    config[enable_switch] = true;
    document
      .getElementById(enable_object)
      .removeAttribute("disabled", "disabled");
  } else {
    config[enable_switch] = false;
    document.getElementById(enable_object).setAttribute("disabled", "disabled");
  }
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
}

// enable or disable a setting switch
// not used at this time
function set_setting_switch(setting_switch, enable_object, state) {
  document.getElementById(setting_switch).checked = state;
  enable_setting(setting_switch, enable_object);
}

setInterval(checkRigctld, 500);
function checkRigctld() {
  var rigctld_ip = document.getElementById("hamlib_rigctld_ip").value;
  var rigctld_port = document.getElementById("hamlib_rigctld_port").value;

  let Data = {
    ip: rigctld_ip,
    port: rigctld_port,
  };

  //Prevents an error on startup if hamlib settings aren't populated yet
  if (rigctld_port.length > 0 && rigctld_ip.length > 0) {
    ipcRenderer.send("request-check-rigctld", Data);
  }
}

ipcRenderer.on("action-check-rigctld", (event, data) => {
  document.getElementById("hamlib_rigctld_status").value = data["state"];
});

ipcRenderer.on("action-set-app-version", (event, data) => {
  appVer = data;
});

function updateTitle(
  mycall = config.mycall,
  tnc = config.tnc_host,
  tncport = config.tnc_port,
  appender = ""
) {
  //Multiple consecutive  spaces get converted to a single space
  var title =
    "FreeDATA " +
    appVer +
    " - Call: " +
    mycall +
    " - TNC: " +
    tnc +
    ":" +
    tncport +
    appender;
  if (title != document.title) {
    document.title = title;
  }
}

//Set force to true to ensure a class is present on a control, otherwise set to false to ensure it isn't present
function toggleClass(control, classToToggle, force) {
  var cntrl = document.getElementById(control);
  if (cntrl == undefined) {
    console.log("toggle class:  unknown control: ", control);
    return;
  }
  var activeClasses = cntrl.className;
  //var oldactive = activeClasses;
  if (force == true && activeClasses.indexOf(classToToggle) >= 0) {
    return;
  }
  if (force == false && activeClasses.indexOf(classToToggle) == -1) {
    return;
  }
  if (force == true) {
    activeClasses += " " + classToToggle;
  } else {
    activeClasses = activeClasses.replace(classToToggle, "");
  }
  activeClasses = activeClasses.replace("  ", " ").trim();
  cntrl.className = activeClasses;
  //console.log(control," toggleClass; force:  ", force, "class: " ,classToToggle, " in: '" ,oldactive, "' out: '",activeClasses,"'");
}
function set_CPU_mode() {
  if (config.high_graphics.toUpperCase() == "FALSE") {
    toggleClass("dbfs_level", "disable-effects", true);
    toggleClass("dbfs_level", "progress-bar-striped", false);
    toggleClass("noise_level", "disable-effects", true);
    toggleClass("noise_level", "progress-bar-striped", false);
    toggleClass("waterfall", "disable-effects", true);
    toggleClass("transmission_progress", "disable-effects", true);
    toggleClass("transmission_progress", "progress-bar-striped", false);
  } else {
    toggleClass("dbfs_level", "disable-effects", false);
    toggleClass("dbfs_level", "progress-bar-striped", true);
    toggleClass("noise_level", "disable-effects", false);
    toggleClass("noise_level", "progress-bar-striped", true);
    toggleClass("waterfall", "disable-effects", false);
    toggleClass("transmission_progress", "disable-effects", false);
    toggleClass("transmission_progress", "progress-bar-striped", true);
  }
}
//Temporarily disable a button with timeout
function pauseButton(btn, timems) {
  btn.disabled = true;
  var curText = btn.innerHTML;
  if (config.high_graphics.toUpperCase() == "TRUE") {
    btn.innerHTML =
      '<span class="spinner-grow spinner-grow-sm force-gpu" role="status" aria-hidden="true">';
  }
  setTimeout(() => {
    btn.innerHTML = curText;
    btn.disabled = false;
  }, timems);
}
//https://stackoverflow.com/questions/15900485/correct-way-to-convert-size-in-bytes-to-kb-mb-gb-in-javascript
function formatBytes(bytes, decimals = 1) {
  if (!+bytes) return "0 Bytes";

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

// display toast
function displayToast(
  type = "primary",
  icon = "bi-info",
  content = "default",
  duration = 5000
) {
  mainToastContainer = document.getElementById("mainToastContainer");

  let randomID = uuidv4();
  let toastCode = `
        <div class="toast align-items-center bg-outline-${type} border-1" id="${randomID}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body p-0 m-0 bg-white rounded-2 w-100">
                      <div class="row p-1 m-0">
                        <div class="col-auto bg-${type} rounded-start rounded-2 d-flex align-items-center">
                            <i class="bi ${icon}" style="font-size: 1rem; color: white"></i>
                        </div>
                        <div class="col p-2">
                          ${content}
                        </div>
                      </div>
                </div>
                <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

  // insert toast to toast container
  mainToastContainer.insertAdjacentHTML("beforeend", toastCode);

  // register toast
  let toastHTMLElement = document.getElementById(randomID);
  let toast = bootstrap.Toast.getOrCreateInstance(toastHTMLElement); // Returns a Bootstrap toast instance
  toast._config.delay = duration;

  // show toast
  toast.show();

  //register event listener if toast is hidden
  toastHTMLElement.addEventListener("hidden.bs.toast", () => {
    // remove eventListener
    toastHTMLElement.removeEventListener("hidden.bs.toast", this);
    // remove toast
    toastHTMLElement.remove();
  });
}

function loadSettings(elements) {
  elements.forEach(function (id) {
    let element = document.getElementById(id);

    if (element.tagName === "SELECT") {
      element.value = config[id];

      // add selected value
      for (var i = 0, j = element.options.length; i < j; ++i) {
        if (element.options[i].innerHTML === config[id]) {
          element.selectedIndex = i;
          break;
        }
      }
    } else if (element.tagName === "INPUT" && element.type === "text") {
      element.value = config[id];
    } else if (element.tagName === "INPUT" && element.type === "radio") {
      element.value = config[id];

      if (config[id] === "True") {
        element.checked = true;
      } else {
        element.checked = false;
      }
    } else {
      console.log("nothing matched....");
    }
  });
}
