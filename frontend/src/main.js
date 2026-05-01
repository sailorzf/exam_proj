// frontend/src/main.js
import { createApp } from 'vue'
import router from './router'

const app = createApp({ template: '<router-view />' })
app.use(router)
app.mount('#app')
