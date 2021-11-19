const path = require('path')
const {
    ipcRenderer
} = require('electron')
const sock = require('./sock.js');


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
            dxcallsign = 'DN2LS'
            let Data = {
                command: "sendMessage",
                dxcallsign : dxcallsign.toUpperCase(), 
                mode : 10, 
                frames : 1, 
                data : 'hallo welt', 
                checksum : '123'
            };
            ipcRenderer.send('run-tnc-command', Data);    
    })

})


ipcRenderer.on('action-update-rx-buffer', (event, arg) => {

    alert(arg)


})
