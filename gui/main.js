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
const spawn = require('child_process').spawn;

const log = require('electron-log');
const mainLog = log.scope('main');
const daemonProcessLog = log.scope('freedata-daemon');
const mime = require('mime');
const net = require('net');

  
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
                  "radiocontrol" : "disabled",\
                  "hamlib_deviceid": "RIG_MODEL_DUMMY_NOVFO",\
                  "enable_hamlib_deviceport" : "False",\
                  "hamlib_deviceport": "/dev/ttyACM1",\
                  "enable_hamlib_stop_bits" : "False",\
                  "hamlib_stop_bits" : "1",\
                  "enable_hamlib_data_bits" : "False",\
                  "hamlib_data_bits" : "8",\
                  "enable_hamlib_handshake" : "False",\
                  "hamlib_handshake" : "None",\
                  "enable_hamlib_serialspeed" : "False",\
                  "hamlib_serialspeed" : "9600",\
                  "enable_hamlib_pttprotocol" : "False",\
                  "hamlib_dtrstate" : "OFF",\
                  "enable_hamlib_dtrstate" : "False",\
                  "hamlib_pttprotocol" : "USB",\
                  "enable_hamlib_pttport" : "False",\
                  "hamlib_pttport": "/dev/ttyACM1",\
                  "hamlib_dcd": "None",\
                  "hamlbib_serialspeed_ptt": "9600",\
                  "hamlib_rigctld_port" : "4532",\
                  "hamlib_rigctld_ip" : "127.0.0.1",\
                  "hamlib_rigctld_path" : "",\
                  "hamlib_rigctld_server_port" : "4532",\
                  "spectrum": "waterfall",\
                  "tnclocation": "localhost",\
                  "enable_scatter" : "False",\
                  "enable_fft" : "False",\
                  "enable_fsk" : "False",\
                  "low_bandwidth_mode" : "False",\
                  "theme" : "default",\
                  "screen_height" : 430,\
                  "screen_width" : 1050,\
                  "update_channel" : "latest",\
                  "beacon_interval" : 5,\
                  "received_files_folder" : "None",\
                  "tuning_range_fmin" : "-50.0",\
                  "tuning_range_fmax" : "50.0",\
                  "respond_to_cq" : "True",\
                  "rx_buffer_size" : "16", \
                  "enable_explorer" : "False", \
                  "wftheme": 2 \
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


// create a splash screen
function createSplashScreen(){
    splashScreen = new BrowserWindow({
        height: 250,
        width: 250,
        transparent: true,
        frame: false,
        alwaysOnTop: true
    });
    splashScreen.loadFile('src/splash.html');
    splashScreen.center();
}


