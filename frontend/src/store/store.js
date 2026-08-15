import { reactive } from 'vue'

// Безопасный доступ к localStorage
const safeLocalStorage = {
  getItem(key) {
    try {
      return localStorage.getItem(key)
    } catch (e) {
      console.warn('localStorage недоступен:', e)
      return null
    }
  },
  setItem(key, value) {
    try {
      localStorage.setItem(key, value)
    } catch (e) {
      console.warn('localStorage недоступен:', e)
    }
  },
  removeItem(key) {
    try {
      localStorage.removeItem(key)
    } catch (e) {
      console.warn('localStorage недоступен:', e)
    }
  }
}

export const store = reactive({
  user: null,
  token: null,
  
  setUser(user) {
    this.user = user
    safeLocalStorage.setItem('user', JSON.stringify(user))
  },
  
  setToken(token) {
    this.token = token
    safeLocalStorage.setItem('access_token', token)
  },
  
  logout() {
    this.user = null
    this.token = null
    safeLocalStorage.removeItem('access_token')
    safeLocalStorage.removeItem('user')
  },
  
  isAuthenticated() {
    return !!this.token && !!this.user
  },
  
  isAdmin() {
    return this.user?.role === 'admin'
  },
  
  loadFromStorage() {
    const savedToken = safeLocalStorage.getItem('access_token')
    const savedUser = safeLocalStorage.getItem('user')
    
    if (savedToken) {
      this.token = savedToken
    }
    
    if (savedUser) {
      try {
        this.user = JSON.parse(savedUser)
      } catch (e) {
        console.error('Ошибка загрузки пользователя:', e)
        this.logout()
      }
    }
  }
})

// Загружаем данные при инициализации
store.loadFromStorage()
