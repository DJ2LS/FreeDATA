var net = require('net');
const path = require('path')
const {
    ipcRenderer
} = require('electron')

// https://stackoverflow.com/a/26227660
var appDataFolder = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + "/.config")
var configFolder = path.join(appDataFolder, "codec2-FreeDATA");
var configPath = path.join(configFolder, 'config.json')
const config = require(configPath);

var client = new net.Socket();
var msg = ''; // Current message, per connection.

// globals for getting new data only if available
var rxBufferLengthTnc = 0
var rxBufferLengthGui = 0

// network connection Timeout
setTimeout(connectTNC, 3000)

function connectTNC() {
    //exports.connectTNC = function(){
    //console.log('connecting to TNC...')

    //clear message buffer after reconnecting or inital connection
    msg = '';

    if (config.tnclocation == 'localhost') {
        client.connect(3000, '127.0.0.1')
    } else {
        client.connect(config.tnc_port, config.tnc_host)
    }
}

client.on('connect', function(data) {
    console.log('TNC connection established')
})

client.on('error', function(data) {
    console.log('TNC connection error');

    let Data = {
        busy_state: "-",
        arq_state: "-",
        channel_state: "-",
        frequency: "-",
        mode: "-",
        bandwith: "-",
        rms_level: 0

    };
    ipcRenderer.send('request-update-tnc-state', Data);

    setTimeout(connectTNC, 2000)
    // setTimeout( function() { exports.connectTNC(tnc_host, tnc_port); }, 2000 );

});

/*
client.on('close', function(data) {
	console.log(' TNC connection closed');
    setTimeout(connectTNC, 2000) 
});
*/

client.on('end', function(data) {
    console.log('TNC connection ended');
    //setTimeout(connectTNC, 2000)  
    setTimeout(connectTNC, 0)

    //      setTimeout( function() { exports.connectTNC(tnc_host, tnc_port); }, 2000 );

});

//exports.writeTncCommand = function(command){    
writeTncCommand = function(command) {

    //console.log(command)
    // we use the writingCommand function to update our TCPIP state because we are calling this function a lot
    // if socket openend, we are able to run commands
    if (client.readyState == 'open') {
        //uiMain.setTNCconnection('open')
        client.write(command + '\n');
    }

    if (client.readyState == 'closed') {
        //uiMain.setTNCconnection('closed')
        //console.log("CLOSED!!!!!")
    }

    if (client.readyState == 'opening') {
        //uiMain.setTNCconnection('opening')
        //console.log("OPENING!!!!!")
        console.log('connecting to TNC...')
    }
}

client.on('data', function(data) {

    /* 
    stackoverflow.com questions 9070700 nodejs-net-createserver-large-amount-of-data-coming-in
    */

    data = data.toString('utf8'); // convert data to string
    msg += data.toString('utf8'); // append data to buffer so we can stick long data together
    //console.log(data)
    // check if we reached an EOF, if true, clear buffer and parse JSON data
    if (data.endsWith('"EOF":"EOF"}')) {
        //console.log(msg)
        try {
            //console.log(msg)
            data = JSON.parse(msg)
        } catch (e) {
            console.log(e); /* "SyntaxError*/
        }
        msg = '';
        /* console.log("EOF detected!") */

        //console.log(data)

        if (data['COMMAND'] == 'TNC_STATE') {
            //console.log(data)
            rxBufferLengthTnc = data['RX_BUFFER_LENGTH']

            let Data = {
                toe: Date.now() - data['TIMESTAMP'], // time of execution
                ptt_state: data['PTT_STATE'],
                busy_state: data['TNC_STATE'],
                arq_state: data['ARQ_STATE'],
                channel_state: data['CHANNEL_STATE'],
                frequency: data['FREQUENCY'],
                mode: data['MODE'],
                bandwith: data['BANDWITH'],
                rms_level: (data['AUDIO_RMS'] / 1000) * 100,
                scatter: data['SCATTER'],
                rx_buffer_length: data['RX_BUFFER_LENGTH'],
                tx_n_max_retries: data['TX_N_MAX_RETRIES'],
                arq_tx_n_frames_per_burst: data['ARQ_TX_N_FRAMES_PER_BURST'],
                arq_tx_n_bursts: data['ARQ_TX_N_BURSTS'],
                arq_tx_n_current_arq_frame: data['ARQ_TX_N_CURRENT_ARQ_FRAME'],
                arq_tx_n_total_arq_frames: data['ARQ_TX_N_TOTAL_ARQ_FRAMES'],
                arq_rx_frame_n_bursts: data['ARQ_RX_FRAME_N_BURSTS'],
                arq_rx_n_current_arq_frame: data['ARQ_RX_N_CURRENT_ARQ_FRAME'],
                arq_n_arq_frames_per_data_frame: data['ARQ_N_ARQ_FRAMES_PER_DATA_FRAME'],
                arq_bytes_per_minute: data['ARQ_BYTES_PER_MINUTE'],
                total_bytes: data['TOTAL_BYTES'],
                arq_transmission_percent: data['ARQ_TRANSMISSION_PERCENT'],
                stations: data['STATIONS'],
            };
            //console.log(Data)
            ipcRenderer.send('request-update-tnc-state', Data);
        }

        if (data['COMMAND'] == 'RX_BUFFER') {

            rxBufferLengthGui = data['DATA-ARRAY'].length
            //console.log(rxBufferLengthGui)
            let Data = {
                data: data['DATA-ARRAY'],
            };
            //console.log(Data)
            ipcRenderer.send('request-update-rx-buffer', Data);
        }

        // check if EOF	...
    }

});

