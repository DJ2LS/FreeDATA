const path = require('path');
const {ipcRenderer} = require('electron');
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

// split character used for appending addiotional data to files
const split_char = '\0;';


// https://stackoverflow.com/a/26227660
var appDataFolder = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + "/.config");
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, 'config.json');
const config = require(configPath);

// START INTERVALL COMMAND EXECUTION FOR STATES
//setInterval(sock.getRxBuffer, 1000);


// WINDOW LISTENER
window.addEventListener('DOMContentLoaded', () => {


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


    // DISABLE HAMLIB DIRECT AND RIGCTL ON WINDOWS
    if(os.platform()=='win32' || os.platform()=='win64'){

        document.getElementById("radio-control-switch1").style.disabled = true;
        //document.getElementById("radio-control-switch2").style.disabled = true;
    }

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
    document.getElementById("myCallSSID").value = ssid;
    document.getElementById("myGrid").value = config.mygrid;
    
    document.getElementById('hamlib_deviceid').value = config.deviceid;
    document.getElementById('hamlib_serialspeed').value = config.serialspeed_direct;
    document.getElementById('hamlib_ptt_protocol').value = config.pttprotocol_direct; 

    document.getElementById("hamlib_rigctld_ip").value = config.rigctld_ip;
    document.getElementById("hamlib_rigctld_port").value = config.rigctld_port;
    
    //document.getElementById("hamlib_deviceid_rigctl").value = config.deviceid_rigctl;
    //document.getElementById("hamlib_serialspeed_rigctl").value = config.serialspeed_rigctl;
    //document.getElementById("hamlib_ptt_protocol_rigctl").value = config.pttprotocol_rigctl; 
    
    document.getElementById('hamlib_serialspeed_advanced').value = config.serialspeed_direct;
    document.getElementById('hamlib_ptt_protocol_advanced').value = config.pttprotocol_direct;     
    document.getElementById('hamlib_databits_advanced').value = config.data_bits_direct;
    document.getElementById('hamlib_stopbits_advanced').value = config.stop_bits_direct;
    document.getElementById('hamlib_handshake_advanced').value = config.handshake_direct;

    document.getElementById("beaconInterval").value = config.beacon_interval;
 
    document.getElementById("scatterSwitch").value = config.enable_scatter;
    document.getElementById("fftSwitch").value = config.enable_fft;
    document.getElementById("500HzModeSwitch").value = config.low_bandwith_mode; 
    document.getElementById("fskModeSwitch").value = config.enable_fsk; 
       
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

    if(config.low_bandwith_mode == 'True'){
        document.getElementById("500HzModeSwitch").checked = true;
    } else {
        document.getElementById("500HzModeSwitch").checked = false;
    }  
          
    if(config.enable_fsk == 'True'){
        document.getElementById("fskModeSwitch").checked = true;
    } else {
        document.getElementById("fskModeSwitch").checked = false;
    }  
    // theme selector

    if(config.theme != 'default'){

        var theme_path = "../node_modules/bootswatch/dist/"+ config.theme +"/bootstrap.min.css";
        document.getElementById("theme_selector").value = config.theme;
        document.getElementById("bootstrap_theme").href = theme_path;
    } else {    
        var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
        document.getElementById("theme_selector").value = 'default';
        document.getElementById("bootstrap_theme").href = theme_path;
    }
    

    // Update channel selector
    document.getElementById("update_channel_selector").value = config.update_channel;

    // Update tuning range fmin fmax
    document.getElementById("tuning_range_fmin").value = config.tuning_range_fmin;
    document.getElementById("tuning_range_fmax").value = config.tuning_range_fmax;
    
    
    // Update TX Audio Level
    document.getElementById("audioLevelTXvalue").innerHTML = config.tx_audio_level;
    document.getElementById("audioLevelTX").value = config.tx_audio_level;    
    
    
    if (config.spectrum == 'waterfall') {
        document.getElementById("waterfall-scatter-switch1").checked = true;
        document.getElementById("waterfall-scatter-switch2").checked = false;
        document.getElementById("scatter").style.visibility = 'hidden';
        document.getElementById("waterfall").style.visibility = 'visible';
        document.getElementById("waterfall").style.height = '100%';
    } else {

        document.getElementById("waterfall-scatter-switch1").checked = false;
        document.getElementById("waterfall-scatter-switch2").checked = true;
        document.getElementById("scatter").style.visibility = 'visible';
        document.getElementById("waterfall").style.visibility = 'hidden';
        document.getElementById("waterfall").style.height = '0px';
    }

    // radio control element
    if (config.radiocontrol == 'direct') {

        document.getElementById("radio-control-switch0").checked = false;
        document.getElementById("radio-control-switch1").checked = true;
        //document.getElementById("radio-control-switch2").checked = false;
        document.getElementById("radio-control-switch3").checked = false;

        //document.getElementById("radio-control-rigctl").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.visibility = 'hidden';        
        //document.getElementById("radio-control-rigctl").style.display = 'none';
        document.getElementById("radio-control-rigctld").style.display = 'none';  

        document.getElementById("radio-control-direct").style.display = 'block';
        document.getElementById("radio-control-direct").style.visibility = 'visible';
        document.getElementById("radio-control-direct").style.height = '100%'; 

    /*
    } else if (config.radiocontrol == 'rigctl') {

        document.getElementById("radio-control-switch0").checked = false;  
        document.getElementById("radio-control-switch1").checked = false;
        //document.getElementById("radio-control-switch2").checked = true;
        document.getElementById("radio-control-switch3").checked = false;
        
        document.getElementById("radio-control-direct").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.visibility = 'hidden';        
        document.getElementById("radio-control-direct").style.display = 'none';
        document.getElementById("radio-control-rigctld").style.display = 'none';  

        document.getElementById("radio-control-rigctl").style.display = 'block';                
        document.getElementById("radio-control-rigctl").style.visibility = 'visible';
        document.getElementById("radio-control-rigctl").style.height = '100%';       
*/
    } else if (config.radiocontrol == 'rigctld') {

        document.getElementById("radio-control-switch0").checked = false;
        document.getElementById("radio-control-switch1").checked = false;
        //document.getElementById("radio-control-switch2").checked = false;
        document.getElementById("radio-control-switch3").checked = true;

        document.getElementById("radio-control-direct").style.visibility = 'hidden';
        //document.getElementById("radio-control-rigctl").style.visibility = 'hidden';        
        document.getElementById("radio-control-direct").style.display = 'none';
        //document.getElementById("radio-control-rigctl").style.display = 'none';  

        document.getElementById("radio-control-rigctld").style.display = 'block';                
        document.getElementById("radio-control-rigctld").style.visibility = 'visible';
        document.getElementById("radio-control-rigctld").style.height = '100%';
        
    } else {
    
        document.getElementById("radio-control-switch0").checked = true;
        document.getElementById("radio-control-switch1").checked = false;
        //document.getElementById("radio-control-switch2").checked = false;
        document.getElementById("radio-control-switch3").checked = false;

        //document.getElementById("radio-control-rigctl").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.visibility = 'hidden';        
        //document.getElementById("radio-control-rigctl").style.display = 'none';
        document.getElementById("radio-control-rigctld").style.display = 'none';  

        document.getElementById("radio-control-direct").style.display = 'block';
        document.getElementById("radio-control-direct").style.visibility = 'visible';
        document.getElementById("radio-control-direct").style.height = '100%';

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
            spectrumPercent: 0
        });



    // on click radio control toggle view
    // disabled
    document.getElementById("radio-control-switch0").addEventListener("click", () => {
        //document.getElementById("radio-control-rigctl").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.visibility = 'hidden';        
        //document.getElementById("radio-control-rigctl").style.display = 'none';
        document.getElementById("radio-control-rigctld").style.display = 'none';  

        document.getElementById("radio-control-direct").style.display = 'block';
        document.getElementById("radio-control-direct").style.visibility = 'visible';
        document.getElementById("radio-control-direct").style.height = '100%';
        config.radiocontrol = 'disabled'
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
    
    
    // direct
    document.getElementById("radio-control-switch1").addEventListener("click", () => {
        //document.getElementById("radio-control-rigctl").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.visibility = 'hidden';        
        //document.getElementById("radio-control-rigctl").style.display = 'none';
        document.getElementById("radio-control-rigctld").style.display = 'none';  

        document.getElementById("radio-control-direct").style.display = 'block';
        document.getElementById("radio-control-direct").style.visibility = 'visible';
        document.getElementById("radio-control-direct").style.height = '100%';
        config.radiocontrol = 'direct';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

    /*
    // rigctl
    document.getElementById("radio-control-switch2").addEventListener("click", () => {
        document.getElementById("radio-control-direct").style.visibility = 'hidden';
        document.getElementById("radio-control-rigctld").style.visibility = 'hidden';        
        document.getElementById("radio-control-direct").style.display = 'none';
        document.getElementById("radio-control-rigctld").style.display = 'none';  

        //document.getElementById("radio-control-rigctl").style.display = 'block';                
        //document.getElementById("radio-control-rigctl").style.visibility = 'visible';
        //document.getElementById("radio-control-rigctl").style.height = '100%';
        config.radiocontrol = 'rigctl';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
    */
    // rigctld
    document.getElementById("radio-control-switch3").addEventListener("click", () => {
        document.getElementById("radio-control-direct").style.visibility = 'hidden';
        //document.getElementById("radio-control-rigctl").style.visibility = 'hidden';        
        document.getElementById("radio-control-direct").style.display = 'none';
        //document.getElementById("radio-control-rigctl").style.display = 'none';  

        document.getElementById("radio-control-rigctld").style.display = 'block';                
        document.getElementById("radio-control-rigctld").style.visibility = 'visible';
        document.getElementById("radio-control-rigctld").style.height = '100%';
        config.radiocontrol = 'rigctld';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });    


    // on click waterfall scatter toggle view
    // waterfall
    document.getElementById("waterfall-scatter-switch1").addEventListener("click", () => {
        document.getElementById("scatter").style.visibility = 'hidden';
        document.getElementById("waterfall").style.visibility = 'visible';
        document.getElementById("waterfall").style.height = '100%';
        config.spectrum = 'waterfall';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
    // scatter
    document.getElementById("waterfall-scatter-switch2").addEventListener("click", () => {
        document.getElementById("scatter").style.visibility = 'visible';
        document.getElementById("waterfall").style.visibility = 'hidden';
        document.getElementById("waterfall").style.height = '0px';
        config.spectrum = 'scatter';
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

    // on change port and host
    document.getElementById("tnc_adress").addEventListener("change", () => {
        console.log(document.getElementById("tnc_adress").value);
        config.tnc_host = document.getElementById("tnc_adress").value;
        config.daemon_host = document.getElementById("tnc_adress").value;
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
        
    
    // on change tnc port
    document.getElementById("tnc_port").addEventListener("change", () => {
        config.tnc_port = document.getElementById("tnc_port").value;
        config.daemon_port = parseInt(document.getElementById("tnc_port").value) + 1;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    });
    
    // on change audio TX Level
    document.getElementById("audioLevelTX").addEventListener("change", () => {
        var tx_audio_level = document.getElementById("audioLevelTX").value;
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
    document.getElementById("saveMyCall").addEventListener("click", () => {
        callsign = document.getElementById("myCall").value;
        ssid = document.getElementById("myCallSSID").value;
        callsign_ssid = callsign.toUpperCase() + '-' + ssid;
        config.mycall = callsign_ssid;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        daemon.saveMyCall(callsign_ssid);
    });

    // saveMyGrid button clicked
    document.getElementById("saveMyGrid").addEventListener("click", () => {
        grid = document.getElementById("myGrid").value;
        config.mygrid = grid;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        daemon.saveMyGrid(grid);

    });
      

    // startPing button clicked
    document.getElementById("sendPing").addEventListener("click", () => {
        var dxcallsign = document.getElementById("dxCall").value;
        dxcallsign = dxcallsign.toUpperCase();
        sock.sendPing(dxcallsign);
    });

    // dataModalstartPing button clicked
    document.getElementById("dataModalSendPing").addEventListener("click", () => {
        var dxcallsign = document.getElementById("dataModalDxCall").value;
        dxcallsign = dxcallsign.toUpperCase();
        sock.sendPing(dxcallsign);
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
            config.low_bandwith_mode = "True";       
        } else {
            config.low_bandwith_mode = "False";       
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
        document.getElementById("bootstrap_theme").href = theme_path
        
        config.theme = theme;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    });
    
    // Update channel selector clicked
    document.getElementById("update_channel_selector").addEventListener("click", () => {
        config.update_channel = document.getElementById("update_channel_selector").value;
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

    // startTNC button clicked
    document.getElementById("startTNC").addEventListener("click", () => {

        var tuning_range_fmin = document.getElementById("tuning_range_fmin").value;
        var tuning_range_fmax = document.getElementById("tuning_range_fmax").value;
                
        var rigctld_ip = document.getElementById("hamlib_rigctld_ip").value;
        var rigctld_port = document.getElementById("hamlib_rigctld_port").value;

        var deviceid = document.getElementById("hamlib_deviceid").value;
        var deviceport = document.getElementById("hamlib_deviceport").value;
        var serialspeed = document.getElementById("hamlib_serialspeed").value;
        var pttprotocol = document.getElementById("hamlib_ptt_protocol").value;

        var mycall = document.getElementById("myCall").value;
        var ssid = document.getElementById("myCallSSID").value;
        callsign_ssid = mycall.toUpperCase() + '-' + ssid;
        
        var mygrid = document.getElementById("myGrid").value;
        
        var rx_audio = document.getElementById("audio_input_selectbox").value;
        var tx_audio = document.getElementById("audio_output_selectbox").value;
        
        var pttport = document.getElementById("hamlib_ptt_port_advanced").value;
        var data_bits = document.getElementById('hamlib_databits_advanced').value;
        var stop_bits = document.getElementById('hamlib_stopbits_advanced').value;
        var handshake = document.getElementById('hamlib_handshake_advanced').value;
        
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
            var low_bandwith_mode = "True";
        } else {
            var low_bandwith_mode = "False";
        }
        
        if (document.getElementById("fskModeSwitch").checked == true){
            var enable_fsk = "True";
        } else {
            var enable_fsk = "False";
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

        /*
        // overriding settings for rigctl / direct
        if (document.getElementById("radio-control-switch2").checked){
            var radiocontrol = 'rigctl';
            var deviceid = document.getElementById("hamlib_deviceid_rigctl").value;
            var deviceport = document.getElementById("hamlib_deviceport_rigctl").value;
            var serialspeed = document.getElementById("hamlib_serialspeed_rigctl").value;
            var pttprotocol = document.getElementById("hamlib_ptt_protocol_rigctl").value;
        
        } else 
        */
        if (document.getElementById("radio-control-switch3").checked) {
            var radiocontrol = 'rigctld';

        } else if (document.getElementById("radio-control-switch1").checked) {
            var radiocontrol = 'direct';
                        
        } else {
            var radiocontrol = 'disabled';
        }     

        var tx_audio_level = document.getElementById("audioLevelTX").value;

        
        config.radiocontrol = radiocontrol;
        config.mycall = callsign_ssid;
        config.mygrid = mygrid;                
        config.deviceid = deviceid;
        config.deviceport = deviceport;
        config.serialspeed_direct = serialspeed;
        config.pttprotocol_direct = pttprotocol;
        config.pttport = pttport;
        config.data_bits_direct = data_bits;
        config.stop_bits_direct = stop_bits;
        config.handshake_direct = handshake;
        //config.deviceid_rigctl = deviceid_rigctl;
        //config.serialspeed_rigctl = serialspeed_rigctl;
        //config.pttprotocol_rigctl = pttprotocol_rigctl;
        config.rigctld_port = rigctld_port;
        config.rigctld_ip = rigctld_ip;
        //config.deviceport_rigctl = deviceport_rigctl;
        config.enable_scatter = enable_scatter;
        config.enable_fft = enable_fft;
        config.enable_fsk = enable_fsk;
        config.low_bandwith_mode = low_bandwith_mode;
        config.tx_audio_level = tx_audio_level;
        
 
        
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


        daemon.startTNC(callsign_ssid, mygrid, rx_audio, tx_audio, radiocontrol, deviceid, deviceport, pttprotocol, pttport, serialspeed, data_bits, stop_bits, handshake, rigctld_ip, rigctld_port, enable_fft, enable_scatter, low_bandwith_mode, tuning_range_fmin, tuning_range_fmax, enable_fsk, tx_audio_level);
        
        
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
        

        var data_bits = document.getElementById("hamlib_databits_advanced").value;
        var stop_bits = document.getElementById("hamlib_stopbits_advanced").value;
        var handshake = document.getElementById("hamlib_handshake_advanced").value;
        var pttport = document.getElementById("hamlib_ptt_port_advanced").value;

        var rigctld_ip = document.getElementById("hamlib_rigctld_ip").value;
        var rigctld_port = document.getElementById("hamlib_rigctld_port").value;

        var deviceid = document.getElementById("hamlib_deviceid").value;
        var deviceport = document.getElementById("hamlib_deviceport").value;
        var serialspeed = document.getElementById("hamlib_serialspeed").value;
        var pttprotocol = document.getElementById("hamlib_ptt_protocol").value;


        /*
        // overriding settings for rigctl / direct
        if (document.getElementById("radio-control-switch2").checked){
            var radiocontrol = 'rigctl';
            var deviceid = document.getElementById("hamlib_deviceid_rigctl").value;
            var deviceport = document.getElementById("hamlib_deviceport_rigctl").value;
            var serialspeed = document.getElementById("hamlib_serialspeed_rigctl").value;
            var pttprotocol = document.getElementById("hamlib_ptt_protocol_rigctl").value;
        
        } else */
        if (document.getElementById("radio-control-switch3").checked) {
            var radiocontrol = 'rigctld';

        } else if (document.getElementById("radio-control-switch1").checked) {
            var radiocontrol = 'direct';
        } else {
            var radiocontrol = 'disabled';
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


    // TOE TIME OF EXECUTION --> How many time needs a command to be executed until data arrives
    // deactivated this feature, beacuse its useless at this time. maybe it is getting more interesting, if we are working via network
    // but for this we need to find a nice place for this on the screen
    /*
    if (typeof(arg.toe) == 'undefined') {
        var toe = 0
    } else {
        var toe = arg.toe
    }
    document.getElementById("toe").innerHTML = toe + ' ms'
    */
    
    // DATA STATE
    global.rxBufferLengthTnc = arg.rx_buffer_length

    // SCATTER DIAGRAM PLOTTING
    //global.myChart.destroy();

    //console.log(arg.scatter.length)

        const config = {
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




    var data = arg.scatter
    var newdata = {
        datasets: [{
            //label: 'constellation diagram',
            data: data,
            options: config,
            backgroundColor: 'rgb(255, 99, 132)'
        }],
    };

    if (typeof(arg.scatter) == 'undefined') {
        var scatterSize = 0;
    } else {
        var scatterSize = arg.scatter.length;
    }
    if (global.data != newdata && scatterSize > 0) {
        try {
            global.myChart.destroy();
        } catch (e) {
            // myChart not yet created
            console.log(e);
        }

        global.data = newdata;


        var ctx = document.getElementById('scatter').getContext('2d');
        global.myChart = new Chart(ctx, {
            type: 'scatter',
            data: global.data,
            options: config
        });
    }

    // PTT STATE
    if (arg.ptt_state == 'True') {
        document.getElementById("ptt_state").className = "btn btn-sm btn-danger";
    } else if (arg.ptt_state == 'False') {
        document.getElementById("ptt_state").className = "btn btn-sm btn-success";
    } else {
        document.getElementById("ptt_state").className = "btn btn-sm btn-secondary";
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
    // RMS
    document.getElementById("rms_level").setAttribute("aria-valuenow", arg.rms_level);
    document.getElementById("rms_level").setAttribute("style", "width:" + arg.rms_level + "%;");


    // SET FREQUENCY
    document.getElementById("frequency").innerHTML = arg.frequency;

    // SET MODE
    document.getElementById("mode").innerHTML = arg.mode;

    // SET BANDWITH
    document.getElementById("bandwith").innerHTML = arg.bandwith;

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
    document.getElementById("transmission_progress").setAttribute("aria-valuenow", arg.arq_transmission_percent);
    document.getElementById("transmission_progress").setAttribute("style", "width:" + arg.arq_transmission_percent + "%;");

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
        if (arg.stations[i]['dxcallsign'] == document.getElementById("dxCall").value) {
            var dxGrid = arg.stations[i]['dxgrid'];
            var myGrid = document.getElementById("myGrid").value;
            try {
                var dist = parseInt(distance(myGrid, dxGrid)) + ' km';
                document.getElementById("pingDistance").innerHTML = dist;
                document.getElementById("dataModalPingDistance").innerHTML = dist;
            } catch {
                document.getElementById("pingDistance").innerHTML = '---';
                document.getElementById("dataModalPingDistance").innerHTML = '---';
            }
            document.getElementById("pingDB").innerHTML = arg.stations[i]['snr'];
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
    
    
    // DISPLAY INFO TOASTS
        if (typeof(arg.info) == 'undefined') {
        var infoLength = 0;
    } else {
        var infoLength = arg.info.length;
    }

    for (i = 0; i < infoLength; i++) {
        
        // SENDING CQ TOAST
        if (arg.info[i] == "CQ;SENDING"){
            var toastCQsending = document.getElementById('toastCQsending');
            var toast = bootstrap.Toast.getOrCreateInstance(toastCQsending); // Returns a Bootstrap toast instance
            toast.show();
        }
    
        // RECEIVING CQ TOAST
        if (arg.info[i] == "CQ;RECEIVING"){
            var toastCQreceiving = document.getElementById('toastCQreceiving');
            var toast = bootstrap.Toast.getOrCreateInstance(toastCQreceiving); // Returns a Bootstrap toast instance
            toast.show();
        }

        // RECEIVING BEACON TOAST
        if (arg.info[i] == "BEACON;RECEIVING"){
            var toastBEACONreceiving = document.getElementById('toastBEACONreceiving');
            var toast = bootstrap.Toast.getOrCreateInstance(toastBEACONreceiving); // Returns a Bootstrap toast instance
            toast.show();
        }
        
                
        // SENDING PING TOAST
        if (arg.info[i] == "PING;SENDING"){
            var toastPINGsending = document.getElementById('toastPINGsending');
            var toast = bootstrap.Toast.getOrCreateInstance(toastPINGsending); // Returns a Bootstrap toast instance
            toast.show();
        }
        // RECEIVING PING TOAST
        if (arg.info[i] == "PING;RECEIVING"){
            var toastPINGreceiving = document.getElementById('toastPINGreceiving');
            var toast = bootstrap.Toast.getOrCreateInstance(toastPINGreceiving); // Returns a Bootstrap toast instance
            toast.show();
        }    
        // RECEIVING PING ACK TOAST
        if (arg.info[i] == "PING;RECEIVEDACK"){
            var toastPINGreceivedACK = document.getElementById('toastPINGreceivedACK');
            var toast = bootstrap.Toast.getOrCreateInstance(toastPINGreceivedACK); // Returns a Bootstrap toast instance
            toast.show();
        }
        // DATACHANNEL OPENING TOAST
        if (arg.info[i] == "DATACHANNEL;OPENING"){
            var toastDATACHANNELopening = document.getElementById('toastDATACHANNELopening');
            var toast = bootstrap.Toast.getOrCreateInstance(toastDATACHANNELopening); // Returns a Bootstrap toast instance
            toast.show();
        }
        
        // DATACHANNEL OPEN TOAST
        if (arg.info[i] == "DATACHANNEL;OPEN"){
            var toastDATACHANNELopen = document.getElementById('toastDATACHANNELopen');
            var toast = bootstrap.Toast.getOrCreateInstance(toastDATACHANNELopen); // Returns a Bootstrap toast instance
            toast.show();
        }
         // DATACHANNEL RECEIVEDOPENER TOAST
        if (arg.info[i] == "DATACHANNEL;RECEIVEDOPENER"){
            var toastDATACHANNELreceivedopener = document.getElementById('toastDATACHANNELreceivedopener');
            var toast = bootstrap.Toast.getOrCreateInstance(toastDATACHANNELreceivedopener); // Returns a Bootstrap toast instance
            toast.show();
        }  
         // TRANSMISSION STOPPED
        if (arg.info[i] == "TRANSMISSION;STOPPED"){
            var toastDATACHANNELreceivedopener = document.getElementById('toastTRANSMISSIONstopped');
            var toast = bootstrap.Toast.getOrCreateInstance(toastDATACHANNELreceivedopener); // Returns a Bootstrap toast instance
            toast.show();
        }         
                                        
         // DATACHANNEL FAILED TOAST
        if (arg.info[i] == "DATACHANNEL;FAILED"){
            var toastDATACHANNELfailed = document.getElementById('toastDATACHANNELfailed');
            var toast = bootstrap.Toast.getOrCreateInstance(toastDATACHANNELfailed); // Returns a Bootstrap toast instance
            toast.show();
        }  
         // ARQ RECEIVING TOAST
        if (arg.info[i] == "ARQ;RECEIVING"){
        
            document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped progress-bar-animated bg-primary";
        
            var toastARQreceiving = document.getElementById('toastARQreceiving');
            var toast = bootstrap.Toast.getOrCreateInstance(toastARQreceiving); // Returns a Bootstrap toast instance
            toast.show();
        }        
         // ARQ RECEIVING SUCCESS TOAST
        console.log(arg.info[i])
        if (arg.info[i] == "ARQ;RECEIVING;SUCCESS"){
            
            document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped bg-success";
            
            var toastARQreceivingsuccess = document.getElementById('toastARQreceivingsuccess');
            var toast = bootstrap.Toast.getOrCreateInstance(toastARQreceivingsuccess); // Returns a Bootstrap toast instance
            toast.show();
        }
         // ARQ RECEIVING FAILED TOAST
        if (arg.info[i] == "ARQ;RECEIVING;FAILED"){
        
            document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped bg-danger";
        
            var toastARQreceivingfailed = document.getElementById('toastARQreceivingfailed');
            var toast = bootstrap.Toast.getOrCreateInstance(toastARQreceivingfailed); // Returns a Bootstrap toast instance
            toast.show();
        }        
         // ARQ TRANSMITTING TOAST
        if (arg.info[i] == "ARQ;TRANSMITTING"){
        
            document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped progress-bar-animated bg-primary";
        
            var toastARQtransmitting = document.getElementById('toastARQtransmitting');
            var toast = bootstrap.Toast.getOrCreateInstance(toastARQtransmitting); // Returns a Bootstrap toast instance
            toast.show();
        }        
         // ARQ TRANSMITTING SUCCESS TOAST
        if (arg.info[i] == "ARQ;TRANSMITTING;SUCCESS"){
        
            document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped bg-success";
        
            var toastARQtransmittingsuccess = document.getElementById('toastARQtransmittingsuccess');
            var toast = bootstrap.Toast.getOrCreateInstance(toastARQtransmittingsuccess); // Returns a Bootstrap toast instance
            toast.show();
        }               
         // ARQ TRANSMITTING FAILED TOAST
        if (arg.info[i] == "ARQ;TRANSMITTING;FAILED"){
        
            document.getElementById("transmission_progress").className = "progress-bar progress-bar-striped bg-danger";
        
            var toast = bootstrap.Toast.getOrCreateInstance(toastARQtransmittingfailed); // Returns a Bootstrap toast instance
            toast.show();
        }           
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
                if(config.deviceport == option.value){
                    option.setAttribute('selected', true);
                }
                document.getElementById("hamlib_deviceport").add(option);
   
            }
        }

        // advanced settings
        if (document.getElementById("hamlib_deviceport_advanced").length != arg.serial_devices.length) {
            document.getElementById("hamlib_deviceport_advanced").innerHTML = "";
            for (i = 0; i < arg.serial_devices.length; i++) {
                var option = document.createElement("option");
                option.text = arg.serial_devices[i]['description'];
                option.value = arg.serial_devices[i]['port'];
                // set device from config if available
                if(config.deviceport == option.value){
                    option.setAttribute('selected', true);
                }
                document.getElementById("hamlib_deviceport_advanced").add(option);
            }
        }
        
        /*
        // rigctl settings
        if (document.getElementById("hamlib_deviceport_rigctl").length != arg.serial_devices.length) {
            document.getElementById("hamlib_deviceport_rigctl").innerHTML = "";
            for (i = 0; i < arg.serial_devices.length; i++) {
                var option = document.createElement("option");
                option.text = arg.serial_devices[i]['description'];
                option.value = arg.serial_devices[i]['port'];
                // set device from config if available
                if(config.deviceport == option.value){
                    option.setAttribute('selected', true);
                }
                document.getElementById("hamlib_deviceport_rigctl").add(option);
            }
        }
        */
        
               
    }
    
    if (arg.tnc_running_state == "stopped") {
        if (document.getElementById("hamlib_ptt_port_advanced").length != arg.serial_devices.length) {
            document.getElementById("hamlib_ptt_port_advanced").innerHTML = "";
            for (i = 0; i < arg.serial_devices.length; i++) {
                var option = document.createElement("option");
                option.text = arg.serial_devices[i]['description'];
                option.value = arg.serial_devices[i]['port'];
                // set device from config if available
                if(config.pttport == option.value){
                    option.setAttribute('selected', true);
                }
                document.getElementById("hamlib_ptt_port_advanced").add(option);
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
        document.getElementById('hamlib_deviceid').disabled = true;
        document.getElementById('hamlib_deviceport').disabled = true;
        document.getElementById('advancedHamlibSettingsButton').disabled = true;
        document.getElementById('testHamlib').disabled = true;
        document.getElementById('hamlib_ptt_protocol').disabled = true;
        document.getElementById('audio_input_selectbox').disabled = true;
        document.getElementById('audio_output_selectbox').disabled = true;
        //document.getElementById('stopTNC').disabled = false;
        document.getElementById('startTNC').disabled = true;
        document.getElementById('dxCall').disabled = false;
        document.getElementById("hamlib_serialspeed").disabled = true;
        document.getElementById("openDataModule").disabled = false;

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
        document.getElementById('hamlib_deviceid').disabled = false;
        document.getElementById('hamlib_deviceport').disabled = false;
        document.getElementById('advancedHamlibSettingsButton').disabled = false;
        document.getElementById('testHamlib').disabled = false;
        document.getElementById('hamlib_ptt_protocol').disabled = false;
        document.getElementById('audio_input_selectbox').disabled = false;
        document.getElementById('audio_output_selectbox').disabled = false;
        //document.getElementById('stopTNC').disabled = true;
        document.getElementById('startTNC').disabled = false;
        document.getElementById('dxCall').disabled = true;
        document.getElementById("hamlib_serialspeed").disabled = false;
        document.getElementById("openDataModule").disabled = true;
        
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
        if (arg.data[i]['dxcallsign'] == document.getElementById("dxCall").value) {
            /*
            // if we are sending data without doing a ping before, we don't have a grid locator available. This could be a future feature for the TNC!
            if(arg.data[i]['DXGRID'] != ''){
                document.getElementById("pingDistance").innerHTML = arg.stations[i]['DXGRID']
            }
            */
            document.getElementById("pingDB").innerHTML = arg.stations[i]['snr'];

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
    if (arg.command == 'send_test_frame') {
        sock.sendTestFrame();
    }    
                  
    

});

// IPC ACTION FOR AUTO UPDATER
ipcRenderer.on('action-updater', (event, arg) => {

        if (arg.status == "download-progress"){
        
            bootstrap.Toast.getOrCreateInstance(document.getElementById('toastUpdateAvailable')).hide(); // close our update available notification
            
            
            var progressinfo = '(' + Math.round(arg.progress.transferred/1024) + 'kB /' + Math.round(arg.progress.total/1024) + 'kB)'; 
            document.getElementById("toastUpdateProgressInfo").innerHTML = progressinfo;            
            document.getElementById("toastUpdateProgressSpeed").innerHTML = Math.round(arg.progress.bytesPerSecond/1024) + "kByte/s";
            
            document.getElementById("toastUpdateProgressBar").setAttribute("aria-valuenow", arg.progress.percent)
            document.getElementById("toastUpdateProgressBar").setAttribute("style", "width:" + arg.progress.percent + "%;")
         
            var toast = bootstrap.Toast.getOrCreateInstance(
                document.getElementById('toastUpdateProgress')             
            ); // Returns a Bootstrap toast instance
            

            let showing = document.getElementById("toastUpdateProgress").getAttribute("class").includes("showing");
            if(!showing){
                toast.show();                
            }
        }   

        if (arg.status == "checking-for-update"){
            var toast = bootstrap.Toast.getOrCreateInstance(
                document.getElementById('toastUpdateChecking')     
            ); // Returns a Bootstrap toast instance
            toast.show();
            document.title = "FreeDATA by DJ2LS" + ' - v' + arg.version;
        }   
        if (arg.status == "update-downloaded"){
            var toast = bootstrap.Toast.getOrCreateInstance(
                document.getElementById('toastUpdateDownloaded')            
            ); // Returns a Bootstrap toast instance
            toast.show();
        }   
        if (arg.status == "update-not-available"){
            bootstrap.Toast.getOrCreateInstance(document.getElementById('toastUpdateChecking')).hide();
            var toast = bootstrap.Toast.getOrCreateInstance(
                document.getElementById('toastUpdateNotAvailable')            
            ); // Returns a Bootstrap toast instance
            toast.show();
        }   
        if (arg.status == "update-available"){
        
            bootstrap.Toast.getOrCreateInstance(document.getElementById('toastUpdateChecking')).hide();
            var toast = bootstrap.Toast.getOrCreateInstance(
                document.getElementById('toastUpdateAvailable')            
            ); // Returns a Bootstrap toast instance
            toast.show();
        }    
        
        if (arg.status == "error"){
            var toast = bootstrap.Toast.getOrCreateInstance(
                document.getElementById('toastUpdateNotChecking')            
            ); // Returns a Bootstrap toast instance
            toast.show();

            
        }          
        
        

});
