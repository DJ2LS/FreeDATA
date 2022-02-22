const {
    app,
    BrowserWindow,
    ipcMain
} = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const fs = require('fs');
const os = require('os');
const exec = require('child_process').spawn;

app.setName("FreeDATA");

var appDataFolder = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + "/.config");
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, 'config.json');

// create config folder if not exists
if (!fs.existsSync(configFolder)) {
    fs.mkdirSync(configFolder);
}

// create config file if not exists
var configContent = `
{
  "tnc_host": "127.0.0.1",
  "tnc_port": "3000",
  "daemon_host": "127.0.0.1",
  "daemon_port": "3001",
  "mycall": "AA0AA",
  "mygrid": "JN40aa",
  "deviceid": "RIG_MODEL_DUMMY_NOVFO",
  "deviceport": "/dev/ttyACM1",
  "serialspeed_direct": "9600",
  "spectrum": "waterfall",
  "tnclocation": "localhost",
  "stop_bits_direct" : "1",
  "data_bits_direct" : "8",
  "handshake_direct" : "None",
  "radiocontrol" : "disabled",
  "deviceport_rigctl" : "3",
  "deviceid_rigctl" : "3",
  "serialspeed_rigctl" : "9600",
  "pttprotocol_direct" : "USB",
  "pttprotocol_rigctl" : "USB",
  "rigctld_port" : "4532",
  "rigctld_ip" : "127.0.0.1",
  "enable_scatter" : "False",
  "enable_fft" : "False",
  "low_bandwith_mode" : "False",
  "theme" : "default",
  "screen_height" : 430,
  "screen_width" : 1050
}
`;
if (!fs.existsSync(configPath)) {
    fs.writeFileSync(configPath, configContent)
}



var chatDB = path.join(configFolder, 'chatDB.json')
// create chat database file if not exists
var configContent = `
{ "chatDB" : [{
    "id" : "00000000",
    "timestamp" : 1234566,
    "mycall" : "AA0AA",
    "dxcall" : "AB0AB",
    "dxgrid" : "JN1200",
    "message" : "hallowelt"
}]
}
`;
if (!fs.existsSync(chatDB)) {
    fs.writeFileSync(chatDB, configContent);
}



/*
// Creates receivedFiles folder if not exists
// https://stackoverflow.com/a/26227660
var appDataFolder = process.env.HOME
var applicationFolder = path.join(appDataFolder, "FreeDATA");
var receivedFilesFolder = path.join(applicationFolder, "receivedFiles");

// https://stackoverflow.com/a/13544465
fs.mkdir(receivedFilesFolder, {
    recursive: true
}, function(err) {
    console.log(err);
});

*/



const config = require(configPath);


let win = null;
let data = null;
var daemonProcess = null;

function createWindow() {
    win = new BrowserWindow({
        width: config.screen_width,
        height: config.screen_height,
        autoHideMenuBar: true,
        icon: __dirname + '/src/icon_cube_border.png',
        webPreferences: {
            //preload: path.join(__dirname, 'preload-main.js'),
            preload: require.resolve('./preload-main.js'),
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: false, //https://stackoverflow.com/questions/53390798/opening-new-window-electron/53393655 https://github.com/electron/remote
        }
    })
    // hide menu bar
    win.setMenuBarVisibility(false)

    //open dev tools
    /*win.webContents.openDevTools({
        mode: 'undocked',
        activate: true,
    })
    */
    win.loadFile('src/index.html')
    
    chat = new BrowserWindow({
        height: 900,
        width: 600,
        show: false,
        parent: win,
        webPreferences: {
            preload: require.resolve('./preload-chat.js'),
            nodeIntegration: true,

        }
    })

    chat.loadFile('src/chat-module.html');
    chat.setMenuBarVisibility(false);


    // Emitted when the window is closed.
    win.on('closed', function() {
        // Dereference the window object, usually you would store windows
        // in an array if your app supports multi windows, this is the time
        // when you should delete the corresponding element.
        win = null;
        chat = null;
    })
    
    
    win.once('ready-to-show', () => {
    
        autoUpdater.autoInstallOnAppQuit = true;
        autoUpdater.autoDownload = true;
        autoUpdater.checkForUpdatesAndNotify();
    });

    
    chat.on('closed', function () {
            // Dereference the window object, usually you would store windows
            // in an array if your app supports multi windows, this is the time
            // when you should delete the corresponding element.
        })
    

    // https://stackoverflow.com/questions/44258831/only-hide-the-window-when-closing-it-electron
    chat.on('close', function(evt) {
        evt.preventDefault();
        chat.hide();
    });
    
}

