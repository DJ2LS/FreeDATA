var net = require('net');
var config = require('./config.json');
const {
    ipcRenderer
} = require('electron');

var client = new net.Socket();
var msg = ''; // Current message, per connection.

setTimeout(connectTNC, 3000)

function connectTNC() {
    //exports.connectTNC = function(){
    console.log('connecting to TNC...')

    //clear message buffer after reconnecting or inital connection
    msg = '';
    client.connect(config.tnc_port, config.tnc_host)
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

    console.log(command)
    // we use the writingCommand function to update our TCPIP state because we are calling this function a lot
    // if socket openend, we are able to run commands
    if (client.readyState == 'open') {
        //uiMain.setTNCconnection('open')
        client.write(command + '\n');
    }

    if (client.readyState == 'closed') {
        //uiMain.setTNCconnection('closed')
        console.log("CLOSED!!!!!")
    }

    if (client.readyState == 'opening') {
        //uiMain.setTNCconnection('opening')
        console.log("OPENING!!!!!")
    }
}



client.on('data', function(data) {

    /* 
    stackoverflow.com questions 9070700 nodejs-net-createserver-large-amount-of-data-coming-in
    */

    data = data.toString('utf8'); // convert data to string
    msg += data.toString('utf8'); // append data to buffer so we can stick long data together

    // check if we reached an EOF, if true, clear buffer and parse JSON data
    if (data.endsWith('}')) {
        //console.log(msg)
        try {
            //console.log(msg)
            data = JSON.parse(msg)
        } catch (e) {
            console.log(e); /* "SyntaxError*/
        }
        msg = '';
        /* console.log("EOF detected!") */


        if (data['COMMAND'] == 'TNC_STATE') {
            let Data = {
                ptt_state: data['PTT_STATE'],
                busy_state: data['TNC_STATE'],
                arq_state: data['ARQ_STATE'],
                channel_state: data['CHANNEL_STATE'],
                frequency: data['FREQUENCY'],
                mode: data['MODE'],
                bandwith: data['BANDWITH'],
                rms_level: (data['AUDIO_RMS'] / 1000) * 100,
            };
            console.log(Data)
            ipcRenderer.send('request-update-tnc-state', Data);
        }

        if (data['COMMAND'] == 'DATA_STATE') {
            let Data = {
                rx_buffer_length: data['RX_BUFFER_LENGTH'],
                tx_n_max_retries: data['TX_N_MAX_RETRIES'],
                arq_tx_n_frames_per_burst: data['ARQ_TX_N_FRAMES_PER_BURST'],
                arq_tx_n_bursts: data['ARQ_TX_N_BURSTS'],
                arq_tx_n_current_arq_frame: data['ARQ_TX_N_CURRENT_ARQ_FRAME'],
                arq_tx_n_total_arq_frames: data['ARQ_TX_N_TOTAL_ARQ_FRAMES'],
                arq_rx_frame_n_bursts: data['ARQ_RX_FRAME_N_BURSTS'],
                arq_rx_n_current_arq_frame: data['ARQ_RX_N_CURRENT_ARQ_FRAME'],
                arq_n_arq_frames_per_data_frame: data['ARQ_N_ARQ_FRAMES_PER_DATA_FRAME'],
            };
            console.log(Data)
            ipcRenderer.send('request-update-data-state', Data);
        }

        if (data['COMMAND'] == 'HEARD_STATIONS') {
            //console.log(data['STATIONS'])
            let Data = {
                stations: data['STATIONS'],
            };
            //console.log(Data)
            ipcRenderer.send('request-update-heard-stations', Data);
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
    command = '{"type" : "SET", "command": "MYCALLSIGN" , "parameter": "' + callsign + '" }'
    writeTncCommand(command)
}

// Save myGrid
exports.saveMyGrid = function(grid) {
    command = '{"type" : "SET", "command": "MYGRID" , "parameter": "' + grid + '" }'
    writeTncCommand(command)
}

//Get TNC State
exports.getTncState = function() {
    command = '{"type" : "GET", "command" : "TNC_STATE"}';
    writeTncCommand(command)
}

//Get DATA State
exports.getDataState = function() {
    command = '{"type" : "GET", "command" : "DATA_STATE"}';
    //writeTncCommand(command)
}

//Get Heard Stations
exports.getHeardStations = function() {
    command = '{"type" : "GET", "command" : "HEARD_STATIONS"}';
    writeTncCommand(command)
}
 

// Send Ping
exports.sendPing = function(dxcallsign) {
    command = '{"type" : "PING", "command" : "PING", "dxcallsign" : "' + dxcallsign + '"}'
    writeTncCommand(command)
}

// Send CQ
exports.sendCQ = function() {
    command = '{"type" : "CQ", "command" : "CQCQCQ"}'
    writeTncCommand(command)
}

// Send File
exports.sendFile = function(dxcallsign, mode, frames, filename, filetype, data, checksum) {
    command = '{"type" : "ARQ", "command" : "sendFile",  "dxcallsign" : " '+dxcallsign+' ", "mode" : " '+mode+' ", n_"frames" : " '+frames+' ", "filename" : " '+filename+' ", "filetype" : " '+filetype+' ", "data" : " '+data+' ", "checksum" : " '+checksum+' "}'
    writeTncCommand(command)
}

// Send Message
exports.sendMessage = function(dxcallsign, mode, frames, data, checksum) {
    command = '{"type" : "ARQ", "command" : "sendMessage",  "dxcallsign" : " '+dxcallsign+' ", "mode" : " '+mode+' ", "n_frames" : " '+frames+' ", "data" : " '+data+' ", "checksum" : " '+checksum+' "}'
    writeTncCommand(command)
}