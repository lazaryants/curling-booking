<template>
  <div class="login-container">
    <div class="login-box">
      <h2>Вход в систему</h2>
      
      <form @submit.prevent="login">
        <div class="form-group">
          <label for="email">Email</label>
          <input 
            type="email" 
            id="email" 
            v-model="email" 
            required 
            placeholder="Введите email"
          >
        </div>
        
        <div class="form-group">
          <label for="password">Пароль</label>
          <input 
            type="password" 
            id="password" 
            v-model="password" 
            required 
            placeholder="Введите пароль"
          >
        </div>
        
        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
        
        <p class="register-link">
          Нет аккаунта? 
          <router-link to="/register">Зарегистрироваться</router-link>
        </p>
      </form>
      
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import { store } from '../store/store'

export default {
  data() {
    return {
      email: '',
      password: '',
      loading: false,
      error: null
    }
  },
  methods: {
    async login() {
      this.loading = true
      this.error = null
      
      try {
        const response = await api.post('/login', {
          email: this.email,
          password: this.password
        })
        
        store.setToken(response.data.access_token)
        store.setUser(response.data.user)
        
        // Небольшая задержка для уверенности
        setTimeout(() => {
          this.$router.push('/profile')
        }, 100)
      } catch (error) {
        this.error = error.response?.data?.detail || 'Ошибка входа'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>


<style src="../styles/LoginView.css" scoped></style>