app.whenReady().then(() => {
    createWindow();

    // start daemon by checking os
    console.log("Trying to start daemon binary")
    

    if(os.platform()=='darwin'){
        daemonProcess = exec(path.join(process.resourcesPath, 'tnc', 'daemon'), [], 
            {   
                cwd: path.join(process.resourcesPath, 'tnc'),              
            });                
    }    
    
    /*
    process.resourcesPath -->
    /tmp/.mount_FreeDAUQYfKb/resources
    
    __dirname -->
    /tmp/.mount_FreeDAUQYfKb/resources/app.asar
    */

    if(os.platform()=='linux'){
        console.log("starting daemon...")
        console.log("-------------------------------")

    var folder = path.join(process.resourcesPath, 'tnc');
    //var folder = path.join(__dirname, 'extraResources', 'tnc');
    console.log(folder);
    fs.readdir(folder, (err, files) => {
        console.log(files);
    });
    
        console.log("-------------------------------")        
        
        daemonProcess = exec(path.join(process.resourcesPath, 'tnc', 'daemon'), [], 
            {   
                cwd: path.join(process.resourcesPath, 'tnc'),              
            });
        
    }

    
    if(os.platform()=='win32' || os.platform()=='win64'){
        // for windows the relative path via path.join(__dirname) is not needed for some reason 
        //daemonProcess = exec('\\tnc\\daemon.exe', [])
        
        daemonProcess = exec(path.join(process.resourcesPath, 'tnc', 'daemon.exe'), [], 
            {   
                cwd: path.join(process.resourcesPath, 'tnc'),              
            });
                
    }

    // return process messages
    
    daemonProcess.on('error', (err) => {
          console.log(`error when starting daemon: ${err}`);
    });
        
    daemonProcess.on('message', (data) => {
          console.log(data);
    });
    daemonProcess.stdout.on('data', (data) => {
      console.log(`daemonProcess stdout: ${data}`);
    });

    daemonProcess.stderr.on('data', (data) => {
      console.error(`daemonProcess stderr: ${data}`);
    });

    daemonProcess.on('close', (code) => {
      console.log(`daemonProcess exited with code ${code}`);
    });



    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    })
})

app.on('window-all-closed', () => {
    // closing the tnc binary if not closed when closing application and also our daemon which has been started by the gui
    try {
        daemonProcess.kill();
    } catch (e) {   
        console.log(e);
    }
    

    console.log("closing tnc...")
    
    if(os.platform()=='win32' || os.platform()=='win64'){
        exec('Taskkill', ['/IM', 'tnc.exe', '/F'])
    }
    
    if(os.platform()=='linux' || os.platform()=='darwin'){
        console.log("kill tnc process...")
        exec('pkill', ['-9', 'tnc'])
        
        // on macOS we need to kill the daemon as well. If we are not doing this, 
        // the daemon wont startup again because the socket is already in use
        console.log("kill daemon process...")
        exec('pkill', ['-9', 'daemon'])        
        
    }
        

    if (process.platform !== 'darwin') {
        app.quit();
    }
})

// IPC HANDLER

ipcMain.on('request-show-chat-window', (event, arg) => {
    chat.show();
 });


ipcMain.on('request-update-tnc-state', (event, arg) => {
    win.webContents.send('action-update-tnc-state', arg);
    //data.webContents.send('action-update-tnc-state', arg);
});

/*
ipcMain.on('request-update-data-state', (event, arg) => {
    //win.webContents.send('action-update-data-state', arg);
    //data.webContents.send('action-update-data-state', arg);
});

ipcMain.on('request-update-heard-stations', (event, arg) => {
    win.webContents.send('action-update-heard-stations', arg);
});
*/
ipcMain.on('request-update-daemon-state', (event, arg) => {
    win.webContents.send('action-update-daemon-state', arg);
});

ipcMain.on('request-update-hamlib-test', (event, arg) => {
    win.webContents.send('action-update-hamlib-test', arg);
});



ipcMain.on('request-update-tnc-connection', (event, arg) => {
    win.webContents.send('action-update-tnc-connection', arg);
});

ipcMain.on('request-update-daemon-connection', (event, arg) => {
    win.webContents.send('action-update-daemon-connection', arg);
});

ipcMain.on('run-tnc-command', (event, arg) => {
    win.webContents.send('run-tnc-command', arg);
});

ipcMain.on('request-update-rx-buffer', (event, arg) => {
    win.webContents.send('action-update-rx-buffer', arg);
});

ipcMain.on('request-update-rx-msg-buffer', (event, arg) => {
    chat.webContents.send('action-update-rx-msg-buffer', arg);
});


// LISTENER FOR UPDATER EVENTS
autoUpdater.on('update-available', () => {
  console.log('update available');
    let arg = {
        status: "update-available"
    };
  win.webContents.send('action-updater', arg);
  
});

autoUpdater.on('update-not-available', () => {
  console.log('update-not-available');
    let arg = {
        status: "update-not-available"
    };
  win.webContents.send('action-updater', arg);  
});


autoUpdater.on('update-downloaded', () => {
  console.log('update downloaded');
      let arg = {
        status: "update-downloaded"
    };
  win.webContents.send('action-updater', arg); 
});

autoUpdater.on('checking-for-update', () => {
    let arg = {
        status: "checking-for-update",
        version: app.getVersion()
    };
  win.webContents.send('action-updater', arg); 
});

autoUpdater.on('download-progress', (progress) => {
    let arg = {
        status: "download-progress",
        progress: progress
    };
  win.webContents.send('action-updater', arg); 
});

autoUpdater.on('error', (progress) => {
    let arg = {
        status: "error",
        progress: progress
    };
  win.webContents.send('action-updater', arg); 
});

// not needed yet
// gives possibility of directly restarting the app
ipcMain.on('restart_app', () => {
  autoUpdater.quitAndInstall();
});
