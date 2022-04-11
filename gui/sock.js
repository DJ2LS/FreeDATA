var net = require('net');
const path = require('path')
const {
    ipcRenderer
} = require('electron')

const log = require('electron-log');
const socketLog = log.scope('tnc');
const utf8 = require('utf8');
    
    
// https://stackoverflow.com/a/26227660
var appDataFolder = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + "/.config")
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, 'config.json')
const config = require(configPath);

var client = new net.Socket();
var socketchunk = ''; // Current message, per connection.

// split character
const split_char = '\0;'

// globals for getting new data only if available so we are saving bandwith
var rxBufferLengthTnc = 0
var rxBufferLengthGui = 0
var rxMsgBufferLengthTnc = 0
var rxMsgBufferLengthGui = 0

// network connection Timeout
setTimeout(connectTNC, 2000)

function connectTNC() {
    //exports.connectTNC = function(){
    //socketLog.info('connecting to TNC...')

    //clear message buffer after reconnecting or inital connection
    socketchunk = '';

    if (config.tnclocation == 'localhost') {
        client.connect(3000, '127.0.0.1')
    } else {
        client.connect(config.tnc_port, config.tnc_host)
    }
}

client.on('connect', function(data) {
    socketLog.info('TNC connection established')
    let Data = {
        busy_state: "-",
        arq_state: "-",
        //channel_state: "-",
        frequency: "-",
        mode: "-",
        bandwith: "-",
        rms_level: 0
    };
    ipcRenderer.send('request-update-tnc-state', Data);
    
    // also update tnc connection state
    ipcRenderer.send('request-update-tnc-connection', {tnc_connection : client.readyState});   
    
    
})

client.on('error', function(data) {
    socketLog.error('TNC connection error');
    socketLog.error(data);
    let Data = {
        tnc_connection: client.readyState,
        busy_state: "-",
        arq_state: "-",
        //channel_state: "-",
        frequency: "-",
        mode: "-",
        bandwith: "-",
        rms_level: 0

    };
    ipcRenderer.send('request-update-tnc-state', Data);
    ipcRenderer.send('request-update-tnc-connection', {tnc_connection : client.readyState});
    client.destroy();
    setTimeout(connectTNC, 500)
    // setTimeout( function() { exports.connectTNC(tnc_host, tnc_port); }, 2000 );

});

/*
client.on('close', function(data) {
	socketLog.info(' TNC connection closed');
    setTimeout(connectTNC, 2000)
});
*/

client.on('end', function(data) {
    socketLog.info('TNC connection ended');
    ipcRenderer.send('request-update-tnc-connection', {tnc_connection : client.readyState});
    client.destroy();
    
    setTimeout(connectTNC, 500)

});

writeTncCommand = function(command) {
    
    //socketLog.info(command)
    // we use the writingCommand function to update our TCPIP state because we are calling this function a lot
    // if socket opened, we are able to run commands

    
    
    if (client.readyState == 'open') {
        client.write(command + '\n');

    }

    if (client.readyState == 'closed') {
        socketLog.info("CLOSED!")

    }

    if (client.readyState == 'opening') {
        socketLog.info('connecting to TNC...')

    }
}

