const {
    app,
    BrowserWindow,
    ipcMain,
    dialog,
    shell
} = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const fs = require('fs');
const os = require('os');
const exec = require('child_process').spawn;
const log = require('electron-log');
const mainLog = log.scope('main');
const daemonProcessLog = log.scope('freedata-daemon');

const sysInfo = log.scope('system information');
sysInfo.info("SYSTEM INFORMATION  -----------------------------  ");
sysInfo.info("APP VERSION : " + app.getVersion());
sysInfo.info("PLATFORM    : " + os.platform());
sysInfo.info("ARCHITECTURE: " + os.arch());
sysInfo.info("FREE  MEMORY: " + os.freemem());
sysInfo.info("TOTAL MEMORY: " + os.totalmem());
sysInfo.info("LOAD AVG    : " + os.loadavg());
sysInfo.info("RELEASE     : " + os.release());
sysInfo.info("TYPE        : " + os.type());
sysInfo.info("VERSION     : " + os.version());
sysInfo.info("UPTIME      : " + os.uptime());



app.setName("FreeDATA");

var appDataFolder = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + "/.config");
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, 'config.json');

// create config folder if not exists
if (!fs.existsSync(configFolder)) {
    fs.mkdirSync(configFolder);
}

// create config file if not exists with defaults
const configDefaultSettings = '{\
                  "tnc_host": "127.0.0.1",\
                  "tnc_port": "3000",\
                  "daemon_host": "127.0.0.1",\
                  "daemon_port": "3001",\
                  "mycall": "AA0AA-0",\
                  "mygrid": "JN40aa",\
                  "deviceid": "RIG_MODEL_DUMMY_NOVFO",\
                  "deviceport": "/dev/ttyACM1",\
                  "serialspeed_direct": "9600",\
                  "spectrum": "waterfall",\
                  "tnclocation": "localhost",\
                  "stop_bits_direct" : "1",\
                  "data_bits_direct" : "8",\
                  "handshake_direct" : "None",\
                  "radiocontrol" : "disabled",\
                  "deviceport_rigctl" : "3",\
                  "deviceid_rigctl" : "3",\
                  "serialspeed_rigctl" : "9600",\
                  "pttprotocol_direct" : "USB",\
                  "pttprotocol_rigctl" : "USB",\
                  "rigctld_port" : "4532",\
                  "rigctld_ip" : "127.0.0.1",\
                  "enable_scatter" : "False",\
                  "enable_fft" : "False",\
                  "low_bandwith_mode" : "False",\
                  "theme" : "default",\
                  "screen_height" : 430,\
                  "screen_width" : 1050,\
                  "update_channel" : "latest",\
                  "beacon_interval" : 5,\
                  "received_files_folder" : "None"\
                  }';

if (!fs.existsSync(configPath)) {
    fs.writeFileSync(configPath, configDefaultSettings)
}

// load settings
var config = require(configPath);

//config validation
// check running config against default config.
// if parameter not exists, add it to running config to prevent errors
sysInfo.info("CONFIG VALIDATION  -----------------------------  ");

var parsedConfig = JSON.parse(configDefaultSettings);
for (key in parsedConfig) {    
    if (config.hasOwnProperty(key)) {
        sysInfo.info("FOUND SETTTING [" + key + "]: " + config[key]);
    } else {
        sysInfo.error("MISSING SETTTING [" + key + "] : " + parsedConfig[key]);
        config[key] = parsedConfig[key];
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));      
    }    
}
sysInfo.info("------------------------------------------  ");





/*
var chatDB = path.join(configFolder, 'chatDB.json')
// create chat database file if not exists
const configContentChatDB = `
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
    fs.writeFileSync(chatDB, configContentChatDB);
}
*/


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






let win = null;
let data = null;
let logViewer = null;
var daemonProcess = null;

