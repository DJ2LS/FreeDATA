import { createApp } from 'vue'
import './styles.css'


// Import all of Bootstrap's JS
//import * as bootstrap from 'bootstrap'



import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-icons/font/bootstrap-icons.css'


// Import our custom CSS
//import './scss/styles.scss'






import App from './App.vue'

createApp(App).mount('#app').$nextTick(() => postMessage({ payload: 'removeLoading' }, '*'))
