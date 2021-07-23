
const { ipcRenderer } = require('electron');
 //const sock = require('./sock.js')
//const globals = require('./globals.js')



window.addEventListener('DOMContentLoaded', () => {
  const replaceText = (selector, text) => {
    const element = document.getElementById(selector)
    if (element) element.innerText = text
  }

   // sendPing button clicked 
   document.getElementById("sendPing").addEventListener("click", () => {
        dxcallsign = document.getElementById("dxCall").value
        //sock.sendPing(dxcallsign)
        
         let Data = {
            command: "ping",
            dxcallsign: document.getElementById("dxCall").value
        };
        ipcRenderer.send('run-tnc-command', Data);
    })  


     document.getElementById("startTransmission").addEventListener("click", () => {
      alert("HALLO ")
    })  



  
})




ipcRenderer.on('action-update-tnc-state', (event, arg) => {

// PTT STATE
    if(arg.ptt_state == 'True'){
    		document.getElementById("ptt_state").className = "btn btn-danger";
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
             
 });
 
 
 ipcRenderer.on('action-update-data-state', (event, arg) => {

 });