client.on('data', function(socketdata) {

    ipcRenderer.send('request-update-tnc-connection', {tnc_connection : client.readyState});

    /*
    inspired by:
    stackoverflow.com questions 9070700 nodejs-net-createserver-large-amount-of-data-coming-in
    */

    socketdata = socketdata.toString('utf8'); // convert data to string
    socketchunk += socketdata// append data to buffer so we can stick long data together


    // check if we received begin and end of json data
    if (socketchunk.startsWith('{"') && socketchunk.endsWith('"}\n')) {

        var data = ''

        // split data into chunks if we received multiple commands
        socketchunk = socketchunk.split("\n"); 
        data = JSON.parse(socketchunk[0])    
             

        // search for empty entries in socketchunk and remove them
        for (i = 0; i < socketchunk.length; i++) {
            if (socketchunk[i] === ''){
                socketchunk.splice(i, 1);
            }
        }
        
        
        //iterate through socketchunks array to execute multiple commands in row 
        for (i = 0; i < socketchunk.length; i++) {

            //check if data is not empty
            if(socketchunk[i].length > 0){
            
                //try to parse JSON
                try {

                    data = JSON.parse(socketchunk[i])

                } catch (e) {
                    socketLog.info(e); // "SyntaxError
                    socketLog.info(socketchunk[i])
                    socketchunk = ''

                }

            }
            

            if (data['command'] == 'tnc_state') {
                //socketLog.info(data)
                // set length of RX Buffer to global variable
                rxBufferLengthTnc = data['rx_buffer_length']
                rxMsgBufferLengthTnc = data['rx_msg_buffer_length']

                let Data = {
                    ptt_state: data['ptt_state'],
                    busy_state: data['tnc_state'],
                    arq_state: data['arq_state'],
                    arq_session: data['arq_session'],
                    //channel_state: data['CHANNEL_STATE'],
                    frequency: data['frequency'],
                    speed_level: data['speed_level'],
                    mode: data['mode'],
                    bandwith: data['bandwith'],
                    rms_level: data['audio_rms'],
                    fft: data['fft'],
                    channel_busy: data['channel_busy'],
                    scatter: data['scatter'],
                    info: data['info'],
                    rx_buffer_length: data['rx_buffer_length'],
                    rx_msg_buffer_length: data['rx_msg_buffer_length'],
                    tx_n_max_retries: data['tx_n_max_retries'],
                    arq_tx_n_frames_per_burst: data['arq_tx_n_frames_per_burst'],
                    arq_tx_n_bursts: data['arq_tx_n_bursts'],
                    arq_tx_n_current_arq_frame: data['arq_tx_n_current_arq_frame'],
                    arq_tx_n_total_arq_frames: data['arq_tx_n_total_arq_frames'],
                    arq_rx_frame_n_bursts: data['arq_rx_frame_n_bursts'],
                    arq_rx_n_current_arq_frame: data['arq_rx_n_current_arq_frame'],
                    arq_n_arq_frames_per_data_frame: data['arq_n_arq_frames_per_data_frame'],
                    arq_bytes_per_minute: data['arq_bytes_per_minute'],
                    arq_compression_factor: data['arq_compression_factor'],
                    total_bytes: data['total_bytes'],
                    arq_transmission_percent: data['arq_transmission_percent'],
                    stations: data['stations'],
                    beacon_state: data['beacon_state'],
                };

                ipcRenderer.send('request-update-tnc-state', Data);
            }

            // update transmission status

            if (data['arq'] == 'transmission'){
            socketLog.info(data)
            
                let state = {
                    status: data['status'],
                    uuid: data['uuid'],
                    percent: data['percent'],
                    bytesperminute: data['bytesperminute'],
                };
            ipcRenderer.send('request-update-transmission-status', state);                
                
            
            }

            // Check for Ping 
            if (data['type'] == 'ping') {
                ipcRenderer.send('request-new-msg-received', {data: [data]});
            }

            // Check for Beacon 
            if (data['type'] == 'beacon') {
                ipcRenderer.send('request-new-msg-received', {data: [data]});
            }
            
            /* A TEST WITH STREAMING DATA .... */       
            // if we received data through network stream, we get a single data item
            if (data['arq'] == 'received') {
                dataArray = []
                messageArray = []

                socketLog.info(data)
                // we need to encode here to do a deep check for checking if file or message
                var encoded_data = atob(data['data'])
                var splitted_data = encoded_data.split(split_char)
                
                
                if(splitted_data[0] == 'f'){
                    dataArray.push(data)
                }
                        
                if(splitted_data[0] == 'm'){
                    messageArray.push(data)
                    console.log(data)
                }

                rxBufferLengthGui = dataArray.length
                let Files = {
                    data: dataArray,
                };
                ipcRenderer.send('request-update-rx-buffer', Files);
                ipcRenderer.send('request-new-msg-received', Files);
                
                rxMsgBufferLengthGui = messageArray.length
                let Messages = {
                    data: messageArray,
                };
                ipcRenderer.send('request-new-msg-received', Messages);
            }
            
            // if we manually checking for the rx buffer we are getting an array of multiple data
            if (data['command'] == 'rx_buffer') {
                socketLog.info(data)
                // iterate through buffer list and sort it to file or message array
                dataArray = []
                messageArray = []

                for (i = 0; i < data['data-array'].length; i++) {
                    try{
                        // we need to encode here to do a deep check for checking if file or message
                        var encoded_data = atob(data['data-array'][i]['data'])
                        var splitted_data = encoded_data.split(split_char)


                        if(splitted_data[0] == 'f'){
                            dataArray.push(data['data-array'][i]) 

                        }
                        
                        if(splitted_data[0] == 'm'){
                            messageArray.push(data['data-array'][i])

                        }
                        
                    } catch (e) {
                        socketLog.info(e)
                    }
                }
            
                
                
                rxBufferLengthGui = dataArray.length
                let Files = {
                    data: dataArray,
                };
                ipcRenderer.send('request-update-rx-buffer', Files);
                
                rxMsgBufferLengthGui = messageArray.length
                let Messages = {
                    data: messageArray,
                };
                //ipcRenderer.send('request-update-rx-msg-buffer', Messages);
                ipcRenderer.send('request-new-msg-received', Messages);
                
      
            }

        }
   
    //finally delete message buffer 
    socketchunk = '';
    
    }
});

