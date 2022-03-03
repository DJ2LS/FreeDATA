const path = require('path');
const {ipcRenderer} = require('electron');

// https://stackoverflow.com/a/26227660
var appDataFolder = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + "/.config")
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, 'config.json')
const config = require(configPath);



// WINDOW LISTENER
window.addEventListener('DOMContentLoaded', () => {
    // here we could add filter buttons, somewhen later..
    
})


ipcRenderer.on('action-update-log', (event, arg) => {

    var entry = arg.entry
   
   // remove ANSI characters from string, caused by color logging  
   // https://stackoverflow.com/a/29497680
   entry = entry.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g,'')

  
    var tbl = document.getElementById("log");
    var row = document.createElement("tr");

    var timestamp = document.createElement("td");
    var timestampText = document.createElement('span');
    datetime = new Date();
    timestampText.innerText = datetime.toISOString();
    timestamp.appendChild(timestampText);
    
    var logEntry = document.createElement("td");
    var logEntryText = document.createElement('span');
    logEntryText.innerText = entry
    logEntry.appendChild(logEntryText);

    row.appendChild(timestamp);
    row.appendChild(logEntry);
    tbl.appendChild(row);



    if (logEntryText.innerText.includes('ALSA lib pcm')) {
        row.classList.add("table-secondary");
    }
    
    if (logEntryText.innerText.includes('[info ]')) {
        row.classList.add("table-info");
    }
    if (logEntryText.innerText.includes('[debug ]')) {
        row.classList.add("table-secondary");
    }

    if (logEntryText.innerText.includes('[warning ]')) {
        row.classList.add("table-warning");
    }  
    
    if (logEntryText.innerText.includes('[error ]')) {
        row.classList.add("table-danger");
    }    
        
    
    // scroll to bottom of page
    // https://stackoverflow.com/a/11715670
    window.scrollTo(0,document.body.scrollHeight);
    

})
