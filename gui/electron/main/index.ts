import { app, BrowserWindow, shell, ipcMain } from "electron";
import { release, platform } from "node:os";
import { join } from "node:path";
import { autoUpdater } from "electron-updater";
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
var daemonProcess = null;
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
      backgroundThrottle: false,

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
    //autoUpdater.logger = log.scope("updater");
    //autoUpdater.channel = config.update_channel;
    autoUpdater.autoInstallOnAppQuit = false;
    autoUpdater.autoDownload = true;
    autoUpdater.checkForUpdatesAndNotify();
    //autoUpdater.quitAndInstall();
  });
}

//app.whenReady().then(
app.whenReady().then(() => {
  createWindow();

  //Generate daemon binary path
  var daemonPath = "";
  switch (platform().toLowerCase()) {
    case "darwin":
    case "linux":
      daemonPath = join(process.resourcesPath, "modem", "freedata-daemon");

      break;
    case "win32":
    case "win64":
      daemonPath = join(process.resourcesPath, "modem", "freedata-daemon.exe");
      break;
    default:
      console.log("Unhandled OS Platform: ", platform());
      break;
  }

  //Start daemon binary if it exists
  if (existsSync(daemonPath)) {
    console.log("Starting freedata-daemon binary");
    daemonProcess = spawn(daemonPath, [], {
      cwd: join(daemonPath, ".."),
    });
    // return process messages
    daemonProcess.on("error", (err) => {
      // daemonProcessLog.error(`error when starting daemon: ${err}`);
    });
    daemonProcess.on("message", (data) => {
      // daemonProcessLog.info(`${data}`);
    });
    daemonProcess.stdout.on("data", (data) => {
      // daemonProcessLog.info(`${data}`);
    });
    daemonProcess.stderr.on("data", (data) => {
      // daemonProcessLog.info(`${data}`);
      let arg = {
        entry: `${data}`,
      };
    });
    daemonProcess.on("close", (code) => {
      // daemonProcessLog.warn(`daemonProcess exited with code ${code}`);
    });
  } else {
    daemonProcess = null;
    daemonPath = null;
    console.log("Daemon binary doesn't exist--normal for dev environments.");
  }

  //)
});

app.on("window-all-closed", () => {
  win = null;
  if (process.platform !== "darwin") app.quit(close_sub_processes());
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

//restart and install udpate
ipcMain.on("request-restart-and-install-update", (event, data) => {
  close_sub_processes();
  autoUpdater.quitAndInstall();
});

// LISTENER FOR UPDATER EVENTS
autoUpdater.on("update-available", (info) => {
  console.log("update available");

  let arg = {
    status: "update-available",
    info: info,
  };
  win.webContents.send("action-updater", arg);
});

autoUpdater.on("update-not-available", (info) => {
  console.log("update not available");
  let arg = {
    status: "update-not-available",
    info: info,
  };
  win.webContents.send("action-updater", arg);
});

autoUpdater.on("update-downloaded", (info) => {
  console.log("update downloaded");
  let arg = {
    status: "update-downloaded",
    info: info,
  };
  win.webContents.send("action-updater", arg);
  // we need to call this at this point.
  // if an update is available and we are force closing the app
  // the entire screen crashes...
  //console.log('quit application and install update');
  //autoUpdater.quitAndInstall();
});

autoUpdater.on("checking-for-update", () => {
  console.log("checking for update");
  let arg = {
    status: "checking-for-update",
    version: app.getVersion(),
  };
  win.webContents.send("action-updater", arg);
});

autoUpdater.on("download-progress", (progress) => {
  let arg = {
    status: "download-progress",
    progress: progress,
  };
  win.webContents.send("action-updater", arg);
});

autoUpdater.on("error", (error) => {
  console.log("update error");
  let arg = {
    status: "error",
    progress: error,
  };
  win.webContents.send("action-updater", arg);
  console.log("AUTO UPDATER : " + error);
});

function close_sub_processes() {
  console.log("closing sub processes");

  // closing the modem binary if not closed when closing application and also our daemon which has been started by the gui
  try {
    if (daemonProcess != null) {
      daemonProcess.kill();
    }
  } catch (e) {
    console.log(e);
  }

  console.log("closing modem and daemon");
  try {
    if (platform() == "win32" || platform() == "win64") {
      spawn("Taskkill", ["/IM", "freedata-modem.exe", "/F"]);
      spawn("Taskkill", ["/IM", "freedata-daemon.exe", "/F"]);
    }

    if (platform() == "linux") {
      spawn("pkill", ["-9", "freedata-modem"]);
      spawn("pkill", ["-9", "freedata-daemon"]);
    }

    if (platform() == "darwin") {
      spawn("pkill", ["-9", "freedata-modem"]);
      spawn("pkill", ["-9", "freedata-daemon"]);
    }
  } catch (e) {
    console.log(e);
  }
}