function hexToBytes(hex) {
    for (var bytes = [], c = 0; c < hex.length; c += 2)
        bytes.push(parseInt(hex.substr(c, 2), 16));
    return bytes;
}


//Get TNC State
exports.getTncState = function() {
    command = '{"type" : "get", "command" : "tnc_state"}';
    writeTncCommand(command)
}

//Get DATA State
exports.getDataState = function() {
    command = '{"type" : "get", "command" : "data_state"}';
    //writeTncCommand(command)
}


// Send Ping
exports.sendPing = function(dxcallsign) {
    command = '{"type" : "ping", "command" : "ping", "dxcallsign" : "' + dxcallsign + '"}'
    writeTncCommand(command)
}

// Send CQ
exports.sendCQ = function() {
    command = '{"type" : "broadcast", "command" : "cqcqcq"}'
    writeTncCommand(command)
}

// Set AUDIO Level
exports.setTxAudioLevel = function(value) {
    command = '{"type" : "set", "command" : "tx_audio_level", "value" : "'+ value +'"}'
    writeTncCommand(command)
}



// Send File
exports.sendFile = function(dxcallsign, mode, frames, filename, filetype, data, checksum) {

    socketLog.info(data) 
    socketLog.info(filetype)
    socketLog.info(filename)
                
    var datatype = "f"

    data = datatype + split_char + filename + split_char + filetype + split_char + checksum + split_char + data
    socketLog.info(data)
    socketLog.info(btoa(data))
    data = btoa(data)

    command = '{"type" : "arq", "command" : "send_raw",  "parameter" : [{"dxcallsign" : "' + dxcallsign + '", "mode" : "' + mode + '", "n_frames" : "' + frames + '", "data" : "' + data + '"}]}'
    writeTncCommand(command)
}

// Send Message
exports.sendMessage = function(dxcallsign, mode, frames, data, checksum, uuid, command) {
    socketLog.info(data) 
    // convert message to plain utf8 because of unicode emojis
    data = utf8.encode(data)
    socketLog.info(data) 
    
    var datatype = "m"
    data = datatype + split_char + command + split_char + checksum + split_char + uuid + split_char + data
    socketLog.info(data)
    
    
    
    socketLog.info(btoa(data))
    data = btoa(data)

    //command = '{"type" : "arq", "command" : "send_message", "parameter" : [{ "dxcallsign" : "' + dxcallsign + '", "mode" : "' + mode + '", "n_frames" : "' + frames + '", "data" :  "' + data + '" , "checksum" : "' + checksum + '"}]}'
    command = '{"type" : "arq", "command" : "send_raw",  "uuid" : "'+ uuid +'", "parameter" : [{"dxcallsign" : "' + dxcallsign + '", "mode" : "' + mode + '", "n_frames" : "' + frames + '", "data" : "' + data + '"}]}'
    socketLog.info(command)
    socketLog.info("-------------------------------------")
    writeTncCommand(command)
}


//STOP TRANSMISSION
exports.stopTransmission = function() {
    command = '{"type" : "arq", "command": "stop_transmission"}'
    writeTncCommand(command)
}

// Get RX BUffer
exports.getRxBuffer = function() {
    command = '{"type" : "get", "command" : "rx_buffer"}'

    // call command only if new data arrived
    if (rxBufferLengthGui != rxBufferLengthTnc) {
        writeTncCommand(command)
    }
}


// START BEACON
exports.startBeacon = function(interval) {
    command = '{"type" : "broadcast", "command" : "start_beacon", "parameter": "' + interval + '"}'
    writeTncCommand(command)
}

// STOP BEACON
exports.stopBeacon = function() {
    command = '{"type" : "broadcast", "command" : "stop_beacon"}'
    writeTncCommand(command)
}

// OPEN ARQ SESSION
exports.connectARQ = function(dxcallsign) {
    command = '{"type" : "arq", "command" : "connect", "dxcallsign": "'+ dxcallsign + '"}'
    writeTncCommand(command)
}

// CLOSE ARQ SESSION
exports.disconnectARQ = function() {
    command = '{"type" : "arq", "command" : "disconnect"}'
    writeTncCommand(command)
}

// SEND SINE
exports.sendTestFrame = function() {
    command = '{"type" : "set", "command" : "send_test_frame"}'
    writeTncCommand(command)
}
