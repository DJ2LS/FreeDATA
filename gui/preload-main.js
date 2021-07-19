const sock = require('./sock.js')
const daemon = require('./daemon.js')

setInterval(daemon.getDaemonState, 1000) 
setInterval(sock.getTncState, 250)  


const { ipcRenderer } = require('electron');





window.addEventListener('DOMContentLoaded', () => {

/*
globals.tnc_host = document.getElementById("tnc_adress").value
globals.tnc_port = document.getElementById("tnc_port").value
console.log(globals.tnc_host)
console.log(globals.tnc_port)
setInterval(sock.connectTNC, 500)  
*/
//setInterval( function() { sock.connectTNC(tnc_host, tnc_port); }, 500 );

  
//setInterval(sock.getTncState, 500)  
//setInterval(daemon.getDaemonState, 500)  
//setInterval(uiMain.updateFFT, 250)  



// Create spectrum object on canvas with ID "waterfall"
    global.spectrum = new Spectrum(
        "waterfall", {
            spectrumPercent: 20
    });




   // saveMyCall button clicked 
   document.getElementById("saveMyCall").addEventListener("click", () => {
        callsign = document.getElementById("myCall").value
        sock.saveMyCall(callsign)
        /*        
        let Data = {
            command: "saveMyCall",
            callsign: document.getElementById("myCall").value
        };
        ipcRenderer.send('run-tnc-command', Data);
        
        */
        
        
    })  

   // saveMyGrid button clicked 
   document.getElementById("saveMyGrid").addEventListener("click", () => {
        grid = document.getElementById("myGrid").value
        sock.saveMyGrid(grid)
       /*
        let Data = {
            command: "saveMyGrid",
            grid: document.getElementById("myGrid").value
        };
        ipcRenderer.send('run-tnc-command', Data);
*/
    })  
    
    // startPing button clicked 
   document.getElementById("sendPing").addEventListener("click", () => {
        dxcallsign = document.getElementById("dxCall").value
        sock.sendPing(dxcallsign)
        /*        
        let Data = {
            command: "saveMyCall",
            callsign: document.getElementById("myCall").value
        };
        ipcRenderer.send('run-tnc-command', Data);
        
        */
        
        
    })  
    
           // sendCQ button clicked 
   document.getElementById("sendCQ").addEventListener("click", () => {
    sock.sendCQ()

        
        
    })  
       
       
       
       
       

   // startTNC button clicked 
   document.getElementById("startTNC").addEventListener("click", () => {        
        var rx_audio = document.getElementById("audio_input_selectbox").value
        var tx_audio = document.getElementById("audio_output_selectbox").value    
        var deviceid = document.getElementById("hamlib_deviceid").value
        var deviceport = document.getElementById("hamlib_deviceport").value
        var ptt = document.getElementById("hamlib_ptt").value

        daemon.startTNC(rx_audio, tx_audio, deviceid, deviceport, ptt)
        /*
         let Data = {
            command: "startTNC",
            rx_audio : document.getElementById("audio_input_selectbox").value,
            tx_audio : document.getElementById("audio_output_selectbox").value,   
            deviceid : document.getElementById("hamlib_deviceid").value,
            deviceport : document.getElementById("hamlib_deviceport").value,
            ptt : document.getElementById("hamlib_ptt").value,
        };
        ipcRenderer.send('run-daemon-command', Data);
        */
        
        
    })  

   // stopTNC button clicked 
   document.getElementById("stopTNC").addEventListener("click", () => {        
        daemon.stopTNC()
  /*               let Data = {
            command: "stopTNC",
        };
        ipcRenderer.send('run-daemon-command', Data);
   */
    })  
        
   // openDataModule button clicked 
   document.getElementById("openDataModule").addEventListener("click", () => {        
    //data.show()
    let Data = {
    message: "Hello World !"
    };
    ipcRenderer.send('show-data-window', Data);
      })        
  
  
  

  
  
  
})






