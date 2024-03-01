import { app, BrowserWindow, shell, ipcMain } from "electron";
import { release, platform } from "os";
import { join, dirname } from "path";
import { existsSync } from "fs";
import { spawn } from "child_process";

// The built directory structure
//
// ├─┬ dist-electron
// │ ├─┬ main
// │ │ └── index.js    > Electron-Main
// │ └─┬ preload
// │   └── index.js    > Preload-Scripts
// ├─┬ dist
// │ └── index.html    > Electron-Renderer
//
process.env.DIST_ELECTRON = join(__dirname, "..");
process.env.DIST = join(process.env.DIST_ELECTRON, "../dist");
process.env.VITE_PUBLIC = process.env.VITE_DEV_SERVER_URL
  ? join(process.env.DIST_ELECTRON, "../public")
  : process.env.DIST;

// Disable GPU Acceleration for Windows 7
if (release().startsWith("6.1")) app.disableHardwareAcceleration();

// Set application name for Windows 10+ notifications
if (process.platform === "win32") app.setAppUserModelId(app.getName());

if (!app.requestSingleInstanceLock()) {
  close_sub_processes();
  app.quit();
  process.exit(0);
}

// Remove electron security warnings
// This warning only shows in development mode
// Read more on https://www.electronjs.org/docs/latest/tutorial/security
// process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true'

// set daemon process var
var serverProcess = null;
let win: BrowserWindow | null = null;
// Here, you can also use other preload
const preload = join(__dirname, "../preload/index.js");
const url = process.env.VITE_DEV_SERVER_URL;
const indexHtml = join(process.env.DIST, "index.html");

async function createWindow() {
  win = new BrowserWindow({
    title: "FreeDATA",
    width: 1200,
    height: 670,
    icon: join(process.env.VITE_PUBLIC, "icon_cube_border.png"),
    autoHideMenuBar: true,
    webPreferences: {
      preload,
      backgroundThrottling: false,
      // Warning: Enable nodeIntegration and disable contextIsolation is not secure in production
      // Consider using contextBridge.exposeInMainWorld
      // Read more on https://www.electronjs.org/docs/latest/tutorial/context-isolation
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  if (process.env.VITE_DEV_SERVER_URL) {
    // electron-vite-vue#298
    win.loadURL(url);
    // Open devTool if the app is not packaged
    win.webContents.openDevTools();
  } else {
    win.loadFile(indexHtml);
  }

  // Test actively push message to the Electron-Renderer
  win.webContents.on("did-finish-load", () => {
    win?.webContents.send("main-process-message", new Date().toLocaleString());
  });

  // Make all links open with the browser, not with the application
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("https:")) shell.openExternal(url);
    return { action: "deny" };
  });
  // win.webContents.on('will-navigate', (event, url) => { }) #344

  win.once("ready-to-show", () => {
    //
  });
}

//app.whenReady().then(
app.whenReady().then(() => {
  createWindow();

  console.log(platform());
  //Generate daemon binary path
  var serverPath = "";
  console.log(process.env)

  // Attempt to find Installation Folder
  console.log(app.getAppPath())
  console.log(join(app.getAppPath(), '..', '..'))
  var basePath = join(app.getAppPath(), '..', '..') || join(process.env.PWD, '..') || join(process.env.INIT_CWD, '..') || join(process.env.DIST, '..', '..', '..');

  switch (platform().toLowerCase()) {
    //case "darwin":
    //  serverPath = join(process.resourcesPath, "modem", "freedata-server");
    //case "linux":
    //  serverPath = join(process.resourcesPath, "modem", "freedata-server");
    //  break;
    case "win32":
        serverPath = join(basePath, "freedata-server", "freedata-server.exe");

    case "win64":
        serverPath = join(basePath, "freedata-server", "freedata-server.exe");

    break;
    default:
      console.log("Unhandled OS Platform: ", platform());
      break;
  }

  console.log("serverPath:", serverPath);
  //Start server binary if it exists
  if (existsSync(serverPath)) {
    console.log(`Starting server with path: ${serverPath}`);
serverProcess = spawn(serverPath, [], { shell: true });

    serverProcess.on('error', (err) => {
  console.error('Failed to start server process:', err);
});
serverProcess.stdout.on('data', (data) => {
  console.log(`stdout: ${data}`);
});

serverProcess.stderr.on('data', (data) => {
  console.error(`stderr: ${data}`);
});


  } else {
    serverProcess = null;
    serverPath = null;
    console.log("Server binary doesn't exist in setup folder");
  }

  //)
});

app.on("window-all-closed", () => {
  win = null;
  if (process.platform !== "darwin") app.quit();
});

app.on("second-instance", () => {
  if (win) {
    // Focus on the main window if the user tried to open another
    if (win.isMinimized()) win.restore();
    win.focus();
  }
});

app.on("activate", () => {
  const allWindows = BrowserWindow.getAllWindows();
  if (allWindows.length) {
    allWindows[0].focus();
  } else {
    createWindow();
  }
});

// New window example arg: new windows url
ipcMain.handle("open-win", (_, arg) => {
  const childWindow = new BrowserWindow({
    webPreferences: {
      preload,
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  if (process.env.VITE_DEV_SERVER_URL) {
    childWindow.loadURL(`${url}#${arg}`);
  } else {
    childWindow.loadFile(indexHtml, { hash: arg });
  }
});



function close_sub_processes() {
  console.log("closing sub processes");

  // closing the modem binary if not closed when closing application and also our daemon which has been started by the gui
  try {
    if (serverProcess != null) {
      serverProcess.kill();
    }
  } catch (e) {
    console.log(e);
  }

  console.log("closing freedata server process");
  try {
    if (platform() == "win32") {
      spawn("Taskkill", ["/IM", "freedata-server.exe", "/F"]);
    }

    if (platform() == "linux") {
      spawn("pkill", ["-9", "freedata-server"]);
    }

    if (platform() == "darwin") {
      spawn("pkill", ["-9", "freedata-server"]);
    }
  } catch (e) {
    console.log(e);
  }
}
