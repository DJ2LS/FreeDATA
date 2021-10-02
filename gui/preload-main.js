const path = require('path')
const {
    ipcRenderer
} = require('electron')
const sock = require('./sock.js');
const daemon = require('./daemon.js');
const fs = require('fs');
const {
    locatorToLatLng,
    distance,
    bearingDistance,
    latLngToLocator
} = require('qth-locator');

// https://stackoverflow.com/a/26227660
var appDataFolder = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + "/.config")
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, 'config.json')
const config = require(configPath);

// START INTERVALL COMMAND EXECUTION FOR STATES
setInterval(daemon.getDaemonState, 1000)
setInterval(sock.getTncState, 150)
setInterval(sock.getRxBuffer, 1000)

// UPDATE FFT DEMO
/*
updateFFT = function(fft) {
    var fft = Array.from({
        length: 2048
    }, () => Math.floor(Math.random() * 10));
    spectrum.addData(fft);
    console.log(fft)
}

setInterval(updateFFT, 250)
*/

// WINDOW LISTENER
window.addEventListener('DOMContentLoaded', () => {
    // LOAD SETTINGS
    document.getElementById("tnc_adress").value = config.tnc_host
    document.getElementById("tnc_port").value = config.tnc_port
    document.getElementById("myCall").value = config.mycall
    document.getElementById("myGrid").value = config.mygrid
    document.getElementById('hamlib_deviceid').value = config.deviceid
    document.getElementById('hamlib_deviceport').value = config.deviceport
    document.getElementById('hamlib_serialspeed').value = config.serialspeed
    document.getElementById('hamlib_ptt_protocol').value = config.pttprotocol
    document.getElementById('hamlib_ptt_port').value = config.pttport


    if (config.spectrum == 'waterfall') {
        document.getElementById("waterfall-scatter-switch1").checked = true
        document.getElementById("waterfall-scatter-switch2").checked = false
        document.getElementById("scatter").style.visibility = 'hidden';
        document.getElementById("waterfall").style.visibility = 'visible';
        document.getElementById("waterfall").style.height = '100%';
    } else {

        document.getElementById("waterfall-scatter-switch1").checked = false
        document.getElementById("waterfall-scatter-switch2").checked = true
        document.getElementById("scatter").style.visibility = 'visible';
        document.getElementById("waterfall").style.visibility = 'hidden';
        document.getElementById("waterfall").style.height = '0px';
    }

    // remote tnc
    if (config.tnclocation == 'remote') {
        document.getElementById("local-remote-switch1").checked = false
        document.getElementById("local-remote-switch2").checked = true
        document.getElementById("remote-tnc-field").style.visibility = 'visible';
    } else {
        document.getElementById("local-remote-switch1").checked = true
        document.getElementById("local-remote-switch2").checked = false
        document.getElementById("remote-tnc-field").style.visibility = 'hidden';
    }

    // Create spectrum object on canvas with ID "waterfall"
    global.spectrum = new Spectrum(
        "waterfall", {
            spectrumPercent: 0
        });

    // SETUP OF SCATTER DIAGRAM
/*
    global.data = {
        datasets: [{
            label: 'Scatter Dataset',
            data: [{
                x: 0,
                y: 0
            }],
            backgroundColor: 'rgb(255, 99, 132)'
        }],
    };

    var ctx = document.getElementById('scatter').getContext('2d');
    global.myChart = new Chart(ctx, {
        type: 'scatter',
        data: data,
        options: {
            animation: false,
            legend: {
                display: false
            },

            scales: {
                display: false,
                grid: {
                    display: false
                },
                x: {
                    type: 'linear',
                    position: 'bottom',
                    display: false,
                    min: -50,
                    max: 50
                },
                y: {
                    display: false,
                    min: -50,
                    max: 50
                }

            }
        }
    });
*/

    // on click waterfall scatter toggle view
    // waterfall
    document.getElementById("waterfall-scatter-switch1").addEventListener("click", () => {
        document.getElementById("scatter").style.visibility = 'hidden';
        document.getElementById("waterfall").style.visibility = 'visible';
        document.getElementById("waterfall").style.height = '100%';
        config.spectrum = 'waterfall'
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
    // scatter
    document.getElementById("waterfall-scatter-switch2").addEventListener("click", () => {
        document.getElementById("scatter").style.visibility = 'visible';
        document.getElementById("waterfall").style.visibility = 'hidden';
        document.getElementById("waterfall").style.height = '0px';
        config.spectrum = 'scatter'
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

    // on click remote tnc toggle view
    document.getElementById("local-remote-switch1").addEventListener("click", () => {
        document.getElementById("local-remote-switch1").checked = true
        document.getElementById("local-remote-switch2").checked = false
        document.getElementById("remote-tnc-field").style.visibility = 'hidden';
        config.tnclocation = 'localhost'
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });
    document.getElementById("local-remote-switch2").addEventListener("click", () => {
        document.getElementById("local-remote-switch1").checked = false
        document.getElementById("local-remote-switch2").checked = true
        document.getElementById("remote-tnc-field").style.visibility = 'visible';
        config.tnclocation = 'remote'
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

    // on change port and host
    document.getElementById("tnc_adress").addEventListener("change", () => {
        console.log(document.getElementById("tnc_adress").value)
        config.tnc_host = document.getElementById("tnc_adress").value
        config.daemon_host = document.getElementById("tnc_adress").value
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    });

    // on change ping callsign
        document.getElementById("dxCall").addEventListener("change", () => {
        document.getElementById("dataModalDxCall").value = document.getElementById("dxCall").value
            });
    // on change ping callsign
        document.getElementById("dataModalDxCall").addEventListener("change", () => {
        document.getElementById("dxCall").value = document.getElementById("dataModalDxCall").value
            });
        
    

    document.getElementById("tnc_port").addEventListener("change", () => {
        config.tnc_port = document.getElementById("tnc_port").value
        config.daemon_port = parseInt(document.getElementById("tnc_port").value) + 1
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    });

    // saveMyCall button clicked
    document.getElementById("saveMyCall").addEventListener("click", () => {
        callsign = document.getElementById("myCall").value
        config.mycall = callsign.toUpperCase()
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        sock.saveMyCall(callsign)
    });

    // saveMyGrid button clicked
    document.getElementById("saveMyGrid").addEventListener("click", () => {
        grid = document.getElementById("myGrid").value
        config.mygrid = grid
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        sock.saveMyGrid(grid)

    });

    // startPing button clicked
    document.getElementById("sendPing").addEventListener("click", () => {
        var dxcallsign = document.getElementById("dxCall").value
        dxcallsign = dxcallsign.toUpperCase()
        sock.sendPing(dxcallsign)
    });

    // dataModalstartPing button clicked
    document.getElementById("dataModalSendPing").addEventListener("click", () => {
        var dxcallsign = document.getElementById("dataModalDxCall").value
        dxcallsign = dxcallsign.toUpperCase()
        sock.sendPing(dxcallsign)
    });

    // sendCQ button clicked
    document.getElementById("sendCQ").addEventListener("click", () => {
        sock.sendCQ()
    });

    // startTNC button clicked
    document.getElementById("startTNC").addEventListener("click", () => {
        var rx_audio = document.getElementById("audio_input_selectbox").value
        var tx_audio = document.getElementById("audio_output_selectbox").value
        var deviceid = document.getElementById("hamlib_deviceid").value
        var deviceport = document.getElementById("hamlib_deviceport").value
        var serialspeed = document.getElementById("hamlib_serialspeed").value
        var pttprotocol = document.getElementById("hamlib_ptt_protocol").value
        var pttport = document.getElementById("hamlib_ptt_port").value

        config.deviceid = deviceid
        config.deviceport = deviceport
        config.serialspeed = serialspeed
        config.pttprotocol = pttprotocol
        config.pttport = pttport
        
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

        daemon.startTNC(rx_audio, tx_audio, deviceid, deviceport, pttprotocol, pttport, serialspeed)
        setTimeout(function() {
            sock.saveMyCall(config.mycall);
        }, 3000);
        setTimeout(function() {
            sock.saveMyGrid(config.mygrid);
        }, 4000);
    })

    // stopTNC button clicked
    document.getElementById("stopTNC").addEventListener("click", () => {
        daemon.stopTNC()
    })

    // openDataModule button clicked
    document.getElementById("openDataModule").addEventListener("click", () => {
        if (document.getElementById("mySidebar").style.width == "40%") {
            document.getElementById("mySidebar").style.width = "0px";
        } else {
            document.getElementById("mySidebar").style.width = "40%";
        }
    })

    // START TRANSMISSION
    document.getElementById("startTransmission").addEventListener("click", () => {

        var fileList = document.getElementById("dataModalFile").files;

        var reader = new FileReader();
        //reader.readAsBinaryString(fileList[0]);
        reader.readAsDataURL(fileList[0]);

        reader.onload = function(e) {
            // binary data

            var data = e.target.result
            console.log(data)

            let Data = {
                command: "sendFile",
                dxcallsign: document.getElementById("dataModalDxCall").value.toUpperCase(),
                mode: document.getElementById("datamode").value,
                frames: document.getElementById("framesperburst").value,
                filetype: fileList[0].type,
                filename: fileList[0].name,
                data: data,
                checksum: '123123123',
            };
            ipcRenderer.send('run-tnc-command', Data);
        };
        reader.onerror = function(e) {
            // error occurred
            console.log('Error : ' + e.type);
        };

    })
    // START TRANSMISSION
    document.getElementById("stopTransmission").addEventListener("click", () => {
            let Data = {
                command: "stopTransmission"
            };
            ipcRenderer.send('run-tnc-command', Data);    
    })
  
})

  


ipcRenderer.on('action-update-tnc-state', (event, arg) => {
    //console.log(arg)
/*
    var fft = Array.from({
        length: 2048
    }, () => Math.floor(Math.random() * 10));
    spectrum.addData(fft);
  */
    
    // update FFT
    if (typeof(arg.fft) !== 'undefined') {
        //console.log(arg.fft)
        //console.log(typeof(arg.fft))
        var array = JSON.parse("[" + arg.fft + "]");
        //console.log(typeof(array))
        //console.log(array[0])
        spectrum.addData(array[0]);

    }


    // TOE TIME OF EXECUTION --> How many time needs a command to be executed until data arrives
    if (typeof(arg.toe) == 'undefined') {
        var toe = 0
    } else {
        var toe = arg.toe
    }
    document.getElementById("toe").innerHTML = toe + ' ms'

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
                        min: -40,
                        max: 40,
                        ticks: {
                            display: false
                        }            
                    },
                    y: {
                    
                        display: true,
                        min: -40,
                        max: 40,
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
        var scatterSize = 0
    } else {
        var scatterSize = arg.scatter.length
    }
    if (global.data != newdata && scatterSize > 0) {
        try {
            global.myChart.destroy();
        } catch (e) {
            // myChart not yet created
        }

        global.data = newdata


        var ctx = document.getElementById('scatter').getContext('2d');
        global.myChart = new Chart(ctx, {
            type: 'scatter',
            data: global.data,
            options: config
        });
    }

    // PTT STATE
    if (arg.ptt_state == 'True') {
        document.getElementById("ptt_state").className = "btn btn-danger";
    } else if (arg.ptt_state == 'False') {
        document.getElementById("ptt_state").className = "btn btn-success";
    } else {
        document.getElementById("ptt_state").className = "btn btn-secondary"
    }

    // BUSY STATE
    if (arg.busy_state == 'BUSY') {
        document.getElementById("busy_state").className = "btn btn-danger";
        document.getElementById("startTransmission").disabled = true
        document.getElementById("stopTransmission").disabled = false

    } else if (arg.busy_state == 'IDLE') {
        document.getElementById("busy_state").className = "btn btn-success";

    } else {
        document.getElementById("busy_state").className = "btn btn-secondary"
        document.getElementById("startTransmission").disabled = true
        document.getElementById("stopTransmission").disabled = false
    }

    // ARQ STATE
    if (arg.arq_state == 'DATA') {
        document.getElementById("arq_state").className = "btn btn-warning";
        document.getElementById("startTransmission").disabled = true
        document.getElementById("stopTransmission").disabled = false
    } else if (arg.arq_state == 'IDLE') {
        document.getElementById("arq_state").className = "btn btn-secondary";
        document.getElementById("startTransmission").disabled = false
        document.getElementById("stopTransmission").disabled = true
    } else {
        document.getElementById("arq_state").className = "btn btn-secondary"
        document.getElementById("startTransmission").disabled = true
        document.getElementById("stopTransmission").disabled = false
    }

    // RMS
    document.getElementById("rms_level").setAttribute("aria-valuenow", arg.rms_level)
    document.getElementById("rms_level").setAttribute("style", "width:" + arg.rms_level + "%;")

    // CHANNEL STATE
    if (arg.channel_state == 'RECEIVING_SIGNALLING') {
        document.getElementById("signalling_state").className = "btn btn-success";
        document.getElementById("data_state").className = "btn btn-secondary";

    } else if (arg.channel_state == 'SENDING_SIGNALLING') {
        document.getElementById("signalling_state").className = "btn btn-danger";
        document.getElementById("data_state").className = "btn btn-secondary";

    } else if (arg.channel_state == 'RECEIVING_DATA') {
        document.getElementById("signalling_state").className = "btn btn-secondary";
        document.getElementById("data_state").className = "btn btn-success";

    } else if (arg.channel_state == 'SENDING_DATA') {
        document.getElementById("signalling_state").className = "btn btn-secondary";
        document.getElementById("data_state").className = "btn btn-danger";
    } else {
        document.getElementById("signalling_state").className = "btn btn-secondary"
        document.getElementById("busy_state").className = "btn btn-secondary"

    }

    // SET FREQUENCY
    document.getElementById("frequency").innerHTML = arg.frequency

    // SET MODE
    document.getElementById("mode").innerHTML = arg.mode

    // SET BANDWITH
    document.getElementById("bandwith").innerHTML = arg.bandwith

    // SET BYTES PER MINUTE
    if (typeof(arg.arq_bytes_per_minute) == 'undefined') {
        var arq_bytes_per_minute = 0
    } else {
        var arq_bytes_per_minute = arg.arq_bytes_per_minute
    }
    document.getElementById("bytes_per_min").innerHTML = arq_bytes_per_minute

    // SET TOTAL BYTES
    if (typeof(arg.total_bytes) == 'undefined') {
        var total_bytes = 0
    } else {
        var total_bytes = arg.total_bytes
    }
    document.getElementById("total_bytes").innerHTML = total_bytes
    document.getElementById("transmission_progress").setAttribute("aria-valuenow", arg.arq_transmission_percent)
    document.getElementById("transmission_progress").setAttribute("style", "width:" + arg.arq_transmission_percent + "%;")

    // UPDATE HEARD STATIONS
    var tbl = document.getElementById("heardstations");
    document.getElementById("heardstations").innerHTML = ''

    if (typeof(arg.stations) == 'undefined') {
        var heardStationsLength = 0
    } else {
        var heardStationsLength = arg.stations.length
    }

    for (i = 0; i < heardStationsLength; i++) {

        // first we update the PING window
        if (arg.stations[i]['DXCALLSIGN'] == document.getElementById("dxCall").value) {
            var dxGrid = arg.stations[i]['DXGRID']
            var myGrid = document.getElementById("myGrid").value
            try {
                var dist = parseInt(distance(myGrid, dxGrid)) + ' km';
                document.getElementById("pingDistance").innerHTML = dist
                document.getElementById("dataModalPingDistance").innerHTML = dist
            } catch {
                document.getElementById("pingDistance").innerHTML = '---'
                document.getElementById("dataModalPingDistance").innerHTML = '---'
            }
            document.getElementById("pingDB").innerHTML = arg.stations[i]['SNR']
            document.getElementById("dataModalPingDB").innerHTML = arg.stations[i]['SNR']
        }

        // now we update the heard stations list
        var row = document.createElement("tr");
        //https://stackoverflow.com/q/51421470

        //https://stackoverflow.com/a/847196
        timestampRaw = arg.stations[i]['TIMESTAMP']
        var date = new Date(timestampRaw * 1000);
        var hours = date.getHours();
        var minutes = "0" + date.getMinutes();
        var seconds = "0" + date.getSeconds();
        var datetime = hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);

        var timestamp = document.createElement("td");
        var timestampText = document.createElement('span');
        timestampText.innerText = datetime
        timestamp.appendChild(timestampText);

        var dxCall = document.createElement("td");
        var dxCallText = document.createElement('span');
        dxCallText.innerText = arg.stations[i]['DXCALLSIGN']
        dxCall.appendChild(dxCallText);

        var dxGrid = document.createElement("td");
        var dxGridText = document.createElement('span');
        dxGridText.innerText = arg.stations[i]['DXGRID']
        dxGrid.appendChild(dxGridText);

        var gridDistance = document.createElement("td");
        var gridDistanceText = document.createElement('span');

        try {
            gridDistanceText.innerText = parseInt(distance(document.getElementById("myGrid").value, arg.stations[i]['DXGRID'])) + ' km';
        } catch {
            gridDistanceText.innerText = '---'
        }
        gridDistance.appendChild(gridDistanceText);

        var dataType = document.createElement("td");
        var dataTypeText = document.createElement('span');
        dataTypeText.innerText = arg.stations[i]['DATATYPE']
        dataType.appendChild(dataTypeText);

        if (dataTypeText.innerText == 'CQ CQ CQ') {
            row.classList.add("table-success");
        }

        if (dataTypeText.innerText == 'DATA-CHANNEL') {
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
        snrText.innerText = arg.stations[i]['SNR']
        snr.appendChild(snrText);

        row.appendChild(timestamp);
        row.appendChild(dxCall);
        row.appendChild(dxGrid);
        row.appendChild(gridDistance);
        row.appendChild(dataType);
        row.appendChild(snr);

        tbl.appendChild(row);
    }

});

ipcRenderer.on('action-update-daemon-state', (event, arg) => {

    // RAM
    document.getElementById("progressbar_ram").setAttribute("aria-valuenow", arg.ram_usage)
    document.getElementById("progressbar_ram").setAttribute("style", "width:" + arg.ram_usage + "%;")
    document.getElementById("progressbar_ram_value").innerHTML = arg.ram_usage + "%"

    // CPU
    document.getElementById("progressbar_cpu").setAttribute("aria-valuenow", arg.cpu_usage)
    document.getElementById("progressbar_cpu").setAttribute("style", "width:" + arg.cpu_usage + "%;")
    document.getElementById("progressbar_cpu_value").innerHTML = arg.cpu_usage + "%"

    // UPDATE AUDIO INPUT

    if (document.getElementById("audio_input_selectbox").length != arg.input_devices.length) {
        document.getElementById("audio_input_selectbox").innerHTML = ""
        for (i = 0; i < arg.input_devices.length; i++) {
            var option = document.createElement("option");
            option.text = arg.input_devices[i]['NAME'];
            option.value = arg.input_devices[i]['ID'];

            document.getElementById("audio_input_selectbox").add(option);
        }
    }
    // UPDATE AUDIO OUTPUT

    if (document.getElementById("audio_output_selectbox").length != arg.output_devices.length) {
        document.getElementById("audio_output_selectbox").innerHTML = ""
        for (i = 0; i < arg.output_devices.length; i++) {
            var option = document.createElement("option");
            option.text = arg.output_devices[i]['NAME'];
            option.value = arg.output_devices[i]['ID'];
            document.getElementById("audio_output_selectbox").add(option);
        }
    }

    // UPDATE SERIAL DEVICES

    if (document.getElementById("hamlib_deviceport").length != arg.serial_devices.length) {
        document.getElementById("hamlib_deviceport").innerHTML = ""
        for (i = 0; i < arg.serial_devices.length; i++) {
            var option = document.createElement("option");
            option.text = arg.serial_devices[i]['DESCRIPTION'];
            option.value = arg.serial_devices[i]['PORT'];
            document.getElementById("hamlib_deviceport").add(option);
        }
    }

    if (document.getElementById("hamlib_ptt_port").length != arg.serial_devices.length) {
        document.getElementById("hamlib_ptt_port").innerHTML = ""
        for (i = 0; i < arg.serial_devices.length; i++) {
            var option = document.createElement("option");
            option.text = arg.serial_devices[i]['DESCRIPTION'];
            option.value = arg.serial_devices[i]['PORT'];
            document.getElementById("hamlib_ptt_port").add(option);
        }
    }
    
    
    // TNC RUNNING STATE
    document.getElementById("tnc_running_state").innerHTML = arg.tnc_running_state;
    if (arg.tnc_running_state == "running") {
        document.getElementById('hamlib_deviceid').disabled = true
        document.getElementById('hamlib_deviceport').disabled = true
        document.getElementById('hamlib_ptt_port').disabled = true
        document.getElementById('hamlib_ptt_protocol').disabled = true
        document.getElementById('audio_input_selectbox').disabled = true
        document.getElementById('audio_output_selectbox').disabled = true
        document.getElementById('stopTNC').disabled = false
        document.getElementById('startTNC').disabled = true
        //document.getElementById('myCall').disabled = false
        document.getElementById('dxCall').disabled = false
        //document.getElementById('saveMyCall').disabled = false
        //document.getElementById('myGrid').disabled = false
        //document.getElementById('saveMyGrid').disabled = false
        document.getElementById("hamlib_serialspeed").disabled = true
        //document.getElementById("startTransmission").disabled = false

    } else {
        document.getElementById('hamlib_deviceid').disabled = false
        document.getElementById('hamlib_deviceport').disabled = false
        document.getElementById('hamlib_ptt_port').disabled = false
        document.getElementById('hamlib_ptt_protocol').disabled = false
        document.getElementById('audio_input_selectbox').disabled = false
        document.getElementById('audio_output_selectbox').disabled = false
        document.getElementById('stopTNC').disabled = true
        document.getElementById('startTNC').disabled = false
        //document.getElementById('myCall').disabled = true
        document.getElementById('dxCall').disabled = true
        //document.getElementById('saveMyCall').disabled = true
        //document.getElementById('myGrid').disabled = true
        //document.getElementById('saveMyGrid').disabled = true
        document.getElementById("hamlib_serialspeed").disabled = false
        //document.getElementById("startTransmission").disabled = true

    }

});

ipcRenderer.on('action-update-daemon-connection', (event, arg) => {

    if (arg.daemon_connection == 'open') {
        document.getElementById("daemon_connection_state").className = "btn btn-success";
        document.getElementById("blurdiv").style.webkitFilter = "blur(0px)";

    }
    if (arg.daemon_connection == 'opening') {
        document.getElementById("daemon_connection_state").className = "btn btn-warning";
        document.getElementById("blurdiv").style.webkitFilter = "blur(10px)";

    }
    if (arg.daemon_connection == 'closed') {
        document.getElementById("daemon_connection_state").className = "btn btn-danger";
        document.getElementById("blurdiv").style.webkitFilter = "blur(10px)";
    }

});

ipcRenderer.on('action-update-rx-buffer', (event, arg) => {

    var data = arg.data["DATA"]

    var tbl = document.getElementById("rx-data");
    document.getElementById("rx-data").innerHTML = ''

    for (i = 0; i < arg.data.length; i++) {

        // first we update the PING window
        if (arg.data[i]['DXCALLSIGN'] == document.getElementById("dxCall").value) {
            /*
            // if we are sending data without doing a ping before, we don't have a grid locator available. This could be a future feature for the TNC!
            if(arg.data[i]['DXGRID'] != ''){
                document.getElementById("pingDistance").innerHTML = arg.stations[i]['DXGRID']
            }
            */
            document.getElementById("pingDB").innerHTML = arg.stations[i]['SNR']

        }

        // now we update the received files list

        var row = document.createElement("tr");
        //https://stackoverflow.com/q/51421470

        //https://stackoverflow.com/a/847196
        timestampRaw = arg.data[i]['TIMESTAMP']
        var date = new Date(timestampRaw * 1000);
        var hours = date.getHours();
        var minutes = "0" + date.getMinutes();
        var seconds = "0" + date.getSeconds();
        var datetime = hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);

        var timestamp = document.createElement("td");
        var timestampText = document.createElement('span');
        timestampText.innerText = datetime
        timestamp.appendChild(timestampText);

        var dxCall = document.createElement("td");
        var dxCallText = document.createElement('span');
        dxCallText.innerText = arg.data[i]['DXCALLSIGN']
        dxCall.appendChild(dxCallText);

        /*
                var dxGrid = document.createElement("td");
                var dxGridText = document.createElement('span');
                dxGridText.innerText = arg.data[i]['DXGRID']
                dxGrid.appendChild(dxGridText);
        */

        var fileName = document.createElement("td");
        var fileNameText = document.createElement('span');
        var fileNameString = arg.data[i]['RXDATA'][0]['filename']
        fileNameText.innerText = fileNameString
        fileName.appendChild(fileNameText);

        row.appendChild(timestamp);
        row.appendChild(dxCall);
        //      row.appendChild(dxGrid);
        row.appendChild(fileName);

        tbl.appendChild(row);

        // https://stackoverflow.com/a/26227660
        var appDataFolder = process.env.HOME
        console.log("appDataFolder:" + appDataFolder)
        var applicationFolder = path.join(appDataFolder, "FreeDATA");
        console.log(applicationFolder)
        var receivedFilesFolder = path.join(applicationFolder, "receivedFiles");
        console.log("receivedFilesFolder: " + receivedFilesFolder)
        // Creates receivedFiles folder if not exists
        // https://stackoverflow.com/a/13544465
        fs.mkdir(receivedFilesFolder, {
            recursive: true
        }, function(err) {
            console.log(err);
        });


        // write file to rxdata folder
        var base64String = arg.data[i]['RXDATA'][0]['data']
        // remove header from base64 String
        // https://www.codeblocq.com/2016/04/Convert-a-base64-string-to-a-file-in-Node/
        var base64Data = base64String.split(';base64,').pop()
        //write data to file
        var receivedFile = path.join(receivedFilesFolder, fileNameString);
        console.log(receivedFile)

        require("fs").writeFile(receivedFile, base64Data, 'base64', function(err) {
            console.log(err);
        });
    }

});

ipcRenderer.on('run-tnc-command', (event, arg) => {
    if (arg.command == 'saveMyCall') {
        sock.saveMyCall(arg.callsign)
    }
    if (arg.command == 'saveMyGrid') {
        sock.saveMyGrid(arg.grid)
    }
    if (arg.command == 'ping') {
        sock.sendPing(arg.dxcallsign)
    }

    if (arg.command == 'sendFile') {
        sock.sendFile(arg.dxcallsign, arg.mode, arg.frames, arg.filename, arg.filetype, arg.data, arg.checksum)
    }
    if (arg.command == 'sendMessage') {
        sock.sendMessage(arg.dxcallsign, arg.mode, arg.frames, arg.data, arg.checksum)
    }
    if (arg.command == 'stopTransmission') {
        sock.stopTransmission()
    }
});
