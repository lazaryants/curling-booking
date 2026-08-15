import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { store } from './store/store'
import './styles/variables.css'  // ← Используем переменные
import './styles/global.css'     // ← Единый клеточный фон

const app = createApp(App)
app.use(router)
app.mount('#app')
