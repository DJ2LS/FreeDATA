const {app,BrowserWindow,ipcMain} = require('electron')
const path = require('path')
var config = require('./config.json');

let win = null;
let data = null;

function createWindow() {
    win = new BrowserWindow({
        width: 1220,
        height: 920,
        webPreferences: {
            //preload: path.join(__dirname, 'preload-main.js'),
            preload: require.resolve('./preload-main.js'),
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: false, //https://stackoverflow.com/questions/53390798/opening-new-window-electron/53393655 https://github.com/electron/remote
        }
    })
    //open dev tools
    win.webContents.openDevTools({
        mode: 'undocked',
        activate: true,
    })
    win.loadFile('src/index.html')
    /*
    data = new BrowserWindow({
        height: 900,
        width: 600,
        parent: win,
        webPreferences: {
            preload: require.resolve('./preload-data.js'),
            nodeIntegration: true,

        }
    })
    //open dev tools
    data.webContents.openDevTools({
        mode: 'undocked',
        activate: true,
    })
    data.loadFile('src/data-module.html')
    data.hide()
*/

    // Emitted when the window is closed.
    win.on('closed', function() {
        // Dereference the window object, usually you would store windows
        // in an array if your app supports multi windows, this is the time
        // when you should delete the corresponding element.
        win = null;
        data = null;
    })

    /*
        data.on('closed', function () {
            // Dereference the window object, usually you would store windows
            // in an array if your app supports multi windows, this is the time
            // when you should delete the corresponding element.
        })
    */


    // https://stackoverflow.com/questions/44258831/only-hide-the-window-when-closing-it-electron
    /*
    data.on('close', function(evt) {
        evt.preventDefault();
        data.hide()
    });
    */
}


app.whenReady().then(() => {
    createWindow()

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow()
        }
    })
})

app.on('window-all-closed', () => {

    if (process.platform !== 'darwin') {
        app.quit()
    }
})


// IPC HANDLER
 /*
 ipcMain.on('show-data-window', (event, arg) => {
    data.show()
 });
*/
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

ipcMain.on('request-update-daemon-connection', (event, arg) => {
    win.webContents.send('action-update-daemon-connection', arg);
});

ipcMain.on('run-tnc-command', (event, arg) => {
            win.webContents.send('run-tnc-command', arg);
});

ipcMain.on('request-update-rx-buffer', (event, arg) => {
            win.webContents.send('action-update-rx-buffer', arg);
});            