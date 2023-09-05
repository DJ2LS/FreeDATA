import { app, BrowserWindow, ipcMain } from 'electron'
import path from 'node:path'


//import { useIpcRenderer } from '@vueuse/electron'
//const ipcRenderer = useIpcRenderer()



process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true'

// The built directory structure
//
// ├─┬─┬ dist
// │ │ └── index.html
// │ │
// │ ├─┬ dist-electron
// │ │ ├── main.js
// │ │ └── preload.js
// │
process.env.DIST = path.join(__dirname, '../dist')
process.env.PUBLIC = app.isPackaged ? process.env.DIST : path.join(process.env.DIST, '../public')


let win: BrowserWindow | null
// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']

function createWindow() {
  win = new BrowserWindow({
    icon: path.join(process.env.PUBLIC, 'icon_cube_border.png'),
    //webPreferences: {
    //  preload: path.join(__dirname, 'preload.js'),
    //},
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      //preload: path.join(__dirname, 'preload-main.js'),
      backgroundThrottle: false,
      //preload: require.resolve("preload-main.js"),
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: false,
      sandbox: false,
      //https://stackoverflow.com/questions/53390798/opening-new-window-electron/53393655
      //https://github.com/electron/remote
    },
  })

  win.setMenuBarVisibility(false);


  // Test active push message to Renderer-process.
  win.webContents.on('did-finish-load', () => {
    win?.webContents.send('main-process-message', (new Date).toLocaleString())
  })

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL)
  } else {
    // win.loadFile('dist/index.html')
    win.loadFile(path.join(process.env.DIST, 'index.html'))
  }
}

app.on('window-all-closed', () => {
  win = null
})

app.whenReady().then(createWindow)