function createWindow() {
    win = new BrowserWindow({
        width: config.screen_width,
        height: config.screen_height,
        autoHideMenuBar: true,
        icon: 'src/img/icon.png',
        webPreferences: {
            //preload: path.join(__dirname, 'preload-main.js'),
            preload: require.resolve('./preload-main.js'),
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: false, 
            sandbox: false
            //https://stackoverflow.com/questions/53390798/opening-new-window-electron/53393655 
            //https://github.com/electron/remote
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

    
    logViewer = new BrowserWindow({
        height: 900,
        width: 600,
        show: false,
        parent: win,
        webPreferences: {
            preload: require.resolve('./preload-log.js'),
            nodeIntegration: true,

        }
    })

    logViewer.loadFile('src/log-module.html');
    logViewer.setMenuBarVisibility(false);

    // Emitted when the window is closed.
    logViewer.on('close', function(evt) {
        evt.preventDefault();
        logViewer.hide();
    })







    // Emitted when the window is closed.
    win.on('closed', function() {
        win = null;
        chat = null;
        logViewer = null;
    })
    
    
    win.once('ready-to-show', () => {
    
        log.transports.file.level = "debug"
        autoUpdater.logger = log.scope('updater');
        
        autoUpdater.channel = config.update_channel
        
        autoUpdater.autoInstallOnAppQuit = false;
        autoUpdater.autoDownload = true;
        autoUpdater.checkForUpdatesAndNotify();
        //autoUpdater.quitAndInstall();
    });

    
    chat.on('closed', function () {
           
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
    mainLog.info('Starting freedata-daemon binary');

    if(os.platform()=='darwin'){
        daemonProcess = exec(path.join(process.resourcesPath, 'tnc', 'freedata-daemon'), [], 
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

    /*
    var folder = path.join(process.resourcesPath, 'tnc');
    //var folder = path.join(__dirname, 'extraResources', 'tnc');
    console.log(folder);
    fs.readdir(folder, (err, files) => {
        console.log(files);
    });
    */

        daemonProcess = exec(path.join(process.resourcesPath, 'tnc', 'freedata-daemon'), [], 
            {   
                cwd: path.join(process.resourcesPath, 'tnc'),              
            });        
    }

    
    if(os.platform()=='win32' || os.platform()=='win64'){
        // for windows the relative path via path.join(__dirname) is not needed for some reason 
        //daemonProcess = exec('\\tnc\\daemon.exe', [])
        
        daemonProcess = exec(path.join(process.resourcesPath, 'tnc', 'freedata-daemon.exe'), [], 
            {   
                cwd: path.join(process.resourcesPath, 'tnc'),              
            });
                
    }

    // return process messages
    
    daemonProcess.on('error', (err) => {
      daemonProcessLog.error(`error when starting daemon: ${err}`);
    });
        
    daemonProcess.on('message', (data) => {
      daemonProcessLog.info(`${data}`);
      
    });
    
    daemonProcess.stdout.on('data', (data) => {
      daemonProcessLog.info(`${data}`);

    
    
  win.webContents.send('action-updater', data); 
    });

    daemonProcess.stderr.on('data', (data) => {
      daemonProcessLog.info(`${data}`);

            let arg = {
        entry: `${data}`
      };
        logViewer.webContents.send('action-update-log', arg);
      
      
    });

    daemonProcess.on('close', (code) => {
      daemonProcessLog.warn(`daemonProcess exited with code ${code}`);
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
        mainLog.error(e)
    }
    

    mainLog.warn('closing tnc');
    
    if(os.platform()=='win32' || os.platform()=='win64'){
        exec('Taskkill', ['/IM', 'freedata-tnc.exe', '/F'])
    }
    
    if(os.platform()=='linux'){
        
        exec('pkill', ['-9', 'freedata-tnc'])
        
        // on macOS we need to kill the daemon as well. If we are not doing this, 
        // the daemon wont startup again because the socket is already in use
        //for some reason killing the daemon is killing our screen on Ubuntu..it seems theres another "daemon" out there...
        exec('pkill', ['-9', 'freedata-daemon'])        
    }

    if(os.platform()=='darwin'){

        exec('pkill', ['-9', 'freedata-tnc'])
        
        // on macOS we need to kill the daemon as well. If we are not doing this, 
        // the daemon wont startup again because the socket is already in use
        //for some reason killing the daemon is killing our screen on Ubuntu..it seems theres another "daemon" out there...
        exec('pkill', ['-9', 'freedata-daemon']) 
        
    }
        
    /*
    if (process.platform !== 'darwin') {
        app.quit();
    }
    */
    mainLog.warn('quitting app');
    app.quit();
    
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

/*
ipcMain.on('request-update-rx-msg-buffer', (event, arg) => {
    chat.webContents.send('action-update-rx-msg-buffer', arg);
});
*/
ipcMain.on('request-new-msg-received', (event, arg) => {
    chat.webContents.send('action-new-msg-received', arg);
});

ipcMain.on('request-open-tnc-log', (event) => {
    logViewer.show();
});

//folder selector
ipcMain.on('get-folder-path',(event,data)=>{
    dialog.showOpenDialog({defaultPath: path.join(__dirname, '../assets/'), 
        buttonLabel: 'Select folder', properties: ['openDirectory']}).then(folderPaths => {
            win.webContents.send('return-folder-paths', {path: folderPaths,})              
    });
});

//open folder
ipcMain.on('open-folder',(event,data)=>{
    shell.showItemInFolder(data.path)
});




// LISTENER FOR UPDATER EVENTS
autoUpdater.on('update-available', (info) => {
  mainLog.info('update available');

    let arg = {
        status: "update-available",
        info: info
    };
  win.webContents.send('action-updater', arg);
  
});

autoUpdater.on('update-not-available', (info) => {
  mainLog.info('update not available');
    let arg = {
        status: "update-not-available",
        info: info
    };
  win.webContents.send('action-updater', arg);  
});


autoUpdater.on('update-downloaded', (info) => {
  mainLog.info('update downloaded');
      let arg = {
        status: "update-downloaded",
        info: info
    };
  win.webContents.send('action-updater', arg); 
  // we need to call this at this point. 
  // if an update is available and we are force closing the app
  // the entire screen crashes...
  mainLog.info('quit application and install update');
  autoUpdater.quitAndInstall();

  
});

autoUpdater.on('checking-for-update', () => {
mainLog.info('checking for update');
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

autoUpdater.on('error', (error) => {
    mainLog.info('update error');
    let arg = {
        status: "error",
        progress: error
    };
  win.webContents.send('action-updater', arg); 
});




