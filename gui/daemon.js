var net = require('net');
const path = require('path')
const {
    ipcRenderer
} = require('electron')

// https://stackoverflow.com/a/26227660
var appDataFolder = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + "/.config")
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, 'config.json')
const config = require(configPath);

var daemon = new net.Socket();
var msg = ''; // Current message, per connection.

setTimeout(connectDAEMON, 500)

function connectDAEMON() {

    console.log('connecting to DAEMON...')

    //clear message buffer after reconnecting or inital connection
    msg = '';
    
    if (config.tnclocation == 'localhost') {
        daemon.connect(3001, '127.0.0.1')
    } else {
        daemon.connect(config.daemon_port, config.daemon_host)

    }

    //client.setTimeout(5000);
}

daemon.on('connect', function(data) {
    console.log('DAEMON connection established')
})

daemon.on('error', function(data) {
    console.log('DAEMON connection error');
    setTimeout(connectDAEMON, 2000)
});

/*
client.on('close', function(data) {
	console.log(' TNC connection closed');
    setTimeout(connectTNC, 2000)
});
*/

daemon.on('end', function(data) {
    console.log('DAEMON connection ended');
    setTimeout(connectDAEMON, 2000)
});

//exports.writeCommand = function(command){
writeDaemonCommand = function(command) {

    // we use the writingCommand function to update our TCPIP state because we are calling this function a lot
    // if socket openend, we are able to run commands
    if (daemon.readyState == 'open') {
        //uiMain.setDAEMONconnection('open')
        daemon.write(command + '\n');
    }

    if (daemon.readyState == 'closed') {
        //uiMain.setDAEMONconnection('closed')
    }

    if (daemon.readyState == 'opening') {
        //uiMain.setDAEMONconnection('opening')
    }

    let Data = {
        daemon_connection: daemon.readyState,
    };
    ipcRenderer.send('request-update-daemon-connection', Data);
}

// "https://stackoverflow.com/questions/9070700/nodejs-net-createserver-large-amount-of-data-coming-in"

daemon.on('data', function(data) {

    data = data.toString('utf8'); /* convert data to string */
    msg += data.toString('utf8'); /*append data to buffer so we can stick long data together */

    /* check if we reached an EOF, if true, clear buffer and parse JSON data */
    if (data.endsWith('}')) {
        /*console.log(msg)*/
        try {
            /*console.log(msg)*/
            data = JSON.parse(msg)
        } catch (e) {
            console.log(e); /* "SyntaxError */
        }
        msg = '';
        /*console.log("EOF detected!")*/

        if (data['COMMAND'] == 'DAEMON_STATE') {
            let Data = {
                input_devices: data['INPUT_DEVICES'],
                output_devices: data['OUTPUT_DEVICES'],
                python_version: data['PYTHON_VERSION'],
                hamlib_version: data['HAMLIB_VERSION'],
                serial_devices: data['SERIAL_DEVICES'],
                tnc_running_state: data['DAEMON_STATE'][0]['STATUS'],
                ram_usage: data['RAM'],
                cpu_usage: data['CPU'],
                version: data['VERSION'],
            };
            ipcRenderer.send('request-update-daemon-state', Data);
        }

        if (data['COMMAND'] == 'TEST_HAMLIB') {
            let Data = {
                hamlib_result: data['RESULT'],
                
            };
            ipcRenderer.send('request-update-hamlib-test', Data);
        }
        
        
        ////// check if EOF	...
    }

});

function hexToBytes(hex) {
    for (var bytes = [], c = 0; c < hex.length; c += 2)
        bytes.push(parseInt(hex.substr(c, 2), 16));
    return bytes;
}

exports.getDaemonState = function() {
    //function getDaemonState(){
    command = '{"type" : "GET", "command" : "DAEMON_STATE"}'
    writeDaemonCommand(command)
}

// START TNC
// ` `== multi line string

exports.startTNC = function(rx_audio, tx_audio, devicename, deviceport, pttprotocol, pttport, serialspeed, pttspeed, data_bits, stop_bits, handshake) {
    var json_command = JSON.stringify({
        type: 'SET',
        command: 'STARTTNC',
        parameter: [{
            rx_audio: rx_audio,
            tx_audio: tx_audio,
            devicename: devicename,
            deviceport: deviceport,
            pttprotocol: pttprotocol,
            pttport: pttport,
            serialspeed: serialspeed,
            pttspeed: pttspeed,
            data_bits: data_bits,
            stop_bits: stop_bits,
            handshake: handshake

        }]
    })

    //console.log(json_command)
    writeDaemonCommand(json_command)

}

// STOP TNC
exports.stopTNC = function() {
    command = '{"type" : "SET", "command": "STOPTNC" , "parameter": "---" }'
    writeDaemonCommand(command)
}

// TEST HAMLIB
exports.testHamlib = function(devicename, deviceport, serialspeed, pttprotocol, pttport, pttspeed, data_bits, stop_bits, handshake) {

    var json_command = JSON.stringify({
        type: 'GET',
        command: 'TEST_HAMLIB',
        parameter: [{
            devicename: devicename,
            deviceport: deviceport,
            pttprotocol: pttprotocol,
            pttport: pttport,
            serialspeed: serialspeed,
            pttspeed: pttspeed,
            data_bits: data_bits,
            stop_bits: stop_bits,
            handshake: handshake

        }]
    })
    console.log(json_command)
    writeDaemonCommand(json_command)
}