function hexToBytes(hex) {
    for (var bytes = [], c = 0; c < hex.length; c += 2)
        bytes.push(parseInt(hex.substr(c, 2), 16));
    return bytes;
}

//Save myCall 
exports.saveMyCall = function(callsign) {
    command = '{"type" : "SET", "command": "MYCALLSIGN" , "parameter": "' + callsign + '", "timestamp" : ' + Date.now() + '}'
    writeTncCommand(command)
}

// Save myGrid
exports.saveMyGrid = function(grid) {
    command = '{"type" : "SET", "command": "MYGRID" , "parameter": "' + grid + '", "timestamp" : ' + Date.now() + '}'
    writeTncCommand(command)
}

//Get TNC State
exports.getTncState = function() {
    command = '{"type" : "GET", "command" : "TNC_STATE", "timestamp" : ' + Date.now() + '}';
    writeTncCommand(command)
}

//Get DATA State
exports.getDataState = function() {
    command = '{"type" : "GET", "command" : "DATA_STATE", "timestamp" : ' + Date.now() + '}';
    //writeTncCommand(command)
}

//Get Heard Stations
exports.getHeardStations = function() {
    command = '{"type" : "GET", "command" : "HEARD_STATIONS", "timestamp" : ' + Date.now() + '}';
    writeTncCommand(command)
}

// Send Ping
exports.sendPing = function(dxcallsign) {
    command = '{"type" : "PING", "command" : "PING", "dxcallsign" : "' + dxcallsign + '", "timestamp" : ' + Date.now() + '}'
    writeTncCommand(command)
}

// Send CQ
exports.sendCQ = function() {
    command = '{"type" : "CQ", "command" : "CQCQCQ", "timestamp" : ' + Date.now() + '}'
    writeTncCommand(command)
}

// Send File
exports.sendFile = function(dxcallsign, mode, frames, filename, filetype, data, checksum) {
    command = '{"type" : "ARQ", "command" : "sendFile",  "dxcallsign" : "' + dxcallsign + '", "mode" : "' + mode + '", "n_frames" : "' + frames + '", "filename" : "' + filename + '", "filetype" : "' + filetype + '", "data" : "' + data + '", "checksum" : "' + checksum + '", "timestamp" : ' + Date.now() + '}'
    writeTncCommand(command)
}

// Send Message
exports.sendMessage = function(dxcallsign, mode, frames, data, checksum) {
    command = '{"type" : "ARQ", "command" : "sendMessage",  "dxcallsign" : " ' + dxcallsign + ' ", "mode" : " ' + mode + ' ", "n_frames" : " ' + frames + ' ", "data" :  ' + data + ' , "checksum" : " ' + checksum + ' ", "timestamp" : ' + Date.now() + '}'
    writeTncCommand(command)
}

// Get RX BUffer
exports.getRxBuffer = function() {
    command = '{"type" : "GET", "command" : "RX_BUFFER", "timestamp" : ' + Date.now() + '}'

    // call command only if new data arrived
    if (rxBufferLengthGui != rxBufferLengthTnc) {
        writeTncCommand(command)
    }
}