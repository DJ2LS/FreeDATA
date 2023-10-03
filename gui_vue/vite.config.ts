import { defineConfig } from 'vite'
import electron from 'vite-plugin-electron'
import renderer from 'vite-plugin-electron-renderer'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
server: {
    open: true,
    port: 5173,
  },
build: {
        minify: false
    },
  plugins: [
    vue(),
    electron([

      {
        // Main-Process entry file of the Electron App.
        entry: 'electron/main.ts',
      },
      /*
      {
        // Daemon-Process entry file of the Electron App.
        entry: 'electron/sock.js',
      },
      {
        // Daemon-Process entry file of the Electron App.
        entry: 'electron/daemon.js',
      },
            {
        // Daemon-Process entry file of the Electron App.
        entry: 'electron/freedata.js',
      },
      {
        entry: 'electron/preload-main.js',
        onstart(options) {
          // Notify the Renderer-Process to reload the page when the Preload-Scripts build is complete,
          // instead of restarting the entire Electron App.
          options.reload()
        },
      },
      */
      {
        entry: 'electron/preload.ts',
        onstart(options) {
          // Notify the Renderer-Process to reload the page when the Preload-Scripts build is complete,
          // instead of restarting the entire Electron App.
          options.reload()

        },

      },

    ],


    ),
    renderer(),
  ],
})
