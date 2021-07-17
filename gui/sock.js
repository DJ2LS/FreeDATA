var net = require('net');

const { ipcRenderer } = require('electron');

var client = new net.Socket();
var msg = ''; // Current message, per connection.



setTimeout(connectTNC, 500)

function connectTNC(){

    console.log('connecting to TNC...')
    
    //clear message buffer after reconnecting or inital connection
    msg = '';
    
    tnc_host = document.getElementById("tnc_adress").value
    tnc_port = document.getElementById("tnc_port").value
    client.connect(tnc_port, tnc_host)
    //client.setTimeout(5000);
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
                    frequency : "-",
                    mode: "-",
                    bandwith: "-",
                    rms_level : 0

        };
	    ipcRenderer.send('request-update-tnc-state', Data);	
	
    setTimeout(connectTNC, 2000)
});

/*
client.on('close', function(data) {
	console.log(' TNC connection closed');
    setTimeout(connectTNC, 2000) 
});
*/

client.on('end', function(data) {
	console.log('TNC connection ended');
    setTimeout(connectTNC, 2000)  
});


//exports.writeTncCommand = function(command){    
  writeTncCommand = function(command){    
  
    console.log(command)
    // we use the writingCommand function to update our TCPIP state because we are calling this function a lot
	// if socket openend, we are able to run commands
    if(client.readyState == 'open'){
    	//uiMain.setTNCconnection('open')
	    client.write(command + '\n');
    }
    
    if(client.readyState == 'closed'){
   		//uiMain.setTNCconnection('closed')
    }

    if(client.readyState == 'opening'){
		//uiMain.setTNCconnection('opening')
    }       
}


  
client.on('data', function(data) {

/* 
stackoverflow.com questions 9070700 nodejs-net-createserver-large-amount-of-data-coming-in
*/
    
    data = data.toString('utf8'); // convert data to string
    msg += data.toString('utf8'); // append data to buffer so we can stick long data together
 
/* 
    if (msg.charCodeAt(msg.length - 1) == 0) {
      client.emit('message', msg.substring(0, msg.length - 1));
      msg = '';
      console.log("END OF FILE")
    }
  */
  
  /*
    if (msg.startsWith('{"COMMAND":')) {
    	msg = '';
    	msg += data.toString('utf8');
    	console.log("BOF detected!")
   } 
   */
   
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
      
      
     
	
	
	if(data['COMMAND'] == 'TNC_STATE'){
	    



		// FFT
		//fft_raw = data['FFT']
		//var fft = Buffer.from(fft_raw, "hex")
		//var fft = hexToBytes(fft_raw)
		//var fft = Array.from(fft_raw)
		//console.log(typeof(fft))
		
		
			    
	    let Data = {
                    ptt_state: data['PTT_STATE'],
                    busy_state: data['TNC_STATE'],
                    arq_state: data['ARQ_STATE'],
                    channel_state: data['CHANNEL_STATE'],
                    frequency : data['FREQUENCY'],
                    mode: data['MODE'],
                    bandwith: data['BANDWITH'],
                    rms_level : (data['AUDIO_RMS']/1000)*100

        };
	    ipcRenderer.send('request-update-tnc-state', Data);
		
		
		var fft = Array.from({length: 2048}, () => Math.floor(Math.random() * 10));
		//console.log(fft)
		//uiMain.updateFFT(fft)
		
				
	}
	
	// check if EOF	...
    }
	
	
	
});

function hexToBytes(hex) {
    for (var bytes = [], c = 0; c < hex.length; c += 2)
    bytes.push(parseInt(hex.substr(c, 2), 16));
    return bytes;
}








//Save callsign 
  exports.saveMyCall = function(callsign){
        command = '{"type" : "SET", "command": "MYCALLSIGN" , "parameter": "'+ callsign +'" }'
        writeTncCommand(command)
}

  exports.saveMyGrid = function(grid){
        command = '{"type" : "SET", "command": "MYGRID" , "parameter": "'+ grid +'" }'
        writeTncCommand(command)
}

 exports.getTncState = function(){
        command = '{"type" : "GET", "command": "TNC_STATE"}';
        writeTncCommand(command)
}
