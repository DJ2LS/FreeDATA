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
    let Data = {
        daemon_connection: daemon.readyState,
    };
    ipcRenderer.send('request-update-daemon-connection', Data);

})

daemon.on('error', function(data) {
    console.log('DAEMON connection error');
    setTimeout(connectDAEMON, 2000)
    let Data = {
        daemon_connection: daemon.readyState,
    };
    ipcRenderer.send('request-update-daemon-connection', Data);

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

daemon.on('end', function(data) {
    console.log('DAEMON connection ended');
    setTimeout(connectDAEMON, 2000)
    let Data = {
        daemon_connection: daemon.readyState,
    };
    ipcRenderer.send('request-update-daemon-connection', Data);
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
    if (data.endsWith('}\n')) {
        /*console.log(msg)*/
        try {
            /*console.log(msg)*/
            data = JSON.parse(msg)
        } catch (e) {
            console.log(e); /* "SyntaxError */
        }
        msg = '';
        /*console.log("EOF detected!")*/

        if (data['command'] == 'daemon_state') {
            let Data = {
                input_devices: data['input_devices'],
                output_devices: data['output_devices'],
                python_version: data['python_version'],
                hamlib_version: data['hamlib_version'],
                serial_devices: data['serial_devices'],
                tnc_running_state: data['daemon_state'][0]['status'],
                ram_usage: data['ram'],
                cpu_usage: data['cpu'],
                version: data['version'],
            };
            ipcRenderer.send('request-update-daemon-state', Data);
        }

        if (data['command'] == 'test_hamlib') {
            let Data = {
                hamlib_result: data['result'],
                
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
    command = '{"type" : "get", "command" : "daemon_state"}'
    writeDaemonCommand(command)
}

// START TNC
// ` `== multi line string

exports.startTNC = function(mycall, mygrid, rx_audio, tx_audio, radiocontrol, devicename, deviceport, pttprotocol, pttport, serialspeed, data_bits, stop_bits, handshake, rigctld_ip, rigctld_port) {
    var json_command = JSON.stringify({
        type: 'set',
        command: 'start_tnc',
        parameter: [{
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
            rigctld_ip: rigctld_ip
        }]
    })

    console.log(json_command)
    writeDaemonCommand(json_command)

}

// STOP TNC
exports.stopTNC = function() {
    command = '{"type" : "set", "command": "stop_tnc" , "parameter": "---" }'
    writeDaemonCommand(command)
}

// TEST HAMLIB
exports.testHamlib = function(radiocontrol, devicename, deviceport, serialspeed, pttprotocol, pttport, data_bits, stop_bits, handshake, rigctld_ip, rigctld_port) {

    var json_command = JSON.stringify({
        type: 'get',
        command: 'test_hamlib',
        parameter: [{
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
            rigctld_ip: rigctld_ip
        }]
    })
    console.log(json_command)
    writeDaemonCommand(json_command)
}



//Save myCall
exports.saveMyCall = function(callsign) {
    command = '{"type" : "set", "command": "mycallsign" , "parameter": "' + callsign + '"}'
    writeDaemonCommand(command)
}

// Save myGrid
exports.saveMyGrid = function(grid) {
    command = '{"type" : "set", "command": "mygrid" , "parameter": "' + grid + '"}'
    writeDaemonCommand(command)
}


