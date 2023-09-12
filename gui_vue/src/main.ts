import { createApp, Vue } from 'vue'
import { createPinia } from 'pinia'
import {loadSettings} from './js/settingsHandler'

import './styles.css'


// Import all of Bootstrap's JS
//import * as bootstrap from 'bootstrap'



import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-icons/font/bootstrap-icons.css'




// Import our custom CSS
//import './scss/styles.scss'

import App from './App.vue'
const app = createApp(App)


//.mount('#app').$nextTick(() => postMessage({ payload: 'removeLoading' }, '*'))

const pinia = createPinia()
app.mount('#app')



console.log("init...")
app.use(pinia)
loadSettings()

//import './js/settingsHandler.js'
import './js/daemon.js'
import './js/sock.js'
//import './js/settingsHandler.js'
