import '../styles/global.css'
import '../styles/variables.css'
import '../styles/reset.css'
import '../styles/inputs.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(router)

app.mount('#app')