const path = require('path');
const {ipcRenderer, shell} = require('electron');
const exec = require('child_process').spawn;
const sock = require('./sock.js');
const daemon = require('./daemon.js');
const fs = require('fs');
const {
    locatorToLatLng,
    distance,
    bearingDistance,
    latLngToLocator
} = require('qth-locator');
const os = require('os');

// split character used for appending additional data to files
const split_char = '\0;';


// https://stackoverflow.com/a/26227660
var appDataFolder = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + "/.config");
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, 'config.json');
const config = require(configPath);


// SET dbfs LEVEL GLOBAL
// this is an attempt of reducing CPU LOAD
// we are going to check if we have unequal values before we start calculating again
var dbfs_level_raw = 0



// START INTERVALL COMMAND EXECUTION FOR STATES
//setInterval(sock.getRxBuffer, 1000);


// WINDOW LISTENER
window.addEventListener('DOMContentLoaded', () => {

    // save frequency event listener
    document.getElementById("saveFrequency").addEventListener("click", () => {
            var freq = document.getElementById("newFrequency").value;
            console.log(freq)
            let Data = {
                type: "set",
                command: "frequency",
                frequency: freq,
            };
            ipcRenderer.send('run-tnc-command', Data);

    });

    // enter button for input field
    document.getElementById("newFrequency").addEventListener("keypress", function(event) {
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
            ipcRenderer.send('run-tnc-command', Data);
    });

    // save mode event listener
    document.getElementById("saveModeUSB").addEventListener("click", () => {
            let Data = {
                type: "set",
                command: "mode",
                mode: "USB",
            };
            ipcRenderer.send('run-tnc-command', Data);
    });

    // save mode event listener
    document.getElementById("saveModeLSB").addEventListener("click", () => {
            let Data = {
                type: "set",
                command: "mode",
                mode: "LSB",
            };
            ipcRenderer.send('run-tnc-command', Data);
    });

    // save mode event listener
    document.getElementById("saveModeAM").addEventListener("click", () => {
            let Data = {
                type: "set",
                command: "mode",
                mode: "AM",
            };
            ipcRenderer.send('run-tnc-command', Data);
    });

    // save mode event listener
    document.getElementById("saveModeFM").addEventListener("click", () => {
            let Data = {
                type: "set",
                command: "mode",
                mode: "FM",
            };
            ipcRenderer.send('run-tnc-command', Data);
    });

    // start stop audio recording event listener
    document.getElementById("startStopRecording").addEventListener("click", () => {
            let Data = {
                type: "set",
                command: "record_audio",
            };
            ipcRenderer.send('run-tnc-command', Data);

    });


document.getElementById('received_files_folder').addEventListener('click', () => {

    ipcRenderer.send('get-folder-path',{
        title: 'Title',
    });
    
    ipcRenderer.on('return-folder-paths',(event,data)=>{
        document.getElementById("received_files_folder").value = data.path.filePaths[0]
        config.received_files_folder = data.path.filePaths[0]
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
})

document.getElementById('openReceivedFilesFolder').addEventListener('click', () => {

    ipcRenderer.send('open-folder',{
        path: config.received_files_folder,
    });
})




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
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    })


    // LOAD SETTINGS
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
    document.getElementById('hamlib_deviceid').value = config.hamlib_deviceid;

    set_setting_switch("enable_hamlib_deviceport", "hamlib_deviceport", config.enable_hamlib_deviceport)
    set_setting_switch("enable_hamlib_ptt_port", "hamlib_ptt_port", config.enable_hamlib_ptt_port)

    document.getElementById('hamlib_serialspeed').value = config.hamlib_serialspeed;
    set_setting_switch("enable_hamlib_serialspeed", "hamlib_serialspeed", config.enable_hamlib_serialspeed)

    document.getElementById('hamlib_pttprotocol').value = config.hamlib_pttprotocol;
    set_setting_switch("enable_hamlib_pttprotocol", "hamlib_pttprotocol", config.enable_hamlib_pttprotocol)

    document.getElementById('hamlib_databits').value = config.hamlib_data_bits;
    set_setting_switch("enable_hamlib_databits", "hamlib_databits", config.enable_hamlib_databits)

    document.getElementById('hamlib_stopbits').value = config.hamlib_stop_bits;
    set_setting_switch("enable_hamlib_stopbits", "hamlib_stopbits", config.enable_hamlib_stopbits)

    document.getElementById('hamlib_handshake').value = config.hamlib_handshake;
    set_setting_switch("enable_hamlib_handshake", "hamlib_handshake", config.enable_hamlib_handshake)

    document.getElementById('hamlib_dcd').value = config.hamlib_dcd;
    set_setting_switch("enable_hamlib_dcd", "hamlib_dcd", config.enable_hamlib_dcd)

    document.getElementById('hamlib_dtrstate').value = config.hamlib_dtrstate;
    set_setting_switch("enable_hamlib_dtrstate", "hamlib_dtrstate", config.enable_hamlib_dtrstate)





    document.getElementById("hamlib_rigctld_ip").value = config.hamlib_rigctld_ip;
    document.getElementById("hamlib_rigctld_port").value = config.hamlib_rigctld_port;
    document.getElementById("hamlib_rigctld_path").value = config.hamlib_rigctld_path;
    document.getElementById("hamlib_rigctld_server_port").value = config.hamlib_rigctld_server_port;



    document.getElementById("beaconInterval").value = config.beacon_interval;
 
    document.getElementById("scatterSwitch").value = config.enable_scatter;
    document.getElementById("fftSwitch").value = config.enable_fft;


       
    document.getElementById("received_files_folder").value = config.received_files_folder;   

    if(config.enable_scatter == 'True'){
        document.getElementById("scatterSwitch").checked = true;
    } else {
        document.getElementById("scatterSwitch").checked = false;
    }

    if(config.enable_fft == 'True'){
        document.getElementById("fftSwitch").checked = true;
    } else {
        document.getElementById("fftSwitch").checked = false;
    }

    if(config.low_bandwidth_mode == 'True'){
        document.getElementById("500HzModeSwitch").checked = true;
    } else {
        document.getElementById("500HzModeSwitch").checked = false;
    }  
          
    if(config.enable_fsk == 'True'){
        document.getElementById("fskModeSwitch").checked = true;
    } else {
        document.getElementById("fskModeSwitch").checked = false;
    }  
    
    if(config.respond_to_cq == 'True'){
        document.getElementById("respondCQSwitch").checked = true;
    } else {
        document.getElementById("respondCQSwitch").checked = false;
    }

    if(config.enable_explorer == 'True'){
        document.getElementById("ExplorerSwitch").checked = true;
    } else {
        document.getElementById("ExplorerSwitch").checked = false;
    }
    // theme selector

    if(config.theme != 'default'){

        var theme_path = "../node_modules/bootswatch/dist/"+ config.theme +"/bootstrap.min.css";
        document.getElementById("theme_selector").value = config.theme;
        document.getElementById("bootstrap_theme").href = escape(theme_path);
    } else {    
        var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
        document.getElementById("theme_selector").value = 'default';
        document.getElementById("bootstrap_theme").href = escape(theme_path);
    }
    

    // Update channel selector
    document.getElementById("update_channel_selector").value = config.update_channel;
    document.getElementById("updater_channel").innerHTML = escape(config.update_channel);

    // Update tuning range fmin fmax
    document.getElementById("tuning_range_fmin").value = config.tuning_range_fmin;
    document.getElementById("tuning_range_fmax").value = config.tuning_range_fmax;
    
    
    // Update TX Audio Level
    document.getElementById("audioLevelTXvalue").innerHTML = parseInt(config.tx_audio_level);
    document.getElementById("audioLevelTX").value = parseInt(config.tx_audio_level);    

    // Update RX Buffer Size
    document.getElementById("rx_buffer_size").value = config.rx_buffer_size;

    if (config.spectrum == 'waterfall') {
        document.getElementById("waterfall-scatter-switch1").checked = true;
        document.getElementById("waterfall-scatter-switch2").checked = false;
        document.getElementById("waterfall-scatter-switch3").checked = false;

        document.getElementById("waterfall").style.visibility = 'visible';
        document.getElementById("waterfall").style.height = '100%';
        document.getElementById("waterfall").style.display = 'block';

        document.getElementById("scatter").style.height = '0px';
        document.getElementById("scatter").style.visibility = 'hidden';
        document.getElementById("scatter").style.display = 'none';

        document.getElementById("chart").style.height = '0px';
        document.getElementById("chart").style.visibility = 'hidden';
        document.getElementById("chart").style.display = 'none';

    } else if (config.spectrum == 'scatter'){

        document.getElementById("waterfall-scatter-switch1").checked = false;
        document.getElementById("waterfall-scatter-switch2").checked = true;
        document.getElementById("waterfall-scatter-switch3").checked = false;

        document.getElementById("waterfall").style.visibility = 'hidden';
        document.getElementById("waterfall").style.height = '0px';
        document.getElementById("waterfall").style.display = 'none';


        document.getElementById("scatter").style.height = '100%';
        document.getElementById("scatter").style.visibility = 'visible';
        document.getElementById("scatter").style.display = 'block';

        document.getElementById("chart").style.visibility = 'hidden';
        document.getElementById("chart").style.height = '0px';
        document.getElementById("chart").style.display = 'none';

    } else {

        document.getElementById("waterfall-scatter-switch1").checked = false;
        document.getElementById("waterfall-scatter-switch2").checked = false;
        document.getElementById("waterfall-scatter-switch3").checked = true;

        document.getElementById("waterfall").style.visibility = 'hidden';
        document.getElementById("waterfall").style.height = '0px';
        document.getElementById("waterfall").style.display = 'none';

        document.getElementById("scatter").style.height = '0px';
        document.getElementById("scatter").style.visibility = 'hidden';
        document.getElementById("scatter").style.display = 'none';

        document.getElementById("chart").style.visibility = 'visible';
        document.getElementById("chart").style.height = '100%';
        document.getElementById("chart").style.display = 'block';

    }

    // radio control element
    if (config.radiocontrol == 'rigctld') {

        document.getElementById("radio-control-switch-disabled").checked = false;
        document.getElementById("radio-control-switch-radio").checked = true;
        document.getElementById("radio-control-switch-connect").checked = false;
        document.getElementById("radio-control-switch-network").checked = false;

       document.getElementById("radio-control-disabled").style.visibility = 'hidden';
        document.getElementById("radio-control-disabled").style.display = 'none';

        document.getElementById("radio-control-radio").style.visibility = 'visible';
        document.getElementById("radio-control-radio").style.display = '100%';

        document.getElementById("radio-control-connection").style.visibility = 'hidden';
        document.getElementById("radio-control-connection").style.display = 'none';

        document.getElementById("radio-control-ptt").style.visibility = 'hidden';
        document.getElementById("radio-control-ptt").style.display = 'none';

        document.getElementById("radio-control-network").style.visibility = 'hidden';
        document.getElementById("radio-control-network").style.display = 'none';

       document.getElementById("radio-control-rigctld").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.display = 'none';

       document.getElementById("radio-control-rigctld-info").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld-info").style.display = 'none';
    } else {
    
        document.getElementById("radio-control-switch-disabled").checked = true;
        document.getElementById("radio-control-switch-radio").checked = false;
        document.getElementById("radio-control-switch-connect").checked = false;
        document.getElementById("radio-control-switch-network").checked = false;
        document.getElementById("radio-control-switch-rigctld").checked = false;
        document.getElementById("radio-control-switch-rigctld-info").checked = false;

        document.getElementById("radio-control-connection").style.visibility = 'hidden';
        document.getElementById("radio-control-connection").style.display = 'none';

        document.getElementById("radio-control-ptt").style.visibility = 'hidden';
        document.getElementById("radio-control-ptt").style.display = 'none';

        document.getElementById("radio-control-network").style.display = 'none';  
        document.getElementById("radio-control-network").style.visibility = 'hidden';

        document.getElementById("radio-control-radio").style.display = 'none';
        document.getElementById("radio-control-radio").style.visibility = 'hidden';

       document.getElementById("radio-control-rigctld").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.display = 'none';

        document.getElementById("radio-control-rigctld-info").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld-info").style.display = 'none';

    }

    // remote tnc
    if (config.tnclocation == 'remote') {
        document.getElementById("local-remote-switch1").checked = false;
        document.getElementById("local-remote-switch2").checked = true;
        document.getElementById("remote-tnc-field").style.visibility = 'visible';
    } else {
        document.getElementById("local-remote-switch1").checked = true;
        document.getElementById("local-remote-switch2").checked = false;
        document.getElementById("remote-tnc-field").style.visibility = 'hidden';
    }

    // Create spectrum object on canvas with ID "waterfall"
    global.spectrum = new Spectrum(
        "waterfall", {
            spectrumPercent: 0,
            wf_rows: 192    //Assuming 1 row = 1 pixe1, 192 is the height of the spectrum container
        });

    //Set waterfalltheme
    document.getElementById("wftheme_selector").value = config.wftheme;
    spectrum.setColorMap(config.wftheme);

    // on click radio control toggle view
    // disabled
    document.getElementById("radio-control-switch-disabled").addEventListener("click", () => {

        document.getElementById("hamlib_info_field").innerHTML = 'Set hamlib related settings.';

        document.getElementById("radio-control-disabled").style.display = 'block';
        document.getElementById("radio-control-disabled").style.visibility = 'visible';

        document.getElementById("radio-control-radio").style.display = 'none';
        document.getElementById("radio-control-radio").style.visibility = 'hidden';

        document.getElementById("radio-control-connection").style.visibility = 'hidden';
        document.getElementById("radio-control-connection").style.display = 'none';

        document.getElementById("radio-control-ptt").style.visibility = 'hidden';
        document.getElementById("radio-control-ptt").style.display = 'none';

        document.getElementById("radio-control-network").style.display = 'none';
        document.getElementById("radio-control-network").style.visibility = 'hidden';

       document.getElementById("radio-control-rigctld").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.display = 'none';

        document.getElementById("radio-control-rigctld-info").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld-info").style.display = 'none';

        config.radiocontrol = 'disabled'
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
    
    
    // radio settings event listener
    document.getElementById("radio-control-switch-radio").addEventListener("click", () => {

        document.getElementById("hamlib_info_field").innerHTML = 'Select your radio by searching for the name or ID.';

        document.getElementById("radio-control-disabled").style.display = 'none';
        document.getElementById("radio-control-disabled").style.visibility = 'hidden';

        document.getElementById("radio-control-radio").style.display = 'block';
        document.getElementById("radio-control-radio").style.visibility = 'visible';

        document.getElementById("radio-control-connection").style.visibility = 'hidden';
        document.getElementById("radio-control-connection").style.display = 'none';

        document.getElementById("radio-control-ptt").style.visibility = 'hidden';
        document.getElementById("radio-control-ptt").style.display = 'none';

        document.getElementById("radio-control-network").style.display = 'none';
        document.getElementById("radio-control-network").style.visibility = 'hidden';

       document.getElementById("radio-control-rigctld").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.display = 'none';

        document.getElementById("radio-control-rigctld-info").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld-info").style.display = 'none';

        config.radiocontrol = 'rigctld';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });


    // radio settings 'connection' event listener
    document.getElementById("radio-control-switch-connect").addEventListener("click", () => {

        document.getElementById("hamlib_info_field").innerHTML = 'Setup the connection between rigctld and your radio';

        document.getElementById("radio-control-disabled").style.display = 'none';
        document.getElementById("radio-control-disabled").style.visibility = 'hidden';

        document.getElementById("radio-control-radio").style.display = 'none';
        document.getElementById("radio-control-radio").style.visibility = 'hidden';

        document.getElementById("radio-control-connection").style.visibility = 'visible';
        document.getElementById("radio-control-connection").style.display = 'block';

        document.getElementById("radio-control-ptt").style.visibility = 'hidden';
        document.getElementById("radio-control-ptt").style.display = 'none';

        document.getElementById("radio-control-network").style.display = 'none';
        document.getElementById("radio-control-network").style.visibility = 'hidden';

       document.getElementById("radio-control-rigctld").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.display = 'none';

        document.getElementById("radio-control-rigctld-info").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld-info").style.display = 'none';

        config.radiocontrol = 'rigctld';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

    // radio settings 'ptt' event listener
    document.getElementById("radio-control-switch-ptt").addEventListener("click", () => {

        document.getElementById("hamlib_info_field").innerHTML = 'Set your PTT related settings.';

        document.getElementById("radio-control-disabled").style.display = 'none';
        document.getElementById("radio-control-disabled").style.visibility = 'hidden';

        document.getElementById("radio-control-radio").style.display = 'none';
        document.getElementById("radio-control-radio").style.visibility = 'hidden';

        document.getElementById("radio-control-connection").style.visibility = 'hidden';
        document.getElementById("radio-control-connection").style.display = 'none';

        document.getElementById("radio-control-ptt").style.visibility = 'visible';
        document.getElementById("radio-control-ptt").style.display = 'block';

        document.getElementById("radio-control-network").style.display = 'none';
        document.getElementById("radio-control-network").style.visibility = 'hidden';

       document.getElementById("radio-control-rigctld").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.display = 'none';

        document.getElementById("radio-control-rigctld-info").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld-info").style.display = 'none';

        config.radiocontrol = 'rigctld';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });


    // // radio settings 'network' event listener
    document.getElementById("radio-control-switch-network").addEventListener("click", () => {

        document.getElementById("hamlib_info_field").innerHTML = 'Set the ip and port of a rigctld session';

        document.getElementById("radio-control-disabled").style.display = 'none';
        document.getElementById("radio-control-disabled").style.visibility = 'hidden';

        document.getElementById("radio-control-radio").style.display = 'none';
        document.getElementById("radio-control-radio").style.visibility = 'hidden';

        document.getElementById("radio-control-connection").style.visibility = 'hidden';
        document.getElementById("radio-control-connection").style.display = 'none';

        document.getElementById("radio-control-ptt").style.visibility = 'hidden';
        document.getElementById("radio-control-ptt").style.display = 'none';

        document.getElementById("radio-control-network").style.display = 'block';
        document.getElementById("radio-control-network").style.visibility = 'visible';

       document.getElementById("radio-control-rigctld").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.display = 'none';

        document.getElementById("radio-control-rigctld-info").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld-info").style.display = 'none';

        config.radiocontrol = 'rigctld';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });    

    // // radio settings 'rigctld' event listener
    document.getElementById("radio-control-switch-rigctld").addEventListener("click", () => {

        document.getElementById("hamlib_info_field").innerHTML = 'Define the rigctld path and port';

        document.getElementById("radio-control-disabled").style.display = 'none';
        document.getElementById("radio-control-disabled").style.visibility = 'hidden';

        document.getElementById("radio-control-radio").style.display = 'none';
        document.getElementById("radio-control-radio").style.visibility = 'hidden';

        document.getElementById("radio-control-connection").style.visibility = 'hidden';
        document.getElementById("radio-control-connection").style.display = 'none';

        document.getElementById("radio-control-ptt").style.visibility = 'hidden';
        document.getElementById("radio-control-ptt").style.display = 'none';

        document.getElementById("radio-control-network").style.display = 'none';
        document.getElementById("radio-control-network").style.visibility = 'hidden';

        document.getElementById("radio-control-rigctld").style.visibility = 'visible';
        document.getElementById("radio-control-rigctld").style.display = 'block';

        document.getElementById("radio-control-rigctld-info").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld-info").style.display = 'none';

        config.radiocontrol = 'rigctld';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

    // // radio settings 'rigctld' event listener
    document.getElementById("radio-control-switch-rigctld-info").addEventListener("click", () => {

        document.getElementById("hamlib_info_field").innerHTML = 'Start and stop rigctld .';


        document.getElementById("radio-control-disabled").style.display = 'none';
        document.getElementById("radio-control-disabled").style.visibility = 'hidden';

        document.getElementById("radio-control-radio").style.display = 'none';
        document.getElementById("radio-control-radio").style.visibility = 'hidden';

        document.getElementById("radio-control-connection").style.visibility = 'hidden';
        document.getElementById("radio-control-connection").style.display = 'none';

        document.getElementById("radio-control-ptt").style.visibility = 'hidden';
        document.getElementById("radio-control-ptt").style.display = 'none';

        document.getElementById("radio-control-network").style.display = 'none';
        document.getElementById("radio-control-network").style.visibility = 'hidden';

        document.getElementById("radio-control-rigctld").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.display = 'none';

        document.getElementById("radio-control-rigctld-info").style.visibility = 'visible';
        document.getElementById("radio-control-rigctld-info").style.display = 'block';

        config.radiocontrol = 'rigctld';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });


    // radio settings 'enable hamlib deviceport' event listener
    document.getElementById("enable_hamlib_deviceport").addEventListener("change", () => {
        enable_setting("enable_hamlib_deviceport", "hamlib_deviceport")
    });

    // radio settings 'enable hamlib serialspeed' event listener
    document.getElementById("enable_hamlib_serialspeed").addEventListener("change", () => {
        enable_setting("enable_hamlib_serialspeed", "hamlib_serialspeed")
    });

    // radio settings 'enable hamlib data bits' event listener
    document.getElementById("enable_hamlib_databits").addEventListener("change", () => {
        enable_setting("enable_hamlib_databits", "hamlib_databits")
    });

    // radio settings 'enable hamlib stop bits' event listener
    document.getElementById("enable_hamlib_stopbits").addEventListener("change", () => {
        enable_setting("enable_hamlib_stopbits", "hamlib_stopbits")
    });

    // radio settings 'enable hamlib handshake' event listener
    document.getElementById("enable_hamlib_handshake").addEventListener("change", () => {
        enable_setting("enable_hamlib_handshake", "hamlib_handshake")
    });

    // radio settings 'enable hamlib ptt port' event listener
    document.getElementById("enable_hamlib_ptt_port").addEventListener("change", () => {
        enable_setting("enable_hamlib_ptt_port", "hamlib_ptt_port")
    });

    // radio settings 'enable hamlib ptt protocol' event listener
    document.getElementById("enable_hamlib_pttprotocol").addEventListener("change", () => {
        enable_setting("enable_hamlib_pttprotocol", "hamlib_pttprotocol")
    });
        // radio settings 'enable hamlib dcd' event listener
    document.getElementById("enable_hamlib_dcd").addEventListener("change", () => {
        enable_setting("enable_hamlib_dcd", "hamlib_dcd")
    });

        // radio settings 'enable hamlib dtr state' event listener
    document.getElementById("enable_hamlib_dtrstate").addEventListener("change", () => {
        enable_setting("enable_hamlib_dtrstate", "hamlib_dtrstate")
    });


/*
document.getElementById('hamlib_rigctld_path').addEventListener('change', () => {
var fileList = document.getElementById("dataModalFile").files;
        console.log(fileList)

})
*/

document.getElementById('hamlib_rigctld_path').addEventListener('click', () => {

    ipcRenderer.send('get-file-path',{
        title: 'Title',
    });

    ipcRenderer.on('return-file-paths',(event,data)=>{
        rigctldPath = data.path.filePaths[0]
        document.getElementById("hamlib_rigctld_path").value = rigctldPath
        config.hamlib_rigctld_path = rigctldPath
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    });
})

        // radio settings 'hamlib_rigctld_server_port' event listener
    document.getElementById("hamlib_rigctld_server_port").addEventListener("change", () => {


        config.hamlib_rigctld_server_port = document.getElementById("hamlib_rigctld_server_port").value
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });



document.getElementById('hamlib_rigctld_start').addEventListener('click', () => {
    var rigctldPath = document.getElementById("hamlib_rigctld_path").value;


    var paramList = []

    var hamlib_deviceid = document.getElementById("hamlib_deviceid").value;
    paramList = paramList.concat('-m', hamlib_deviceid)

    // hamlib deviceport setting
    if (document.getElementById('enable_hamlib_deviceport').checked){
        var hamlib_deviceport = document.getElementById("hamlib_deviceport").value;
        paramList = paramList.concat('-r', hamlib_deviceport)
    }

    // hamlib serialspeed setting
    if (document.getElementById('enable_hamlib_serialspeed').checked){
        var hamlib_serialspeed = document.getElementById("hamlib_serialspeed").value;
        paramList = paramList.concat('-s', hamlib_serialspeed)
    }

    // hamlib databits setting
    if (document.getElementById('enable_hamlib_databits').checked){
        var hamlib_databits = document.getElementById("hamlib_databits").value;
        paramList = paramList.concat('--set-conf=data_bits=' + hamlib_databits)
    }

    // hamlib stopbits setting
    if (document.getElementById('enable_hamlib_stopbits').checked){
        var hamlib_stopbits = document.getElementById("hamlib_stopbits").value;
        paramList = paramList.concat('--set-conf=stop_bits=' + hamlib_stopbits)
    }

    // hamlib handshake setting
    if (document.getElementById('enable_hamlib_handshake').checked){
        var hamlib_handshake = document.getElementById("hamlib_handshake").value;
        paramList = paramList.concat('--set-conf=serial_handshake=' + hamlib_handshake)
    }

    // hamlib dcd setting
    if (document.getElementById('enable_hamlib_dcd').checked){
        var hamlib_dcd = document.getElementById("hamlib_dcd").value;
        paramList = paramList.concat('--dcd-type=' + hamlib_dcd)
    }

    // hamlib ptt port
    if (document.getElementById('enable_hamlib_ptt_port').checked){
        var hamlib_ptt_port = document.getElementById("hamlib_ptt_port").value;
        paramList = paramList.concat('-p', hamlib_ptt_port)
    }

    // hamlib ptt type
    if (document.getElementById('enable_hamlib_pttprotocol').checked){
        var hamlib_ptt_type = document.getElementById("hamlib_pttprotocol").value;
        paramList = paramList.concat('--ptt-type=' + hamlib_ptt_type)
    }

    // hamlib dtr state
    if (document.getElementById('enable_hamlib_dtrstate').checked){
        var hamlib_dtrstate = document.getElementById("hamlib_dtrstate").value;
        paramList = paramList.concat('--set-conf=dtr_state=' + hamlib_dtrstate)
    }





    var hamlib_rigctld_server_port = document.getElementById("hamlib_rigctld_server_port").value;
    paramList = paramList.concat('-t', hamlib_rigctld_server_port)




    document.getElementById('hamlib_rigctld_command').value = paramList.join(" ") // join removes the commas

    console.log(paramList)
    console.log(rigctldPath)

    let Data = {
        path: rigctldPath,
        parameters: paramList
    };
    ipcRenderer.send('request-start-rigctld', Data);



})
document.getElementById('hamlib_rigctld_stop').addEventListener('click', () => {
  ipcRenderer.send('request-stop-rigctld',{
        path: '123',
        parameters: '--version'
    });


})


    // on click waterfall scatter toggle view
    // waterfall
    document.getElementById("waterfall-scatter-switch1").addEventListener("click", () => {
        document.getElementById("chart").style.visibility = 'hidden';
        document.getElementById("chart").style.display = 'none';
        document.getElementById("chart").style.height = '0px';

        document.getElementById("scatter").style.height = '0px';
        document.getElementById("scatter").style.display = 'none';
        document.getElementById("scatter").style.visibility = 'hidden';

        document.getElementById("waterfall").style.display = 'block';
        document.getElementById("waterfall").style.visibility = 'visible';
        document.getElementById("waterfall").style.height = '100%';

        config.spectrum = 'waterfall';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
    // scatter
    document.getElementById("waterfall-scatter-switch2").addEventListener("click", () => {
        document.getElementById("scatter").style.display = 'block';
        document.getElementById("scatter").style.visibility = 'visible';
        document.getElementById("scatter").style.height = '100%';

        document.getElementById("waterfall").style.visibility = 'hidden';
        document.getElementById("waterfall").style.height = '0px';
        document.getElementById("waterfall").style.display = 'none';

        document.getElementById("chart").style.visibility = 'hidden';
        document.getElementById("chart").style.height = '0px';
        document.getElementById("chart").style.display = 'none';

        config.spectrum = 'scatter';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
    // chart
    document.getElementById("waterfall-scatter-switch3").addEventListener("click", () => {
        document.getElementById("waterfall").style.visibility = 'hidden';
        document.getElementById("waterfall").style.height = '0px';
        document.getElementById("waterfall").style.display = 'none';

        document.getElementById("scatter").style.height = '0px';
        document.getElementById("scatter").style.visibility = 'hidden';
        document.getElementById("scatter").style.display = 'none';

        document.getElementById("chart").style.height = '100%';
        document.getElementById("chart").style.display = 'block';
        document.getElementById("chart").style.visibility = 'visible';

        config.spectrum = 'chart';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });


    // on click remote tnc toggle view
    document.getElementById("local-remote-switch1").addEventListener("click", () => {
        document.getElementById("local-remote-switch1").checked = true;
        document.getElementById("local-remote-switch2").checked = false;
        document.getElementById("remote-tnc-field").style.visibility = 'hidden';
        config.tnclocation = 'localhost';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
    document.getElementById("local-remote-switch2").addEventListener("click", () => {
        document.getElementById("local-remote-switch1").checked = false;
        document.getElementById("local-remote-switch2").checked = true;
        document.getElementById("remote-tnc-field").style.visibility = 'visible';
        config.tnclocation = 'remote';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });



    // on change ping callsign
        document.getElementById("dxCall").addEventListener("change", () => {
        document.getElementById("dataModalDxCall").value = document.getElementById("dxCall").value;
            });
    // on change ping callsign
        document.getElementById("dataModalDxCall").addEventListener("change", () => {
        document.getElementById("dxCall").value = document.getElementById("dataModalDxCall").value;
        
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
        ipcRenderer.send('request-update-tnc-ip', Data);

        Data = {
            port: parseInt(document.getElementById("tnc_port").value) + 1,
            adress: document.getElementById("tnc_adress").value,
        };
        ipcRenderer.send('request-update-daemon-ip', Data);
    });

    // on change tnc port
    document.getElementById("tnc_port").addEventListener("change", () => {

        config.tnc_port = document.getElementById("tnc_port").value;
        config.daemon_port = parseInt(document.getElementById("tnc_port").value) + 1;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

            let Data = {
                port: document.getElementById("tnc_port").value,
                adress: document.getElementById("tnc_adress").value,
            };
            ipcRenderer.send('request-update-tnc-ip', Data);

            Data = {
                port: parseInt(document.getElementById("tnc_port").value) + 1,
                adress: document.getElementById("tnc_adress").value,
            };
            ipcRenderer.send('request-update-daemon-ip', Data);

    });
    
    // on change audio TX Level
    document.getElementById("audioLevelTX").addEventListener("change", () => {
        var tx_audio_level = parseInt(document.getElementById("audioLevelTX").value);
        document.getElementById("audioLevelTXvalue").innerHTML = tx_audio_level;
        config.tx_audio_level = tx_audio_level;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

            let Data = {
                command: "set_tx_audio_level",
                tx_audio_level: tx_audio_level
            };
            ipcRenderer.send('run-tnc-command', Data); 

    });
    document.getElementById("sendTestFrame").addEventListener("click", () => {
            let Data = {
                type: "set",
                command: "send_test_frame"
            };
            ipcRenderer.send('run-tnc-command', Data);        
    });
    // saveMyCall button clicked
    document.getElementById("myCall").addEventListener("input", () => {
        callsign = document.getElementById("myCall").value;
        ssid = document.getElementById("myCallSSID").value;
        callsign_ssid = callsign.toUpperCase() + '-' + ssid;
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
        pauseButton(document.getElementById("sendPing"),500);
        sock.sendPing(dxcallsign);
    });

    // dataModalstartPing button clicked
    document.getElementById("dataModalSendPing").addEventListener("click", () => {
        var dxcallsign = document.getElementById("dataModalDxCall").value;
        dxcallsign = dxcallsign.toUpperCase();
        sock.sendPing(dxcallsign);
    });
    
    
    
    

    // close app, update and restart
    document.getElementById("update_and_install").addEventListener("click", () => {
        ipcRenderer.send('request-restart-and-install');
    });
    
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


    // sendCQ button clicked
    document.getElementById("sendCQ").addEventListener("click", () => {
        pauseButton(document.getElementById("sendCQ"),500);
        sock.sendCQ();
    });


    // Start beacon button clicked
    document.getElementById("startBeacon").addEventListener("click", () => {
        interval = document.getElementById("beaconInterval").value;
        config.beacon_interval = interval;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        sock.startBeacon(interval);
    });  
    
    // sendscatter Switch clicked
    document.getElementById("scatterSwitch").addEventListener("click", () => {
        console.log(document.getElementById("scatterSwitch").checked);
        if(document.getElementById("scatterSwitch").checked == true){
            config.enable_scatter = "True";       
        } else {
            config.enable_scatter = "False";       
        }
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });  
    
    // sendfft Switch clicked
    document.getElementById("fftSwitch").addEventListener("click", () => {
        if(document.getElementById("fftSwitch").checked == true){
            config.enable_fft = "True";    
        } else {
            config.enable_fft = "False";       
        }
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

    // enable 500z Switch clicked
    document.getElementById("500HzModeSwitch").addEventListener("click", () => {
        if(document.getElementById("500HzModeSwitch").checked == true){
            config.low_bandwidth_mode = "True";       
        } else {
            config.low_bandwidth_mode = "False";       
        }
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
    
    // enable response to cq clicked
    document.getElementById("respondCQSwitch").addEventListener("click", () => {
        if(document.getElementById("respondCQSwitch").checked == true){
            config.respond_to_cq = "True";       
        } else {
            config.respond_to_cq = "False";       
        }
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });    

    // enable explorer Switch clicked
    document.getElementById("ExplorerSwitch").addEventListener("click", () => {
        if(document.getElementById("ExplorerSwitch").checked == true){
            config.enable_explorer = "True";
        } else {
            config.enable_explorer = "False";
        }
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

    // enable fsk Switch clicked
    document.getElementById("fskModeSwitch").addEventListener("click", () => {
        if(document.getElementById("fskModeSwitch").checked == true){
            config.enable_fsk = "True";       
        } else {
            config.enable_fsk = "False";       
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
    document.getElementById("theme_selector").addEventListener("click", () => {
        
        var theme = document.getElementById("theme_selector").value;
        if(theme != 'default'){
            var theme_path = "../node_modules/bootswatch/dist/"+ theme +"/bootstrap.min.css";
        } else {
            var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
        }
        
        //update path to css file
        document.getElementById("bootstrap_theme").href = escape(theme_path)
        
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
    
        // Update channel selector clicked
    document.getElementById("update_channel_selector").addEventListener("click", () => {
        config.update_channel = document.getElementById("update_channel_selector").value;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    });    

    // rx buffer size selector clicked
    document.getElementById("rx_buffer_size").addEventListener("click", () => {
        var rx_buffer_size = document.getElementById("rx_buffer_size").value;
        config.rx_buffer_size = rx_buffer_size;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
    

    //screen size
    window.addEventListener('resize',() => {

    config.screen_height = window.innerHeight;
    config.screen_width = window.innerWidth;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });


    // Stop beacon button clicked
    document.getElementById("stopBeacon").addEventListener("click", () => {
        sock.stopBeacon();
    });

    // Explorer button clicked
    document.getElementById("openExplorer").addEventListener("click", () => {
        shell.openExternal('https://explorer.freedata.app/?myCall=' + document.getElementById("myCall").value);
    });

    // startTNC button clicked
    document.getElementById("startTNC").addEventListener("click", () => {

        var tuning_range_fmin = document.getElementById("tuning_range_fmin").value;
        var tuning_range_fmax = document.getElementById("tuning_range_fmax").value;
                
        var rigctld_ip = document.getElementById("hamlib_rigctld_ip").value;
        var rigctld_port = document.getElementById("hamlib_rigctld_port").value;
        var hamlib_rigctld_server_port = document.getElementById("hamlib_rigctld_server_port").value;

        var deviceid = document.getElementById("hamlib_deviceid").value;
        var deviceport = document.getElementById("hamlib_deviceport").value;
        var serialspeed = document.getElementById("hamlib_serialspeed").value;
        var pttprotocol = document.getElementById("hamlib_pttprotocol").value;
        var hamlib_dcd = document.getElementById("hamlib_dcd").value;

        var mycall = document.getElementById("myCall").value;
        var ssid = document.getElementById("myCallSSID").value;
        callsign_ssid = mycall.toUpperCase() + '-' + ssid;
        
        var mygrid = document.getElementById("myGrid").value;
        
        var rx_audio = document.getElementById("audio_input_selectbox").value;
        var tx_audio = document.getElementById("audio_output_selectbox").value;
        
        var pttport = document.getElementById("hamlib_ptt_port").value;
        var data_bits = document.getElementById('hamlib_databits').value;
        var stop_bits = document.getElementById('hamlib_stopbits').value;
        var handshake = document.getElementById('hamlib_handshake').value;
        
        if (document.getElementById("scatterSwitch").checked == true){
            var enable_scatter = "True";
        } else {
            var enable_scatter = "False";
        }
        

        if (document.getElementById("fftSwitch").checked == true){
            var enable_fft = "True";
        } else {
            var enable_fft = "False";
        }

        if (document.getElementById("500HzModeSwitch").checked == true){
            var low_bandwidth_mode = "True";
        } else {
            var low_bandwidth_mode = "False";
        }
        
        if (document.getElementById("fskModeSwitch").checked == true){
            var enable_fsk = "True";
        } else {
            var enable_fsk = "False";
        }        

        if (document.getElementById("respondCQSwitch").checked == true){
            var respond_to_cq = "True";
        } else {
            var respond_to_cq = "False";
        } 

        if (document.getElementById("ExplorerSwitch").checked == true){
            var enable_explorer = "True";
        } else {
            var enable_explorer = "False";
        }
       
        // loop through audio device list and select
        for(i = 0; i < document.getElementById("audio_input_selectbox").length; i++) {
            device = document.getElementById("audio_input_selectbox")[i];
      
            if (device.value == rx_audio) {
                console.log(device.text);
                config.rx_audio = device.text;
            }
        }

        // loop through audio device list and select
        for(i = 0; i < document.getElementById("audio_output_selectbox").length; i++) {
            device = document.getElementById("audio_output_selectbox")[i];
      
            if (device.value == tx_audio) {
                console.log(device.text);
                config.tx_audio = device.text;
            }
        }        

        if (!document.getElementById("radio-control-switch-disabled").checked) {
            var radiocontrol = 'rigctld';
        } else {
            var radiocontrol = 'disabled';
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
        config.hamlib_pttport = pttport;
        config.hamlib_data_bits = data_bits;
        config.hamlib_stop_bits = stop_bits;
        config.hamlib_handshake = handshake;
        config.hamlib_dcd = hamlib_dcd;
        //config.deviceid_rigctl = deviceid_rigctl;
        //config.serialspeed_rigctl = serialspeed_rigctl;
        //config.pttprotocol_rigctl = pttprotocol_rigctl;
        config.hamlib_rigctld_port = rigctld_port;
        config.hamlib_rigctld_ip = rigctld_ip;
        config.hamlib_rigctld_server_port = hamlib_rigctld_server_port;
        //config.deviceport_rigctl = deviceport_rigctl;
        config.enable_scatter = enable_scatter;
        config.enable_fft = enable_fft;
        config.enable_fsk = enable_fsk;
        config.low_bandwidth_mode = low_bandwidth_mode;
        config.tx_audio_level = tx_audio_level;
        config.respond_to_cq = respond_to_cq;
        config.rx_buffer_size = rx_buffer_size;
        config.enable_explorer = enable_explorer;

        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));


        // collapse settings screen
        // deactivated this part so start / stop is a little bit more smooth. We are getting problems because of network delay
        /*
        var collapseFirstRow = new bootstrap.Collapse(document.getElementById('collapseFirstRow'), {toggle: false})
        collapseFirstRow.hide()
        var collapseSecondRow = new bootstrap.Collapse(document.getElementById('collapseSecondRow'), {toggle: false})
        collapseSecondRow.hide()
        var collapseThirdRow = new bootstrap.Collapse(document.getElementById('collapseThirdRow'), {toggle: false})
        collapseThirdRow.show() 
        var collapseFourthRow = new bootstrap.Collapse(document.getElementById('collapseFourthRow'), {toggle: false})
        collapseFourthRow.show() 
        */


        daemon.startTNC(callsign_ssid, mygrid, rx_audio, tx_audio, radiocontrol, deviceid, deviceport, pttprotocol, pttport, serialspeed, data_bits, stop_bits, handshake, rigctld_ip, rigctld_port, enable_fft, enable_scatter, low_bandwidth_mode, tuning_range_fmin, tuning_range_fmax, enable_fsk, tx_audio_level, respond_to_cq, rx_buffer_size, enable_explorer);
        
        
    })

    document.getElementById("tncLog").addEventListener("click", () => {

            ipcRenderer.send('request-open-tnc-log');
    
    
    
})


    // stopTNC button clicked
    document.getElementById("stopTNC").addEventListener("click", () => {
        
        daemon.stopTNC();
        
                
        // collapse settings screen
        // deactivated this part so start / stop is a little bit more smooth. We are getting problems because of network delay
        /*
        var collapseFirstRow = new bootstrap.Collapse(document.getElementById('collapseFirstRow'), {toggle: false})
        collapseFirstRow.show()
        var collapseSecondRow = new bootstrap.Collapse(document.getElementById('collapseSecondRow'), {toggle: false})
        collapseSecondRow.show() 
        
        var collapseThirdRow = new bootstrap.Collapse(document.getElementById('collapseThirdRow'), {toggle: false})
        collapseThirdRow.hide()
        var collapseFourthRow = new bootstrap.Collapse(document.getElementById('collapseFourthRow'), {toggle: false})
        collapseFourthRow.hide() 
        */

        
  
    })
    
    
    // openDataModule button clicked
    // not necessesary at this time beacuse bootstrap handles this 
    // document.getElementById("openDataModule").addEventListener("click", () => {
    //   var transmitFileSidebar = document.getElementById('transmitFileSidebar')
    //   var bstransmitFileSidebar = new bootstrap.Offcanvas(transmitFileSidebar)
    //   bstransmitFileSidebar.show()    
    //})

    // openReceivedFiles button clicked
    // not necessesary at this time beacuse bootstrap handles this 
    //document.getElementById("openReceivedFiles").addEventListener("click", () => {
    //   var transmitFileSidebar = document.getElementById('transmitFileSidebar')
    //   var bstransmitFileSidebar = new bootstrap.Offcanvas(transmitFileSidebar)
    //   bstransmitFileSidebar.show()    
    //})


    // TEST HAMLIB
    document.getElementById("testHamlib").addEventListener("click", () => {
        

        var data_bits = document.getElementById("hamlib_databits").value;
        var stop_bits = document.getElementById("hamlib_stopbits").value;
        var handshake = document.getElementById("hamlib_handshake").value;
        var pttport = document.getElementById("hamlib_ptt_port").value;

        var rigctld_ip = document.getElementById("hamlib_rigctld_ip").value;
        var rigctld_port = document.getElementById("hamlib_rigctld_port").value;

        var deviceid = document.getElementById("hamlib_deviceid").value;
        var deviceport = document.getElementById("hamlib_deviceport").value;
        var serialspeed = document.getElementById("hamlib_serialspeed").value;
        var pttprotocol = document.getElementById("hamlib_pttprotocol").value;

        if (document.getElementById("radio-control-switch-disabled").checked) {
            var radiocontrol = 'disabled';
        } else {
            var radiocontrol = 'rigctld';
        }     

        daemon.testHamlib(radiocontrol, deviceid, deviceport, serialspeed, pttprotocol, pttport, data_bits, stop_bits, handshake, rigctld_ip, rigctld_port)                 
    })


    // START TRANSMISSION
    document.getElementById("startTransmission").addEventListener("click", () => {
        //document.getElementById("transmitFileSidebar").style.width = "0px";
        /* not neccessary at this time because handled by bootstap inside html
            var transmitFileSidebar = document.getElementById('transmitFileSidebar')
            var bstransmitFileSidebar = new bootstrap.Offcanvas(transmitFileSidebar)
            bstransmitFileSidebar.show()   
        */
        
        
    
        var fileList = document.getElementById("dataModalFile").files;
        console.log(fileList)
        var reader = new FileReader();
        reader.readAsBinaryString(fileList[0]);
        //reader.readAsDataURL(fileList[0]);

        reader.onload = function(e) {
            // binary data

            var data = e.target.result;
            console.log(data);
            

            let Data = {
                command: "send_file",
                dxcallsign: document.getElementById("dataModalDxCall").value.toUpperCase(),
                mode: document.getElementById("datamode").value,
                frames: document.getElementById("framesperburst").value,
                filetype: fileList[0].type,
                filename: fileList[0].name,
                data: data,
                checksum: '123123123',
            };
            // only send command if dxcallsign entered and we have a file selected
            if(document.getElementById("dataModalDxCall").value.length > 0){
                ipcRenderer.send('run-tnc-command', Data);
            }
        };
        reader.onerror = function(e) {
            // error occurred
            console.log('Error : ' + e.type);
        };

    })
    // STOP TRANSMISSION
    document.getElementById("stopTransmission").addEventListener("click", () => {
            let Data = {
                command: "stop_transmission"
            };
            ipcRenderer.send('run-tnc-command', Data);    
    })
    
    // STOP TRANSMISSION AND CONNECRTION
    document.getElementById("stop_transmission_connection").addEventListener("click", () => {
            let Data = {
                command: "stop_transmission"
            };
            ipcRenderer.send('run-tnc-command', Data);
            sock.disconnectARQ();    
    })
    
    
    // OPEN CHAT MODULE
    document.getElementById("openRFChat").addEventListener("click", () => {
            let Data = {
                command: "openRFChat"
            };
            ipcRenderer.send('request-show-chat-window', Data);    
    })


    
    
    
    

  
})

  


ipcRenderer.on('action-update-tnc-state', (event, arg) => {
    // update FFT
    if (typeof(arg.fft) !== 'undefined') {
        var array = JSON.parse("[" + arg.fft + "]");
        spectrum.addData(array[0]);

    }

    if (typeof(arg.mycallsign) !== 'undefined') {
        // split document title by looking for Call then split and update it
        //var documentTitle = document.title.split('Call:')
        //document.title = documentTitle[0] + 'Call: ' + arg.mycallsign;
        updateTitle(arg.mycallsign);
    }

    // update mygrid information with data from tnc
    if (typeof(arg.mygrid) !== 'undefined') {
        document.getElementById("myGrid").value = arg.mygrid;
    }

    // DATA STATE
    global.rxBufferLengthTnc = arg.rx_buffer_length


    // START OF SCATTER CHART

    const scatterConfig = {
                plugins: {
                    legend: {
                        display: false,
                        },
                    tooltip: {
                        enabled: false
                    },
                    
                    annotation: {
                        annotations: {
                            line1: {
                              type: 'line',
                              yMin: 0,
                              yMax: 0,
                              borderColor: 'rgb(255, 99, 132)',
                              borderWidth: 2,
                            },
                            line2: {
                              type: 'line',
                              xMin: 0,
                              xMax: 0,
                              borderColor: 'rgb(255, 99, 132)',
                              borderWidth: 2,
                            }
                         }   
                     },   
        
        
        
                },
                animations: false,
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        display: true,
                        min: -80,
                        max: 80,
                        ticks: {
                            display: false
                        }            
                    },
                    y: {
                    
                        display: true,
                        min: -80,
                        max: 80,
                        ticks: {
                            display: false,
                        }
                    }
                }
        }
    var scatterData = arg.scatter
    var newScatterData = {
        datasets: [{
            //label: 'constellation diagram',
            data: scatterData,
            options: scatterConfig,
            backgroundColor: 'rgb(255, 99, 132)'
        }],
    };

    if (typeof(arg.scatter) == 'undefined') {
        var scatterSize = 0;
    } else {
        var scatterSize = arg.scatter.length;
    }

     if (global.scatterData != newScatterData && scatterSize > 0) {
     global.scatterData = newScatterData;

        if (typeof(global.scatterChart) == 'undefined') {
        var scatterCtx = document.getElementById('scatter').getContext('2d');
        global.scatterChart = new Chart(scatterCtx, {
            type: 'scatter',
            data: global.scatterData,
            options: scatterConfig
        });
    } else {
        global.scatterChart.data = global.scatterData;
        global.scatterChart.update();
    }
}
    // END OF SCATTER CHART

    // START OF SPEED CHART

    var speedDataTime = []

    if (typeof(arg.speed_list) == 'undefined') {
        var speed_listSize = 0;
    } else {
        var speed_listSize = arg.speed_list.length;
    }

    for (var i=0; i < speed_listSize; i++) {
        var timestamp = arg.speed_list[i].timestamp * 1000
        var h = new Date(timestamp).getHours();
        var m = new Date(timestamp).getMinutes();
        var s = new Date(timestamp).getSeconds();
        var time = h + ':' + m + ':' + s;
        speedDataTime.push(time)
    }

    var speedDataBpm = []
    for (var i=0; i < speed_listSize; i++) {
        speedDataBpm.push(arg.speed_list[i].bpm)

    }

    var speedDataSnr = []
    for (var i=0; i < speed_listSize; i++) {
        speedDataSnr.push(arg.speed_list[i].snr)
    }


    var speedChartConfig = {
      type: 'line',
    };

    var newSpeedData = {
        labels: speedDataTime,
        datasets: [
            {
                type: 'line',
                label: 'SNR[dB]',
                data: speedDataSnr,
                borderColor: 'rgb(255, 99, 132, 1.0)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                order: 1,
                yAxisID: 'SNR',
            },
            {
                type: 'bar',
                label: 'Speed[bpm]',
                data: speedDataBpm,
                borderColor: 'rgb(120, 100, 120, 1.0)',
                backgroundColor: 'rgba(120, 100, 120, 0.2)',
                order: 0,
                yAxisID: 'SPEED',
            }
        ],

    };

var speedChartOptions = {
            responsive: true,
            animations: true,
            cubicInterpolationMode: 'monotone',
            tension: 0.4,
            scales: {
              SNR:{
                type: 'linear',
                ticks: { beginAtZero: true, color: 'rgb(255, 99, 132)' },
                position: 'right',
              },
              SPEED :{
                type: 'linear',
                ticks: { beginAtZero: true, color: 'rgb(120, 100, 120)' },
                position: 'left',
                grid: {
                    drawOnChartArea: false, // only want the grid lines for one axis to show up
                },
              },
              x: { ticks: { beginAtZero: true } },
            }
        }

    if (typeof(global.speedChart) == 'undefined') {
        var speedCtx = document.getElementById('chart').getContext('2d');
        global.speedChart = new Chart(speedCtx, {
            data: newSpeedData,
            options: speedChartOptions
        });
    } else {
        if(speedDataSnr.length > 0){
            global.speedChart.data = newSpeedData;
            global.speedChart.update();
        }
    }

    // END OF SPEED CHART

    // PTT STATE
    if (arg.ptt_state == 'True') {
        document.getElementById("ptt_state").className = "btn btn-sm btn-danger";
    } else if (arg.ptt_state == 'False') {
        document.getElementById("ptt_state").className = "btn btn-sm btn-success";
    } else {
        document.getElementById("ptt_state").className = "btn btn-sm btn-secondary";
    }

    // AUDIO RECORDING
    if (arg.audio_recording == 'True') {
        document.getElementById("startStopRecording").className = "btn btn-sm btn-danger";
        document.getElementById("startStopRecording").innerHTML = "Stop Rec"
    } else if (arg.ptt_state == 'False') {
        document.getElementById("startStopRecording").className = "btn btn-sm btn-danger";
        document.getElementById("startStopRecording").innerHTML = "Start Rec"
    } else {
        document.getElementById("startStopRecording").className = "btn btn-sm btn-danger";
        document.getElementById("startStopRecording").innerHTML = "Start Rec"
    }





    // CHANNEL BUSY STATE
    if (arg.channel_busy == 'True') {
        document.getElementById("channel_busy").className = "btn btn-sm btn-danger";

    } else if (arg.channel_busy == 'False') {
        document.getElementById("channel_busy").className = "btn btn-sm btn-success";

    } else {
        document.getElementById("channel_busy").className = "btn btn-sm btn-secondary";

    }

    // BUSY STATE
    if (arg.busy_state == 'BUSY') {
        document.getElementById("busy_state").className = "btn btn-sm btn-danger";
        
        document.getElementById("startTransmission").disabled = true;
        //document.getElementById("stopTransmission").disabled = false;

    } else if (arg.busy_state == 'IDLE') {
        document.getElementById("busy_state").className = "btn btn-sm btn-success";

    } else {
        document.getElementById("busy_state").className = "btn btn-sm btn-secondary";
        document.getElementById("startTransmission").disabled = true;
        //document.getElementById("stopTransmission").disabled = false;
    }

    // ARQ STATE
    if (arg.arq_state == 'True') {
        document.getElementById("arq_state").className = "btn btn-sm btn-warning";
        //document.getElementById("startTransmission").disabled = true;
        document.getElementById("startTransmission").disabled = false;
        //document.getElementById("stopTransmission").disabled = false;
    } else if (arg.arq_state == 'False') {
        document.getElementById("arq_state").className = "btn btn-sm btn-secondary";
        document.getElementById("startTransmission").disabled = false;
        //document.getElementById("stopTransmission").disabled = true;
    } else {
        document.getElementById("arq_state").className = "btn btn-sm btn-secondary";
        //document.getElementById("startTransmission").disabled = true;
        document.getElementById("startTransmission").disabled = false;
        //document.getElementById("stopTransmission").disabled = false;
    }

    // ARQ SESSION
    if (arg.arq_session == 'True') {
        document.getElementById("arq_session").className = "btn btn-sm btn-warning";

    } else if (arg.arq_session == 'False') {
        document.getElementById("arq_session").className = "btn btn-sm btn-secondary";

    } else {
        document.getElementById("arq_session").className = "btn btn-sm btn-secondary";

    }

    // HAMLIB STATUS
    if (arg.hamlib_status == 'connected') {
        document.getElementById("rigctld_state").className = "btn btn-success btn-sm";

    } else {
        document.getElementById("rigctld_state").className = "btn btn-secondary btn-sm";
    }



    // BEACON STATE
    if (arg.beacon_state == 'True') {
        document.getElementById("startBeacon").className = "btn btn-sm btn-success spinner-grow";
        document.getElementById("startBeacon").disabled = true;
        document.getElementById("beaconInterval").disabled = true;
        document.getElementById("stopBeacon").disabled = false;
    } else if (arg.beacon_state == 'False') {
        document.getElementById("startBeacon").className = "btn btn-sm btn-success";
        document.getElementById("startBeacon").disabled = false;
        document.getElementById("beaconInterval").disabled = false;
        document.getElementById("stopBeacon").disabled = true;
    } else {
        document.getElementById("startBeacon").className = "btn btn-sm btn-success";
        document.getElementById("startBeacon").disabled = false;
        document.getElementById("stopBeacon").disabled = true;
        document.getElementById("beaconInterval").disabled = false;
    }
    // dbfs
    // https://www.moellerstudios.org/converting-amplitude-representations/
    if (dbfs_level_raw != arg.dbfs_level){
        dbfs_level_raw = arg.dbfs_level
        dbfs_level = Math.pow(10, arg.dbfs_level / 20) * 100

        document.getElementById("dbfs_level_value").innerHTML = Math.round(arg.dbfs_level) + ' dBFS'
        var dbfscntrl = document.getElementById("dbfs_level");
        dbfscntrl.setAttribute("aria-valuenow", dbfs_level);
        dbfscntrl.setAttribute("style", "width:" + dbfs_level + "%;");
    }

    // SET FREQUENCY
    // https://stackoverflow.com/a/2901298
    var freq = arg.frequency.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    document.getElementById("frequency").innerHTML = freq;
    //document.getElementById("newFrequency").value = arg.frequency;

    // SET MODE
    document.getElementById("mode").innerHTML = arg.mode;

    // SET bandwidth
    document.getElementById("bandwidth").innerHTML = arg.bandwidth;

    // SET BYTES PER MINUTE
    if (typeof(arg.arq_bytes_per_minute) == 'undefined') {
        var arq_bytes_per_minute = 0;
    } else {
        var arq_bytes_per_minute = arg.arq_bytes_per_minute;
    }
    document.getElementById("bytes_per_min").innerHTML = arq_bytes_per_minute;

    // SET BYTES PER MINUTE COMPRESSED
    if (typeof(arg.arq_bytes_per_minute) == 'undefined') {
        var arq_bytes_per_minute_compressed = 0;
    } else {
        var arq_bytes_per_minute_compressed = Math.round(arg.arq_bytes_per_minute * arg.arq_compression_factor);
    }
    document.getElementById("bytes_per_min_compressed").innerHTML = arq_bytes_per_minute_compressed;

    // SET TIME LEFT UNTIL FINIHED
    if (typeof(arg.arq_seconds_until_finish) == 'undefined') {
        var time_left = 0;
    } else {
        var arq_seconds_until_finish = arg.arq_seconds_until_finish
        var hours = Math.floor(arq_seconds_until_finish / 3600);
        var minutes = Math.floor((arq_seconds_until_finish % 3600) / 60 );
        var seconds = arq_seconds_until_finish % 60;

        if(hours < 0) {
            hours = 0;
        }
        if(minutes < 0) {
            minutes = 0;
        }
        if(seconds < 0) {
            seconds = 0;
        }
        var time_left = "time left: ~ "+ minutes + "min" + " " + seconds + "s";
    }
    document.getElementById("transmission_timeleft").innerHTML = time_left;


    
    // SET SPEED LEVEL

    if(arg.speed_level >= 0) {
        document.getElementById("speed_level").className = "bi bi-reception-1";
    }
    if(arg.speed_level >= 1) {
        document.getElementById("speed_level").className = "bi bi-reception-2";
    }
    if(arg.speed_level >= 2) {
        document.getElementById("speed_level").className = "bi bi-reception-3";
    }
    if(arg.speed_level >= 3) {
        document.getElementById("speed_level").className = "bi bi-reception-4";
    }
    if(arg.speed_level >= 4) {
        document.getElementById("speed_level").className = "bi bi-reception-4";
    }

    
    
    
    // SET TOTAL BYTES
    if (typeof(arg.total_bytes) == 'undefined') {
        var total_bytes = 0;
    } else {
        var total_bytes = arg.total_bytes;
    }
    document.getElementById("total_bytes").innerHTML = total_bytes;
    //Only update if values differ to prevent re-rendering control
    var txprog = document.getElementById("transmission_progress")
    if (txprog.getAttribute("aria-valuenow") != arg.arq_transmission_percent)
        txprog.setAttribute("aria-valuenow", arg.arq_transmission_percent);
    if (txprog.getAttribute("style") !=  "width:" + arg.arq_transmission_percent + "%;")
        txprog.setAttribute("style", "width:" + arg.arq_transmission_percent + "%;");

    // UPDATE HEARD STATIONS
    var tbl = document.getElementById("heardstations");
    document.getElementById("heardstations").innerHTML = '';

    if (typeof(arg.stations) == 'undefined') {
        var heardStationsLength = 0;
    } else {
        var heardStationsLength = arg.stations.length;
    }

    for (i = 0; i < heardStationsLength; i++) {

        // first we update the PING window
        //if (arg.stations[i]['dxcallsign'].split('-',2)[0] == document.getElementById("dxCall").value.split['-',2][0]) {
        if (arg.stations[i]['dxcallsign'] == document.getElementById("dxCall").value.toUpperCase()) {
            var dxGrid = arg.stations[i]['dxgrid'];
            var myGrid = document.getElementById("myGrid").value;
            try {
                var dist = parseInt(distance(myGrid, dxGrid)) + ' km';
                //document.getElementById("pingDistance").innerHTML = dist;
                document.getElementById("dataModalPingDistance").innerHTML = dist;
            } catch {
                //document.getElementById("pingDistance").innerHTML = '---';
                document.getElementById("dataModalPingDistance").innerHTML = '---';
            }
            //document.getElementById("pingDB").innerHTML = arg.stations[i]['snr'];
            document.getElementById("dataModalPingDB").innerHTML = arg.stations[i]['snr'];
        }

        // now we update the heard stations list
        var row = document.createElement("tr");
        //https://stackoverflow.com/q/51421470

        //https://stackoverflow.com/a/847196
        timestampRaw = arg.stations[i]['timestamp'];
        var date = new Date(timestampRaw * 1000);
        var hours = date.getHours();
        var minutes = "0" + date.getMinutes();
        var seconds = "0" + date.getSeconds();
        var datetime = hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);

        var timestamp = document.createElement("td");
        var timestampText = document.createElement('span');
        timestampText.innerText = datetime;
        timestamp.appendChild(timestampText);

        var frequency = document.createElement("td");
        var frequencyText = document.createElement('span');
        frequencyText.innerText = arg.stations[i]['frequency'];
        frequency.appendChild(frequencyText);
        
        
        var dxCall = document.createElement("td");
        var dxCallText = document.createElement('span');
        dxCallText.innerText = arg.stations[i]['dxcallsign'];
        row.addEventListener("click", function(e) {
            document.getElementById("dxCall").value = dxCallText.innerText;
          });
        dxCall.appendChild(dxCallText);

        var dxGrid = document.createElement("td");
        var dxGridText = document.createElement('span');
        dxGridText.innerText = arg.stations[i]['dxgrid'];
        dxGrid.appendChild(dxGridText);

        var gridDistance = document.createElement("td");
        var gridDistanceText = document.createElement('span');

        try {
            gridDistanceText.innerText = parseInt(distance(document.getElementById("myGrid").value, arg.stations[i]['dxgrid'])) + ' km';
        } catch {
            gridDistanceText.innerText = '---';
        }
        gridDistance.appendChild(gridDistanceText);

        var dataType = document.createElement("td");
        var dataTypeText = document.createElement('span');
        dataTypeText.innerText = arg.stations[i]['datatype'];
        dataType.appendChild(dataTypeText);

        if(arg.stations[i]['datatype'] == 'DATA-CHANNEL'){
            dataTypeText.innerText = 'DATA-C';
            dataType.appendChild(dataTypeText);
        }
        
        if(arg.stations[i]['datatype'] == 'SESSION-HB'){
            dataTypeText.innerHTML = '<i class="bi bi-heart-pulse-fill"></i>';
            dataType.appendChild(dataTypeText);
        }


        if (dataTypeText.innerText == 'CQ CQ CQ') {
            row.classList.add("table-success");

        }

        if (dataTypeText.innerText == 'DATA-C') {
            dataTypeText.innerHTML = '<i class="bi bi-file-earmark-binary-fill"></i>';
            row.classList.add("table-warning");
        }

        if (dataTypeText.innerText == 'BEACON') {
            row.classList.add("table-light");
        }

        if (dataTypeText.innerText == 'PING') {
            row.classList.add("table-info");
        }

        if (dataTypeText.innerText == 'PING-ACK') {
            row.classList.add("table-primary");
        }

        var snr = document.createElement("td");
        var snrText = document.createElement('span');
        snrText.innerText = arg.stations[i]['snr'];
        snr.appendChild(snrText);

        var offset = document.createElement("td");
        var offsetText = document.createElement('span');
        offsetText.innerText = arg.stations[i]['offset'];
        offset.appendChild(offsetText);

        row.appendChild(timestamp);
        row.appendChild(frequency);
        row.appendChild(dxCall);
        row.appendChild(dxGrid);
        row.appendChild(gridDistance);
        row.appendChild(dataType);
        row.appendChild(snr);
        row.appendChild(offset);

        tbl.appendChild(row);
    }

});

ipcRenderer.on('action-update-daemon-state', (event, arg) => {
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
        if (document.getElementById("audio_input_selectbox").length != arg.input_devices.length) {
            document.getElementById("audio_input_selectbox").innerHTML = "";
            for (i = 0; i < arg.input_devices.length; i++) {
                var option = document.createElement("option");
                option.text = arg.input_devices[i]['name'];
                option.value = arg.input_devices[i]['id'];
                // set device from config if available
                
                if(config.rx_audio == option.text){
                    option.setAttribute('selected', true);
                }
                document.getElementById("audio_input_selectbox").add(option);
            }
        }
    }
    // UPDATE AUDIO OUTPUT
    if (arg.tnc_running_state == "stopped") {
        if (document.getElementById("audio_output_selectbox").length != arg.output_devices.length) {
            document.getElementById("audio_output_selectbox").innerHTML = "";
            for (i = 0; i < arg.output_devices.length; i++) {
                var option = document.createElement("option");
                option.text = arg.output_devices[i]['name'];
                option.value = arg.output_devices[i]['id'];               
                // set device from config if available
                if(config.tx_audio == option.text){
                    option.setAttribute('selected', true);
                }
                document.getElementById("audio_output_selectbox").add(option);
            }
        }
    }

    // UPDATE SERIAL DEVICES
    if (arg.tnc_running_state == "stopped") {
        if (document.getElementById("hamlib_deviceport").length != arg.serial_devices.length) {
            document.getElementById("hamlib_deviceport").innerHTML = "";
            for (i = 0; i < arg.serial_devices.length; i++) {
                var option = document.createElement("option");
                option.text = arg.serial_devices[i]['port'] + ' -- ' + arg.serial_devices[i]['description'];
                option.value = arg.serial_devices[i]['port'];
                // set device from config if available
                if(config.hamlib_deviceport == option.value){
                    option.setAttribute('selected', true);
                }
                document.getElementById("hamlib_deviceport").add(option);
   
            }
        }


               
    }
    
    if (arg.tnc_running_state == "stopped") {
        if (document.getElementById("hamlib_ptt_port").length != arg.serial_devices.length) {
            document.getElementById("hamlib_ptt_port").innerHTML = "";
            for (i = 0; i < arg.serial_devices.length; i++) {
                var option = document.createElement("option");
                option.text = arg.serial_devices[i]['description'];
                option.value = arg.serial_devices[i]['port'];
                // set device from config if available
                if(config.hamlib_pttport == option.value){
                    option.setAttribute('selected', true);
                }
                document.getElementById("hamlib_ptt_port").add(option);
            }
        }  
    }
    
    
});


// ACTION UPDATE HAMLIB TEST
ipcRenderer.on('action-update-hamlib-test', (event, arg) => {
    console.log(arg.hamlib_result);
    if (arg.hamlib_result == 'SUCCESS') {
        document.getElementById("testHamlib").className = "btn btn-sm btn-success";
        // BUTTON HAS BEEN REMOVED
        //document.getElementById("testHamlibAdvanced").className = "btn btn-sm btn-success";


    }
    if (arg.hamlib_result == 'NOSUCCESS') {
        document.getElementById("testHamlib").className = "btn btn-sm btn-warning";
        // BUTTON HAS BEEN REMOVED
        //document.getElementById("testHamlibAdvanced").className = "btn btn-sm btn-warning";

    }
    if (arg.hamlib_result == 'FAILED') {
        document.getElementById("testHamlib").className = "btn btn-sm btn-danger";
        // BUTTON HAS BEEN REMOVED
        //document.getElementById("testHamlibAdvanced").className = "btn btn-sm btn-danger";
    }

});



ipcRenderer.on('action-update-daemon-connection', (event, arg) => {

    if (arg.daemon_connection == 'open') {
        document.getElementById("daemon_connection_state").className = "btn btn-success";
        //document.getElementById("blurdiv").style.webkitFilter = "blur(0px)";

    }
    if (arg.daemon_connection == 'opening') {
        document.getElementById("daemon_connection_state").className = "btn btn-warning";
        //document.getElementById("blurdiv").style.webkitFilter = "blur(10px)";

    }
    if (arg.daemon_connection == 'closed') {
        document.getElementById("daemon_connection_state").className = "btn btn-danger";
        //document.getElementById("blurdiv").style.webkitFilter = "blur(10px)";
    }

});

ipcRenderer.on('action-update-tnc-connection', (event, arg) => {

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
        var collapseFirstRow = new bootstrap.Collapse(document.getElementById('collapseFirstRow'), {toggle: false})
        collapseFirstRow.hide();
        var collapseSecondRow = new bootstrap.Collapse(document.getElementById('collapseSecondRow'), {toggle: false})
        collapseSecondRow.hide();
        var collapseThirdRow = new bootstrap.Collapse(document.getElementById('collapseThirdRow'), {toggle: false})
        collapseThirdRow.show();     
        var collapseFourthRow = new bootstrap.Collapse(document.getElementById('collapseFourthRow'), {toggle: false})
        collapseFourthRow.show();         
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
        var collapseFirstRow = new bootstrap.Collapse(document.getElementById('collapseFirstRow'), {toggle: false})
        collapseFirstRow.show();
        var collapseSecondRow = new bootstrap.Collapse(document.getElementById('collapseSecondRow'), {toggle: false})
        collapseSecondRow.show();
        var collapseThirdRow = new bootstrap.Collapse(document.getElementById('collapseThirdRow'), {toggle: false})
        collapseThirdRow.hide();   
        var collapseFourthRow = new bootstrap.Collapse(document.getElementById('collapseFourthRow'), {toggle: false})
        collapseFourthRow.hide();
    }






});


ipcRenderer.on('action-update-rx-buffer', (event, arg) => {
    
    var data = arg.data["data"];

    var tbl = document.getElementById("rx-data");
    document.getElementById("rx-data").innerHTML = '';


    for (i = 0; i < arg.data.length; i++) {

        // first we update the PING window
        if (arg.data[i]['dxcallsign'] == document.getElementById("dxCall").value.toUpperCase()) {
            /*
            // if we are sending data without doing a ping before, we don't have a grid locator available. This could be a future feature for the TNC!
            if(arg.data[i]['DXGRID'] != ''){
                document.getElementById("pingDistance").innerHTML = arg.stations[i]['DXGRID']
            }
            */
            //document.getElementById("pingDB").innerHTML = arg.stations[i]['snr'];
            document.getElementById("dataModalPingDB").innerHTML = arg.stations[i]['snr'];
        }



        // now we update the received files list

        var row = document.createElement("tr");
        //https://stackoverflow.com/q/51421470

        //https://stackoverflow.com/a/847196
        timestampRaw = arg.data[i]['timestamp']
        var date = new Date(timestampRaw * 1000);
        var hours = date.getHours();
        var minutes = "0" + date.getMinutes();
        var seconds = "0" + date.getSeconds();
        var datetime = hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);

        var timestamp = document.createElement("td");
        var timestampText = document.createElement('span');
        timestampText.innerText = datetime;
        timestamp.appendChild(timestampText);

        var dxCall = document.createElement("td");
        var dxCallText = document.createElement('span');
        dxCallText.innerText = arg.data[i]['dxcallsign'];
        dxCall.appendChild(dxCallText);

        /*
                var dxGrid = document.createElement("td");
                var dxGridText = document.createElement('span');
                dxGridText.innerText = arg.data[i]['DXGRID']
                dxGrid.appendChild(dxGridText);
        */

        console.log(arg.data);
        
        var encoded_data = atob(arg.data[i]['data']);
        var splitted_data = encoded_data.split(split_char);
        console.log(splitted_data);

        var fileName = document.createElement("td");
        var fileNameText = document.createElement('span');
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
        fs.mkdir(receivedFilesFolder, {
            recursive: true
        }, function(err) {
            console.log(err);
        });


        // write file to data folder
        ////var base64String = arg.data[i]['data'][0]['d']
        // remove header from base64 String
        // https://www.codeblocq.com/2016/04/Convert-a-base64-string-to-a-file-in-Node/
        ////var base64Data = base64String.split(';base64,').pop()
        //write data to file
        var base64Data = splitted_data[4];
        var receivedFile = path.join(receivedFilesFolder, fileNameString);
        console.log(receivedFile);

        require("fs").writeFile(receivedFile, base64Data, 'binary', function(err) {
        //require("fs").writeFile(receivedFile, base64Data, 'base64', function(err) {
            console.log(err);
        });
    }

});

ipcRenderer.on('run-tnc-command', (event, arg) => {

    if (arg.command == 'save_my_call') {
        sock.saveMyCall(arg.callsign);
    }
    if (arg.command == 'save_my_grid') {
        sock.saveMyGrid(arg.grid);
    }
    if (arg.command == 'ping') {
        sock.sendPing(arg.dxcallsign);
    }

    if (arg.command == 'send_file') {
        sock.sendFile(arg.dxcallsign, arg.mode, arg.frames, arg.filename, arg.filetype, arg.data, arg.checksum);
    }
    if (arg.command == 'send_message') {
        sock.sendMessage(arg.dxcallsign, arg.mode, arg.frames, arg.data, arg.checksum, arg.uuid, arg.command);
    }
    if (arg.command == 'stop_transmission') {
        sock.stopTransmission();
    }
    if (arg.command == 'set_tx_audio_level') {
        sock.setTxAudioLevel(arg.tx_audio_level);
    }
    if (arg.command == 'record_audio') {
        sock.record_audio();
    }
    if (arg.command == 'send_test_frame') {
        sock.sendTestFrame();
    }

    if (arg.command == 'frequency') {
        sock.set_frequency(arg.frequency);
    }

    if (arg.command == 'mode') {
        sock.set_mode(arg.mode);
    }
    

});

// IPC ACTION FOR AUTO UPDATER
ipcRenderer.on('action-updater', (event, arg) => {

        if (arg.status == "download-progress"){
        
            var progressinfo = '(' 
                + Math.round(arg.progress.transferred/1024) 
                + 'kB /' 
                + Math.round(arg.progress.total/1024) 
                + 'kB)' 
                + ' @ ' 
                + Math.round(arg.progress.bytesPerSecond/1024) 
                + "kByte/s";; 
            document.getElementById("UpdateProgressInfo").innerHTML = progressinfo;            
            
            document.getElementById("UpdateProgressBar").setAttribute("aria-valuenow", arg.progress.percent)
            document.getElementById("UpdateProgressBar").setAttribute("style", "width:" + arg.progress.percent + "%;")
         
            
        }   

        if (arg.status == "checking-for-update"){
            
            //document.title = document.title + ' - v' + arg.version;
            updateTitle(config.myCall,config.tnc_host,config.tnc_port, " -v " + arg.version);
            document.getElementById("updater_status").innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'
            
            document.getElementById("updater_status").className = "btn btn-secondary btn-sm";
            document.getElementById("update_and_install").style.display = 'none';
        }   
        if (arg.status == "update-downloaded"){

            
            document.getElementById("update_and_install").removeAttribute("style");
            document.getElementById("updater_status").innerHTML = '<i class="bi bi-cloud-download ms-1 me-1" style="color: white;"></i>';
            document.getElementById("updater_status").className = "btn btn-success btn-sm";
            
            // HERE WE NEED TO RUN THIS SOMEHOW...
            //mainLog.info('quit application and install update');
            //autoUpdater.quitAndInstall();
            
        }   
        if (arg.status == "update-not-available"){

            document.getElementById("updater_status").innerHTML = '<i class="bi bi-check2-square ms-1 me-1" style="color: white;"></i>';
            document.getElementById("updater_status").className = "btn btn-success btn-sm";
            document.getElementById("update_and_install").style.display = 'none';
        }   
        if (arg.status == "update-available"){

            document.getElementById("updater_status").innerHTML = '<i class="bi bi-hourglass-split ms-1 me-1" style="color: white;"></i>';
            document.getElementById("updater_status").className = "btn btn-warning btn-sm";
            document.getElementById("update_and_install").style.display = 'none';

        }    
        
        if (arg.status == "error"){
 
            document.getElementById("updater_status").innerHTML = '<i class="bi bi-exclamation-square ms-1 me-1" style="color: white;"></i>';
            document.getElementById("updater_status").className = "btn btn-danger btn-sm";
            document.getElementById("update_and_install").style.display = 'none';            
        }          
        
        

});



// ----------- INFO MODAL ACTIONS -------------------------------

// CQ TRANSMITTING
ipcRenderer.on('action-show-cq-toast-transmitting', (event, data) => {
    var toastCQsending = document.getElementById('toastCQsending');
    var toast = bootstrap.Toast.getOrCreateInstance(toastCQsending); // Returns a Bootstrap toast instance
    toast.show();
});

// CQ RECEIVED
ipcRenderer.on('action-show-cq-toast-received', (event, data) => {
    var toastCQreceiving = document.getElementById('toastCQreceiving');
    var toast = bootstrap.Toast.getOrCreateInstance(toastCQreceiving); // Returns a Bootstrap toast instance
    toast.show();
});

// QRV TRANSMITTING
ipcRenderer.on('action-show-qrv-toast-transmitting', (event, data) => {
    var toastQRVtransmitting = document.getElementById('toastQRVtransmitting');
    var toast = bootstrap.Toast.getOrCreateInstance(toastQRVtransmitting); // Returns a Bootstrap toast instance
    toast.show();
});

// QRV RECEIVED
ipcRenderer.on('action-show-qrv-toast-received', (event, data) => {
    var toastQRVreceiving = document.getElementById('toastQRVreceiving');
    var toast = bootstrap.Toast.getOrCreateInstance(toastQRVreceiving); // Returns a Bootstrap toast instance
    toast.show();
});

// BEACON TRANSMITTING
ipcRenderer.on('action-show-beacon-toast-transmitting', (event, data) => {
});

// BEACON RECEIVED
ipcRenderer.on('action-show-beacon-toast-received', (event, data) => {
    var toastBEACONreceiving = document.getElementById('toastBEACONreceiving');
    var toast = bootstrap.Toast.getOrCreateInstance(toastBEACONreceiving); // Returns a Bootstrap toast instance
    toast.show();
});

// PING TRANSMITTING
ipcRenderer.on('action-show-ping-toast-transmitting', (event, data) => {
    var toastPINGsending = document.getElementById('toastPINGsending');
    var toast = bootstrap.Toast.getOrCreateInstance(toastPINGsending); // Returns a Bootstrap toast instance
    toast.show();
});

// PING RECEIVED
ipcRenderer.on('action-show-ping-toast-received', (event, data) => {
    var toastPINGreceiving = document.getElementById('toastPINGreceiving');
    var toast = bootstrap.Toast.getOrCreateInstance(toastPINGreceiving); // Returns a Bootstrap toast instance
    toast.show();
});

// PING RECEIVED ACK
ipcRenderer.on('action-show-ping-toast-received-ack', (event, data) => {
    var toastPINGreceivedACK = document.getElementById('toastPINGreceivedACK');
    var toast = bootstrap.Toast.getOrCreateInstance(toastPINGreceivedACK); // Returns a Bootstrap toast instance
    toast.show();
});

// DATA CHANNEL OPENING TOAST
ipcRenderer.on('action-show-arq-toast-datachannel-opening', (event, data) => {
    var toastDATACHANNELopening = document.getElementById('toastDATACHANNELopening');
    var toast = bootstrap.Toast.getOrCreateInstance(toastDATACHANNELopening); // Returns a Bootstrap toast instance
    toast.show();
});

// DATA CHANNEL WAITING TOAST
ipcRenderer.on('action-show-arq-toast-datachannel-waiting', (event, data) => {
    var toastDATACHANNELwaiting = document.getElementById('toastDATACHANNELwaiting');
    var toast = bootstrap.Toast.getOrCreateInstance(toastDATACHANNELwaiting); // Returns a Bootstrap toast instance
    toast.show();
});


// DATA CHANNEL OPEN TOAST
ipcRenderer.on('action-show-arq-toast-datachannel-open', (event, data) => {
    var toastDATACHANNELopen = document.getElementById('toastDATACHANNELopen');
    var toast = bootstrap.Toast.getOrCreateInstance(toastDATACHANNELopen); // Returns a Bootstrap toast instance
    toast.show();
});

// DATA CHANNEL RECEIVED OPENER TOAST
ipcRenderer.on('action-show-arq-toast-datachannel-received-opener', (event, data) => {
    var toastDATACHANNELreceivedopener = document.getElementById('toastDATACHANNELreceivedopener');
    var toast = bootstrap.Toast.getOrCreateInstance(toastDATACHANNELreceivedopener); // Returns a Bootstrap toast instance
    toast.show();
});

// ARQ TRANSMISSION FAILED
// TODO: use for both - transmitting and receiving --> we need to change the IDs
ipcRenderer.on('action-show-arq-toast-transmission-failed', (event, data) => {
    document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped bg-danger";
    var toast = bootstrap.Toast.getOrCreateInstance(toastARQtransmittingfailed); // Returns a Bootstrap toast instance
    toast.show();
});

// ARQ TRANSMISSION STOPPED
// TODO: RENAME ID -- WRONG
ipcRenderer.on('action-show-arq-toast-transmission-stopped', (event, data) => {
    var toastDATACHANNELreceivedopener = document.getElementById('toastTRANSMISSIONstopped');
    var toast = bootstrap.Toast.getOrCreateInstance(toastDATACHANNELreceivedopener); // Returns a Bootstrap toast instance
    toast.show();
});

// ARQ TRANSMISSION FAILED
// TODO: USE FOR TX AND RX
ipcRenderer.on('action-show-arq-toast-transmission-failed', (event, data) => {
    document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped bg-danger";

    var toastARQreceivingfailed = document.getElementById('toastARQreceivingfailed');
    var toast = bootstrap.Toast.getOrCreateInstance(toastARQreceivingfailed); // Returns a Bootstrap toast instance
    toast.show();
});

// ARQ TRANSMISSION TRANSMITTED
ipcRenderer.on('action-show-arq-toast-transmission-transmitted', (event, data) => {

    document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped bg-success";
    var toastARQtransmittingsuccess = document.getElementById('toastARQtransmittingsuccess');
    var toast = bootstrap.Toast.getOrCreateInstance(toastARQtransmittingsuccess); // Returns a Bootstrap toast instance
    toast.show();
});

// ARQ TRANSMISSION TRANSMITTING
ipcRenderer.on('action-show-arq-toast-transmission-transmitting', (event, data) => {

    //document.getElementById("toastARQtransmittingSNR").className = "progress-bar progress-bar-striped progress-bar-animated bg-primary";
    var toastARQtransmittingSNR = document.getElementById('toastARQtransmittingSNR');
    var toast = bootstrap.Toast.getOrCreateInstance(toastARQtransmittingSNR); // Returns a Bootstrap toast instance

    var irs_snr = data["data"][0].irs_snr;

    if(irs_snr <= 0){
        document.getElementById("toastARQtransmittingSNR").className = "toast align-items-center text-white bg-danger border-0";
        document.getElementById('toastARQtransmittingSNRValue').innerHTML = " low " + irs_snr;
        toast.show();

    } else if(irs_snr > 0 && irs_snr <= 5){
        document.getElementById("toastARQtransmittingSNR").className = "toast align-items-center text-white bg-warning border-0";
        document.getElementById('toastARQtransmittingSNRValue').innerHTML = " okay " + irs_snr;
        toast.show();

    } else if(irs_snr > 5  && irs_snr < 12.7){
        document.getElementById("toastARQtransmittingSNR").className = "toast align-items-center text-white bg-success border-0";
        document.getElementById('toastARQtransmittingSNRValue').innerHTML = " good " + irs_snr;
        toast.show();

    } else if(irs_snr >= 12.7){
        document.getElementById("toastARQtransmittingSNR").className = "toast align-items-center text-white bg-success border-0";
        document.getElementById('toastARQtransmittingSNRValue').innerHTML = " really good 12.7+";
        toast.show();

    } else {
        console.log("no snr info available")
        document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped progress-bar-animated bg-primary";
        var toastARQtransmitting = document.getElementById('toastARQtransmitting');
        var toast = bootstrap.Toast.getOrCreateInstance(toastARQtransmitting); // Returns a Bootstrap toast instance
        toast.show();

    }



});

// ARQ TRANSMISSION RECEIVED
ipcRenderer.on('action-show-arq-toast-transmission-received', (event, data) => {

    document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped bg-success";
    var toastARQreceivingsuccess = document.getElementById('toastARQreceivingsuccess');
    var toast = bootstrap.Toast.getOrCreateInstance(toastARQreceivingsuccess); // Returns a Bootstrap toast instance
    toast.show();
});

// ARQ TRANSMISSION RECEIVING
ipcRenderer.on('action-show-arq-toast-transmission-receiving', (event, data) => {

    document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped progress-bar-animated bg-primary";
    var toastARQsessionreceiving = document.getElementById('toastARQreceiving');
    var toast = bootstrap.Toast.getOrCreateInstance(toastARQsessionreceiving); // Returns a Bootstrap toast instance
    toast.show();
});

// ARQ SESSION CONNECTING
ipcRenderer.on('action-show-arq-toast-session-connecting', (event, data) => {

    var toastARQsessionconnecting = document.getElementById('toastARQsessionconnecting');
    var toast = bootstrap.Toast.getOrCreateInstance(toastARQsessionconnecting); // Returns a Bootstrap toast instance
    toast.show();
});

// ARQ SESSION CONNECTED
ipcRenderer.on('action-show-arq-toast-session-connected', (event, data) => {

    var toastARQsessionconnected = document.getElementById('toastARQsessionconnected');
    var toast = bootstrap.Toast.getOrCreateInstance(toastARQsessionconnected); // Returns a Bootstrap toast instance
    toast.show();
});

// ARQ SESSION CONNECTED
ipcRenderer.on('action-show-arq-toast-session-waiting', (event, data) => {

    var toastARQsessionwaiting = document.getElementById('toastARQsessionwaiting');
    var toast = bootstrap.Toast.getOrCreateInstance(toastARQsessionwaiting); // Returns a Bootstrap toast instance
    toast.show();
});


// ARQ SESSION CLOSE
ipcRenderer.on('action-show-arq-toast-session-close', (event, data) => {

    var toastARQsessionclose = document.getElementById('toastARQsessionclose');
    var toast = bootstrap.Toast.getOrCreateInstance(toastARQsessionclose); // Returns a Bootstrap toast instance
    toast.show();
});

// ARQ SESSION FAILED
ipcRenderer.on('action-show-arq-toast-session-failed', (event, data) => {

    var toastARQsessionfailed = document.getElementById('toastARQsessionfailed');
    var toast = bootstrap.Toast.getOrCreateInstance(toastARQsessionfailed); // Returns a Bootstrap toast instance
    toast.show();
});


// enable or disable a setting by given switch and element
function enable_setting(enable_switch, enable_object){
        if(document.getElementById(enable_switch).checked){
            config[enable_switch] = true
            document.getElementById(enable_object).removeAttribute("disabled","disabled");
        } else {
            config[enable_switch] = false
            document.getElementById(enable_object).setAttribute("disabled","disabled");
        }
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
}

// enable or disable a setting switch
function set_setting_switch(setting_switch, enable_object, state){
        document.getElementById(setting_switch).checked = state
        enable_setting(setting_switch, enable_object)
    }

setInterval(checkRigctld, 500)
function checkRigctld(){

    var rigctld_ip = document.getElementById("hamlib_rigctld_ip").value;
    var rigctld_port = document.getElementById("hamlib_rigctld_port").value;

    let Data = {
                ip: rigctld_ip,
                port: rigctld_port
            };
    ipcRenderer.send('request-check-rigctld', Data);
}

ipcRenderer.on('action-check-rigctld', (event, data) => {
        document.getElementById("hamlib_rigctld_status").value = data["state"];
});
function updateTitle(mycall = config.mycall , tnc = config.tnc_host, tncport = config.tnc_port, appender = ""){
    //Multiple consecutive  spaces get converted to a single space
    var title ="FreeDATA by DJ2LS - Call: " + mycall + " - TNC: " + tnc +":" + tncport + appender;
    if (title != document.title)
        document.title=title;
}

//Teomporarily disable a button with timeout
function pauseButton(btn, timems) {
    btn.disabled = true;
    var curText = btn.innerHTML;
    btn.innerHTML = "<span class=\"spinner-border spinner-border-sm\" role=\"status\" aria-hidden=\"true\">";
  setTimeout(()=>{
    btn.innerHTML=curText;
    btn.disabled = false;}, timems)
}