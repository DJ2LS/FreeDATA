const path = require('path')
const {
    ipcRenderer
} = require('electron')

// https://stackoverflow.com/a/26227660
var appDataFolder = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + "/.config")
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, 'config.json')
const config = require(configPath);

var chatDB = path.join(configFolder, 'chatDB.json')


// WINDOW LISTENER
window.addEventListener('DOMContentLoaded', () => {
    // SEND MSG
    document.getElementById("sendMessage").addEventListener("click", () => {
            dxcallsign = document.getElementById('chatModuleDxCall').value
            message = document.getElementById('chatModuleMessage').value

            let Data = {
                command: "send_message",
                dxcallsign : dxcallsign.toUpperCase(), 
                mode : 12, 
                frames : 1, 
                data : message, 
                checksum : '123'
            };
            ipcRenderer.send('run-tnc-command', Data);    
    })

})


ipcRenderer.on('action-update-rx-msg-buffer', (event, arg) => {

    var data = arg.data
    var tbl = document.getElementById("rx-msg-data");
    document.getElementById("rx-msg-data").innerHTML = ''
    
    
    

    for (i = 0; i < arg.data.length; i++) {
    
    
    
    // now we update the received files list

        var row = document.createElement("tr");
        //https://stackoverflow.com/q/51421470

        //https://stackoverflow.com/a/847196
        timestampRaw = arg.data[i]['timestamp']
        var date = new Date(timestampRaw * 1000);
        var hours = date.getHours();
        var minutes = "0" + date.getMinutes();
        var seconds = "0" + date.getSeconds();
        var datetime = hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);

        var timestamp = document.createElement("td");
        var timestampText = document.createElement('span');
        timestampText.innerText = datetime
        timestamp.appendChild(timestampText);

        var dxCall = document.createElement("td");
        var dxCallText = document.createElement('span');
        dxCallText.innerText = arg.data[i]['dxcallsign']
        dxCall.appendChild(dxCallText);

        var message = document.createElement("td");
        var messageText = document.createElement('span');
        var messageString = arg.data[i]['rxdata'][0]['d'] //data
        console.log(messageString)
        messageText.innerText = messageString
        message.appendChild(messageText);

        row.appendChild(timestamp);
        row.appendChild(dxCall);
        row.appendChild(message);

        tbl.appendChild(row);

    }

})