ipcRenderer.on('action-update-tnc-state', (event, arg) => {

// PTT STATE
    if(arg.ptt_state == 'True'){
    		document.getElementById("ptt_state").className = "btn btn-danger";
    		console.log("PTT TRUE!!!")

    	} else if(arg.ptt_state == 'False'){
    		document.getElementById("ptt_state").className = "btn btn-success";	
    	} else {
    	    document.getElementById("ptt_state").className = "btn btn-secondary"
    	}

// BUSY STATE
    	if(arg.busy_state == 'BUSY'){
    		document.getElementById("busy_state").className = "btn btn-danger";
    	} else if(arg.busy_state == 'IDLE'){
    		document.getElementById("busy_state").className = "btn btn-success";	
    	} else {
    	    document.getElementById("busy_state").className = "btn btn-secondary"
    	}		            
            
// ARQ STATE
    	if(arg.arq_state == 'DATA'){
    		document.getElementById("arq_state").className = "btn btn-warning";
    	} else if(arg.arq_state == 'IDLE'){
    		document.getElementById("arq_state").className = "btn btn-secondary";	
    	} else {
    	    document.getElementById("arq_state").className = "btn btn-secondary"
    	}	            
            
// RMS
		document.getElementById("rms_level").setAttribute("aria-valuenow", arg.rms_level)
		document.getElementById("rms_level").setAttribute("style", "width:" + arg.rms_level + "%;")	
            
// CHANNEL STATE
		if(arg.channel_state == 'RECEIVING_SIGNALLING'){
    		document.getElementById("signalling_state").className = "btn btn-success";
    		document.getElementById("data_state").className = "btn btn-secondary";
    		
    	} else if(arg.channel_state == 'SENDING_SIGNALLING'){
    		document.getElementById("signalling_state").className = "btn btn-danger";
    		document.getElementById("data_state").className = "btn btn-secondary";

    	} else if(arg.channel_state == 'RECEIVING_DATA'){
    		document.getElementById("signalling_state").className = "btn btn-secondary";
    		document.getElementById("data_state").className = "btn btn-success";
    		
    	} else if(arg.channel_state == 'SENDING_DATA'){
    		document.getElementById("signalling_state").className = "btn btn-secondary";
    		document.getElementById("data_state").className = "btn btn-danger";
   		} else {
    	    document.getElementById("signalling_state").className = "btn btn-secondary"
    	    document.getElementById("busy_state").className = "btn btn-secondary"

    	}		              
            
// SET FREQUENCY
		document.getElementById("frequency").value = arg.frequency

// SET MODE
		document.getElementById("mode").value = arg.mode

// SET BANDWITH
		document.getElementById("bandwith").value = arg.bandwith        
            });




ipcRenderer.on('action-update-daemon-state', (event, arg) => {
// UPDATE AUDIO INPUT

    if(document.getElementById("audio_input_selectbox").length != arg.input_devices.length){
        document.getElementById("audio_input_selectbox").innerHTML = ""
        for (i = 0; i < arg.input_devices.length; i++) { 
            var option = document.createElement("option");
            option.text = arg.input_devices[i]['NAME'];
            option.value = arg.input_devices[i]['ID'];

            document.getElementById("audio_input_selectbox").add(option);
        }
    }
    // UPDATE AUDIO OUTPUT

        if(document.getElementById("audio_output_selectbox").length != arg.output_devices.length){
        document.getElementById("audio_output_selectbox").innerHTML = ""
        for (i = 0; i < arg.output_devices.length; i++) { 
            var option = document.createElement("option");
            option.text = arg.output_devices[i]['NAME'];
            option.value = arg.output_devices[i]['ID'];
            document.getElementById("audio_output_selectbox").add(option);
        }
    }
    
// TNC RUNNING STATE
document.getElementById("tnc_running_state").innerHTML = arg.tnc_running_state;
    if(arg.tnc_running_state == "running"){
     document.getElementById('hamlib_deviceid').disabled = true
     document.getElementById('hamlib_deviceport').disabled = true
     document.getElementById('hamlib_ptt').disabled = true
     document.getElementById('audio_input_selectbox').disabled = true
     document.getElementById('audio_output_selectbox').disabled = true
     document.getElementById('stopTNC').disabled = false
     document.getElementById('startTNC').disabled = true
     document.getElementById('myCall').disabled = false
     document.getElementById('saveMyCall').disabled = false
     document.getElementById('myGrid').disabled = false
     document.getElementById('saveMyGrid').disabled = false
        
    } else {
     document.getElementById('hamlib_deviceid').disabled = false   
     document.getElementById('hamlib_deviceport').disabled = false
     document.getElementById('hamlib_ptt').disabled = false
     document.getElementById('audio_input_selectbox').disabled = false
     document.getElementById('audio_output_selectbox').disabled = false
     document.getElementById('stopTNC').disabled = true
     document.getElementById('startTNC').disabled = false
     document.getElementById('myCall').disabled = true
     document.getElementById('saveMyCall').disabled = true
     document.getElementById('myGrid').disabled = true
     document.getElementById('saveMyGrid').disabled = true
    }


            });


ipcRenderer.on('action-update-daemon-connection', (event, arg) => {


	if(arg.daemon_connection == 'open'){
		 document.getElementById("daemon_connection_state").className = "btn btn-success";
	}
	if(arg.daemon_connection == 'opening'){
    	 document.getElementById("daemon_connection_state").className = "btn btn-warning";
	}
	if(arg.daemon_connection == 'closed'){
	      document.getElementById("daemon_connection_state").className = "btn btn-danger";
	}			

   });
   
   
   
   
   
   ipcRenderer.on('run-tnc-command', (event, arg) => {
    if (arg.command == 'saveMyCall'){
        sock.saveMyCall(arg.callsign)
    }
    if (arg.command == 'saveMyGrid'){
        sock.saveMyGrid(arg.grid)
    }
    if (arg.command == 'ping'){
     sock.sendPing(arg.dxcallsign)
    }    
      });


/*
   ipcRenderer.on('run-daemon-command', (event, arg) => {
    if (arg.command == 'startTNC'){
           daemon.startTNC(arg.rx_audio, arg.tx_audio, arg.deviceid, arg.deviceport, arg.ptt)

    }
    if (arg.command == 'stopTNC'){
        daemon.stopTNC()

    }
      });

*/


   