function createWindow() {
    win = new BrowserWindow({
        width: config.screen_width,
        height: config.screen_height,
        show: false,
        autoHideMenuBar: true,
        icon: 'src/img/icon.png',
        webPreferences: {
            //preload: path.join(__dirname, 'preload-main.js'),
            backgroundThrottle: false,
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
        height: 600,
        width: 1000,
        show: false,
        //parent: win,
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
        //parent: win,
        webPreferences: {
            preload: require.resolve('./preload-log.js'),
            nodeIntegration: true,

        }
    })

    logViewer.loadFile('src/log-module.html');
    logViewer.setMenuBarVisibility(false);

    // Emitted when the window is closed.
    logViewer.on('close', function(evt) {
        if (logViewer !== null){
        evt.preventDefault();
        logViewer.hide();
        } else {
        this.close()
        }
    })







    // Emitted when the window is closed.
    win.on('closed', function() {
        console.log("closing all windows.....")
        /*
        win = null;
        chat = null;
        logViewer = null;
        */
        close_all();
        
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

    // show splash screen
    createSplashScreen();

    // create main window
    createWindow();

   // wait some time, then close splash screen and show main windows
    setTimeout(function() {
        splashScreen.close();
        win.show();
    }, 3000);

    // start daemon by checking os
    mainLog.info('Starting freedata-daemon binary');

    if(os.platform()=='darwin'){
        daemonProcess = spawn(path.join(process.resourcesPath, 'tnc', 'freedata-daemon'), [],
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

        daemonProcess = spawn(path.join(process.resourcesPath, 'tnc', 'freedata-daemon'), [],
            {   
                cwd: path.join(process.resourcesPath, 'tnc'),              
            });        
    }

    
    if(os.platform()=='win32' || os.platform()=='win64'){
        // for windows the relative path via path.join(__dirname) is not needed for some reason 
        //daemonProcess = exec('\\tnc\\daemon.exe', [])
        
        daemonProcess = spawn(path.join(process.resourcesPath, 'tnc', 'freedata-daemon.exe'), [],
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
    });





    daemonProcess.stderr.on('data', (data) => {
      daemonProcessLog.info(`${data}`);

            let arg = {
        entry: `${data}`
      };
        // send info to log only if log screen available
        // it seems an error occurs when updating
        if (logViewer !== null && logViewer !== ''){
            try{
                logViewer.webContents.send('action-update-log', arg);
            } catch (e) {
                // empty for keeping error stuff silent
                // this is important to avoid error messages if we are going to close the app while
                // an logging information will be pushed to the logger
            }
        }
      
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
    close_all();

})

// IPC HANDLER

ipcMain.on('request-show-chat-window', () => {
    chat.show();
 });

// UPDATE TNC CONNECTION
ipcMain.on('request-update-tnc-ip',(event,data)=>{
    win.webContents.send('action-update-tnc-ip', data);
});

// UPDATE DAEMON CONNECTION
ipcMain.on('request-update-daemon-ip',(event,data)=>{
    win.webContents.send('action-update-daemon-ip', data);
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
ipcMain.on('request-update-transmission-status', (event, arg) => {
    chat.webContents.send('action-update-transmission-status', arg);
});

ipcMain.on('request-open-tnc-log', () => {
    logViewer.show();
});

//file selector
ipcMain.on('get-file-path',(event,data)=>{
    dialog.showOpenDialog({defaultPath: path.join(__dirname, '../'),
        buttonLabel: 'Select rigctld', properties: ['openFile']}).then(filePaths => {
            win.webContents.send('return-file-paths', {path: filePaths,})

    });
});

//folder selector
ipcMain.on('get-folder-path',(event,data)=>{
    dialog.showOpenDialog({defaultPath: path.join(__dirname, '../'), 
        buttonLabel: 'Select folder', properties: ['openDirectory']}).then(folderPaths => {
            win.webContents.send('return-folder-paths', {path: folderPaths,})     

    });
});

//open folder
ipcMain.on('open-folder',(event,data)=>{
    shell.showItemInFolder(data.path)
});

//select file
ipcMain.on('select-file',(event,data)=>{
    dialog.showOpenDialog({defaultPath: path.join(__dirname, '../'), 
        buttonLabel: 'Select file', properties: ['openFile']}).then(filepath => {

console.log(filepath.filePaths[0])

  try {
  //fs.readFile(filepath.filePaths[0], 'utf8',  function (err, data) {
  fs.readFile(filepath.filePaths[0], 'binary', function (err, data) {
  
  console.log(data.length)

    console.log(data)

  var filename = path.basename(filepath.filePaths[0])
  var mimeType = mime.getType(filename)
  console.log(mimeType)
  if (mimeType == '' || mimeType == null){
    mimeType = 'plain/text'
  }
    chat.webContents.send('return-selected-files', {data : data, mime: mimeType, filename: filename}) 
    })
       
  } catch (err) {
    console.log(err);
  }

      });  

});

//save file to folder
ipcMain.on('save-file-to-folder',(event,data)=>{

       console.log(data.file)
        
        dialog.showSaveDialog({defaultPath: data.filename}).then(filepath => {

        console.log(filepath.filePath)
        console.log(data.file)        

              try {

                let buffer = Buffer.from(data.file);
                let arraybuffer = Uint8Array.from(buffer);
                console.log(arraybuffer)
               fs.writeFile(filepath.filePath, data.file, 'binary', function (err, data) {
                //fs.writeFile(filepath.filePath, arraybuffer,  function (err, data) {
              //fs.writeFile(filepath.filePath, arraybuffer, 'binary', function(err) {
              //fs.writeFile(filepath.filePath, new Uint8Array(Buffer.from(data.file)),  function (err, data) {
              //fs.writeFile(filepath.filePath, Buffer.from(data.file),  function (err, data) {
                })
              } catch (err) {
                console.log(err);
              }

      });  
      
      
      
});



//tnc messages START --------------------------------------

// CQ TRANSMITTING
ipcMain.on('request-show-cq-toast-transmitting',(event,data)=>{
    win.webContents.send('action-show-cq-toast-transmitting', data);
});

// CQ RECEIVED
ipcMain.on('request-show-cq-toast-received',(event,data)=>{
    win.webContents.send('action-show-cq-toast-received', data);
});

// QRV TRANSMITTING
ipcMain.on('request-show-qrv-toast-transmitting',(event,data)=>{
    win.webContents.send('action-show-qrv-toast-transmitting', data);
});

// QRV RECEIVED
ipcMain.on('request-show-qrv-toast-received',(event,data)=>{
    win.webContents.send('action-show-qrv-toast-received', data);
});

// BEACON TRANSMITTING
ipcMain.on('request-show-beacon-toast-transmitting',(event,data)=>{
    win.webContents.send('action-show-beacon-toast-transmitting', data);
});

// BEACON RECEIVED
ipcMain.on('request-show-beacon-toast-received',(event,data)=>{
    win.webContents.send('action-show-beacon-toast-received', data);
});

// PING TRANSMITTING
ipcMain.on('request-show-ping-toast-transmitting',(event,data)=>{
    win.webContents.send('action-show-ping-toast-transmitting', data);
});

// PING RECEIVED
ipcMain.on('request-show-ping-toast-received',(event,data)=>{
    win.webContents.send('action-show-ping-toast-received', data);
});

// PING RECEIVED ACK
ipcMain.on('request-show-ping-toast-received-ack',(event,data)=>{
    win.webContents.send('action-show-ping-toast-received-ack', data);
});

// ARQ DATA CHANNEL OPENING
ipcMain.on('request-show-arq-toast-datachannel-opening',(event,data)=>{
    win.webContents.send('action-show-arq-toast-datachannel-opening', data);
});

// ARQ DATA CHANNEL WAITING
ipcMain.on('request-show-arq-toast-datachannel-waiting',(event,data)=>{
    win.webContents.send('action-show-arq-toast-datachannel-waiting', data);
});


// ARQ DATA CHANNEL OPEN
ipcMain.on('request-show-arq-toast-datachannel-opened',(event,data)=>{
    win.webContents.send('action-show-arq-toast-datachannel-opened', data);
});

// ARQ DATA RECEIVED OPENER
ipcMain.on('request-show-arq-toast-datachannel-received-opener',(event,data)=>{
    win.webContents.send('action-show-arq-toast-datachannel-received-opener', data);
});

// ARQ TRANSMISSION FAILED
ipcMain.on('request-show-arq-toast-transmission-failed',(event,data)=>{
    win.webContents.send('action-show-arq-toast-transmission-failed', data);
});

// ARQ TRANSMISSION RECEIVING
ipcMain.on('request-show-arq-toast-transmission-receiving',(event,data)=>{
    win.webContents.send('action-show-arq-toast-transmission-receiving', data);
});

// ARQ TRANSMISSION RECEIVED
ipcMain.on('request-show-arq-toast-transmission-received',(event,data)=>{
    win.webContents.send('action-show-arq-toast-transmission-received', data);
});

// ARQ TRANSMISSION TRANSMITTING
ipcMain.on('request-show-arq-toast-transmission-transmitting',(event,data)=>{
    win.webContents.send('action-show-arq-toast-transmission-transmitting', data);
});

// ARQ TRANSMISSION TRANSMITTED
ipcMain.on('request-show-arq-toast-transmission-transmitted',(event,data)=>{
    win.webContents.send('action-show-arq-toast-transmission-transmitted', data);
});

// ARQ SESSION CONNECTING
ipcMain.on('request-show-arq-toast-session-connecting',(event,data)=>{
    win.webContents.send('action-show-arq-toast-session-connecting', data);
});

// ARQ SESSION WAITING
ipcMain.on('request-show-arq-toast-session-waiting',(event,data)=>{
    win.webContents.send('action-show-arq-toast-session-waiting', data);
});

// ARQ SESSION CONNECTED
ipcMain.on('request-show-arq-toast-session-connected',(event,data)=>{
    win.webContents.send('action-show-arq-toast-session-connected', data);
});

// ARQ SESSION CLOSE
ipcMain.on('request-show-arq-toast-session-close',(event,data)=>{
    win.webContents.send('action-show-arq-toast-session-close', data);
});

// ARQ SESSION FAILED
ipcMain.on('request-show-arq-toast-session-failed',(event,data)=>{
    win.webContents.send('action-show-arq-toast-session-failed', data);
});



//tnc messages END --------------------------------------

//restart and install udpate
ipcMain.on('request-restart-and-install',(event,data)=>{
    close_sub_processes()
    autoUpdater.quitAndInstall();
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
  //mainLog.info('quit application and install update');
  //autoUpdater.quitAndInstall();

  
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
  mainLog.error("AUTO UPDATER : " + error);
});



function close_sub_processes(){
    mainLog.warn('closing sub processes');

    // closing the tnc binary if not closed when closing application and also our daemon which has been started by the gui
    try {
        daemonProcess.kill();
    } catch (e) {   
        mainLog.error(e)
    }
    

    mainLog.warn('closing tnc and daemon');
    try {
    
        if(os.platform()=='win32' || os.platform()=='win64'){
            spawn('Taskkill', ['/IM', 'freedata-tnc.exe', '/F'])
            spawn('Taskkill', ['/IM', 'freedata-daemon.exe', '/F'])
        }
        
        if(os.platform()=='linux'){
            
            spawn('pkill', ['-9', 'freedata-tnc'])
            spawn('pkill', ['-9', 'freedata-daemon'])
        }

        if(os.platform()=='darwin'){

            spawn('pkill', ['-9', 'freedata-tnc'])
            spawn('pkill', ['-9', 'freedata-daemon'])
            
        }
    } catch (e) {
        mainLog.error(e)
    }

};


function close_all() {

    // function for closing the application with closing all used processes

    close_sub_processes();
    
    mainLog.warn('quitting app');
    
    win.destroy();
    chat.destroy();
    logViewer.destroy();
    
    app.quit();
}


// RUN RIGCTLD
ipcMain.on('request-start-rigctld',(event, data)=>{

    try{
        let rigctld_proc = spawn(data.path, data.parameters);

        rigctld_proc.on('exit', function (code) {
            console.log('rigctld process exited with code ' + code);

            // if rigctld crashes, error code is -2
            // then we are going to restart rigctld
            // this "fixes" a problem with latest rigctld on raspberry pi
            //if (code == -2){
            //    setTimeout(ipcRenderer.send('request-start-rigctld', data), 500);
            //}
            //let rigctld_proc = spawn(data.path, data.parameters);
        });
    } catch (e) {
     console.log(e);
    }

    /*
    const rigctld = exec(data.path, data.parameters);
    rigctld.stdout.on("data", data => {
        console.log(`stdout: ${data}`);
    });
    */


});


// STOP RIGCTLD
ipcMain.on('request-stop-rigctld',(event,data)=>{
    mainLog.warn('closing rigctld');
    try {

        if(os.platform()=='win32' || os.platform()=='win64'){
            spawn('Taskkill', ['/IM', 'rigctld.exe', '/F'])
        }

        if(os.platform()=='linux'){

            spawn('pkill', ['-9', 'rigctld'])

        }

        if(os.platform()=='darwin'){

            spawn('pkill', ['-9', 'rigctld'])

        }
    } catch (e) {
        mainLog.error(e)
    }
});



// CHECK RIGCTLD CONNECTION
// create new socket so we are not reopening every time a new one
var rigctld_connection = new net.Socket();
var rigctld_connection_state = false;
ipcMain.on('request-check-rigctld',(event, data)=>{

    try{

        let Data = {
                state: "unknown",
        };

        if(!rigctld_connection_state){
            rigctld_connection = new net.Socket();
            rigctld_connection.connect(data.port, data.ip)
        }

        // check if we have created a new socket object
        if (typeof(rigctld_connection) != 'undefined') {

        rigctld_connection.on('connect', function() {
            rigctld_connection_state = true;
            Data["state"] = "connection possible - (" + data.ip + ":" + data.port + ")";
            if (win !== null && win !== '' && typeof(win) != 'undefined'){
                // try catch for being sure we have a clean app close
                try{
                    win.webContents.send('action-check-rigctld', Data);
                } catch(e){
                    console.log(e)
                }
            }
        })

        rigctld_connection.on('error', function() {
            rigctld_connection_state = false;
            Data["state"] = "unknown/stopped - (" + data.ip + ":" + data.port + ")";
            if (win !== null && win !== '' && typeof(win) != 'undefined'){
                // try catch for being sure we have a clean app close
                try{
                    win.webContents.send('action-check-rigctld', Data);
                } catch(e){
                    console.log(e)
                }
            }
        })

        rigctld_connection.on('end', function() {
            rigctld_connection_state = false;
        })

        }

    } catch(e) {
        console.log(e)
    }

});
