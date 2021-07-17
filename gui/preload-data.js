
const { ipcRenderer } = require('electron');
 


window.addEventListener('DOMContentLoaded', () => {
  const replaceText = (selector, text) => {
    const element = document.getElementById(selector)
    if (element) element.innerText = text
  }



     document.getElementById("startTransmission").addEventListener("click", () => {
      alert("HALLO ")
    })  



  
})




            ipcRenderer.on('action-update-tnc-state', (event, arg) => {

                
                
                    	if(arg.ptt_state == 'True'){
    		document.getElementById("ptt_state").className = "btn btn-danger";
    	} else if(arg.ptt_state == 'False'){
    		document.getElementById("ptt_state").className = "btn btn-success";	
    	} else {
    	    document.getElementById("ptt_state").className = "btn btn-secondary"
    	}
            });