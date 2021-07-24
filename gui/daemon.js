var net = require('net');
var config = require('./config.json');


var daemon = new net.Socket();
var msg = ''; // Current message, per connection.

const {
    ipcRenderer
} = require('electron');


setTimeout(connectDAEMON, 500)

function connectDAEMON() {

    console.log('connecting to DAEMON...')

    //clear message buffer after reconnecting or inital connection
    msg = '';
    daemon.connect(config.daemon_port, config.daemon_host)
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
        console.log(command)
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
                tnc_running_state: data['DAEMON_STATE'][0]['STATUS']

            };
            ipcRenderer.send('request-update-daemon-state', Data);

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
    command = '{"type" : "GET", "command": "DAEMON_STATE"}'
    writeDaemonCommand(command)
}




// START TNC
// ` `== multi line string


exports.startTNC = function(rx_audio, tx_audio, deviceid, deviceport, ptt) {
    var json_command = JSON.stringify({
        type: 'SET',
        command: 'STARTTNC',
        parameter: [{
            rx_audio: rx_audio,
            tx_audio: tx_audio,
            deviceid: deviceid,
            deviceport: deviceport,
            ptt: ptt
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