function domReady(condition: DocumentReadyState[] = ['complete', 'interactive']) {
  return new Promise(resolve => {
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
      parent.appendChild(child)
    }
  },
  remove(parent: HTMLElement, child: HTMLElement) {
    if (Array.from(parent.children).find(e => e === child)) {
      parent.removeChild(child)
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
  animation: square-spin 3s 0s cubic-bezier(0.09, 0.57, 0.49, 0.9) infinite;
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

window.onmessage = ev => {
  ev.data.payload === 'removeLoading' && removeLoading()
}

setTimeout(removeLoading, 3000)



import { autoUpdater } from 'electron-updater';
autoUpdater.channel = settings.update_channel;
autoUpdater.autoInstallOnAppQuit = false;
autoUpdater.autoDownload = true;
autoUpdater.checkForUpdatesAndNotify();


// LISTENER FOR UPDATER EVENTS
autoUpdater.on("update-available", (info) => {
  console.log("update available");
});

autoUpdater.on("update-not-available", (info) => {
  console.log("update not available");
});

autoUpdater.on("update-downloaded", (info) => {
  console.log("update downloaded");
  // we need to call this at this point.
  // if an update is available and we are force closing the app
  // the entire screen crashes...
  //console.log('quit application and install update');
  //autoUpdater.quitAndInstall();
});

autoUpdater.on("checking-for-update", () => {
  console.log("checking for update");
});

autoUpdater.on("download-progress", (progress) => {

});

autoUpdater.on("error", (error) => {
  console.log("update error");
});