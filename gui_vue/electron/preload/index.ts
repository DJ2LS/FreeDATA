import { ipcRenderer } from "electron"
import { autoUpdater } from "electron-updater"



function domReady(condition: DocumentReadyState[] = ['complete', 'interactive']) {
  return new Promise((resolve) => {
    if (condition.includes(document.readyState)) {
      resolve(true)
    } else {
      document.addEventListener('readystatechange', () => {
        if (condition.includes(document.readyState)) {
          resolve(true)
        }
      })
    }
  })
}

const safeDOM = {
  append(parent: HTMLElement, child: HTMLElement) {
    if (!Array.from(parent.children).find(e => e === child)) {
      return parent.appendChild(child)
    }
  },
  remove(parent: HTMLElement, child: HTMLElement) {
    if (Array.from(parent.children).find(e => e === child)) {
      return parent.removeChild(child)
    }
  },
}

/**
 * https://tobiasahlin.com/spinkit
 * https://connoratherton.com/loaders
 * https://projects.lukehaas.me/css-loaders
 * https://matejkustec.github.io/SpinThatShit
 */
function useLoading() {
  const className = `loaders-css__square-spin`
  const styleContent = `
@keyframes square-spin {
  0% {
    transform: rotate(0deg);
    background-image: url('icon_cube_border.png'); /* Replace with the URL of your image */
    background-size: cover; /* Scale the image to cover the entire container */
  }
  25% { transform: perspective(100px) rotateX(180deg) rotateY(0);
    background-image: url('icon_cube_border.png'); /* Replace with the URL of your image */
    background-size: cover; /* Scale the image to cover the entire container */
   }

  50% { transform: perspective(100px) rotateX(180deg) rotateY(180deg);
    background-image: url('icon_cube_border.png'); /* Replace with the URL of your image */
    background-size: cover; /* Scale the image to cover the entire container */
  }
  75% { transform: perspective(100px) rotateX(0) rotateY(180deg);
    background-image: url('icon_cube_border.png'); /* Replace with the URL of your image */
    background-size: cover; /* Scale the image to cover the entire container */
  }
  100% { transform: perspective(100px) rotateX(0) rotateY(0);
    background-image: url('icon_cube_border.png'); /* Replace with the URL of your image */
    background-size: cover; /* Scale the image to cover the entire container */
  }
}
.${className} > div {
  animation-fill-mode: both;
  width: 50px;
  height: 50px;
  background: #fff;
  animation: square-spin 6s 0s cubic-bezier(0.09, 0.57, 0.49, 0.9) infinite;
}
.app-loading-wrap {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #282c34;
  z-index: 99999;
}
    `
  const oStyle = document.createElement('style')
  const oDiv = document.createElement('div')

  oStyle.id = 'app-loading-style'
  oStyle.innerHTML = styleContent
  oDiv.className = 'app-loading-wrap'
  oDiv.innerHTML = `<div class="${className}"><div></div></div>`

  return {
    appendLoading() {
      safeDOM.append(document.head, oStyle)
      safeDOM.append(document.body, oDiv)
    },
    removeLoading() {
      safeDOM.remove(document.head, oStyle)
      safeDOM.remove(document.body, oDiv)
    },
  }
}

// ----------------------------------------------------------------------

const { appendLoading, removeLoading } = useLoading()
domReady().then(appendLoading)


window.onmessage = (ev) => {
  ev.data.payload === 'removeLoading' && removeLoading()
}

setTimeout(removeLoading, 4999)





window.addEventListener("DOMContentLoaded", () => {
    // we are using this area for implementing the electron runUpdater
    // we need access to DOM for displaying updater results in GUI
      // close app, update and restart
  document
    .getElementById("update_and_install")
    .addEventListener("click", () => {
      ipcRenderer.send("request-restart-and-install-update");
    });

})


// IPC ACTION FOR AUTO UPDATER
ipcRenderer.on("action-updater", (event, arg) => {
  if (arg.status == "download-progress") {
    var progressinfo =
      "(" +
      Math.round(arg.progress.transferred / 1024) +
      "kB /" +
      Math.round(arg.progress.total / 1024) +
      "kB)" +
      " @ " +
      Math.round(arg.progress.bytesPerSecond / 1024) +
      "kByte/s";
    document.getElementById("UpdateProgressInfo").innerHTML = progressinfo;

    document
      .getElementById("UpdateProgressBar")
      .setAttribute("aria-valuenow", arg.progress.percent);
    document
      .getElementById("UpdateProgressBar")
      .setAttribute("style", "width:" + arg.progress.percent + "%;");
  }

  if (arg.status == "checking-for-update") {
    //document.title = document.title + ' - v' + arg.version;
    updateTitle(
      config.myCall,
      config.tnc_host,
      config.tnc_port,
      " -v " + arg.version,
    );
    document.getElementById("updater_status").innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';

    document.getElementById("updater_status").className =
      "btn btn-secondary btn-sm";
    document.getElementById("update_and_install").style.display = "none";
  }
  if (arg.status == "update-downloaded") {
    document.getElementById("update_and_install").removeAttribute("style");
    document.getElementById("updater_status").innerHTML =
      '<i class="bi bi-cloud-download ms-1 me-1" style="color: white;"></i>';
    document.getElementById("updater_status").className =
      "btn btn-success btn-sm";

    // HERE WE NEED TO RUN THIS SOMEHOW...
    //mainLog.info('quit application and install update');
    //autoUpdater.quitAndInstall();
  }
  if (arg.status == "update-not-available") {
    document.getElementById("updater_status").innerHTML =
      '<i class="bi bi-check2-square ms-1 me-1" style="color: white;"></i>';
    document.getElementById("updater_status").className =
      "btn btn-success btn-sm";
    document.getElementById("update_and_install").style.display = "none";
  }
  if (arg.status == "update-available") {
    document.getElementById("updater_status").innerHTML =
      '<i class="bi bi-hourglass-split ms-1 me-1" style="color: white;"></i>';
    document.getElementById("updater_status").className =
      "btn btn-warning btn-sm";
    document.getElementById("update_and_install").style.display = "none";
  }

  if (arg.status == "error") {
    document.getElementById("updater_status").innerHTML =
      '<i class="bi bi-exclamation-square ms-1 me-1" style="color: white;"></i>';
    document.getElementById("updater_status").className =
      "btn btn-danger btn-sm";
    document.getElementById("update_and_install").style.display = "none";
  }
});
