<template>
  <div class="register-container">
    <div class="register-form">
      <h2>Регистрация</h2>
      <form @submit.prevent="register">
        <div class="form-group">
          <label for="name">Имя *</label>
          <input type="text" id="name" v-model="formData.name" required placeholder="Введите ваше имя" />
        </div>
        <div class="form-group">
          <label for="email">Email *</label>
          <input type="email" id="email" v-model="formData.email" required placeholder="Введите ваш email" />
        </div>
        <div class="form-group">
          <label for="phone">Телефон</label>
          <input type="tel" id="phone" v-model="formData.phone" placeholder="Введите ваш телефон (необязательно)" />
        </div>
        <div class="form-group">
          <label for="password">Пароль *</label>
          <input type="password" id="password" v-model="formData.password" required placeholder="Введите пароль" />
        </div>
        <div class="form-group">
          <label for="confirmPassword">Подтвердите пароль *</label>
          <input type="password" id="confirmPassword" v-model="formData.confirmPassword" required placeholder="Подтвердите пароль" />
        </div>
        <button type="submit" class="register-btn">Зарегистрироваться</button>
        <p class="login-link">
          Уже есть аккаунт? <router-link to="/login">Войти</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import { dialog } from '../services/dialog'

export default {
  data() {
    return {
      formData: {
        name: '',
        email: '',
        phone: '',
        password: '',
        confirmPassword: ''
      }
    }
  },
  methods: {
    async register() {
      if (this.formData.password !== this.formData.confirmPassword) {
        dialog.error('Пароли не совпадают')
        return
      }
      if (this.formData.password.length < 6) {
        dialog.error('Пароль должен содержать не менее 6 символов')
        return
      }
      try {
        await api.post('/register', {
          name: this.formData.name,
          email: this.formData.email,
          phone: this.formData.phone || null,
          password: this.formData.password
        })
        await dialog.success(
          'Регистрация успешна! Теперь вы можете войти.',
          {
            title: 'Регистрация завершена'
          }
        )
        this.$router.push('/login')
      } catch (error) {
        const detail = error.response?.data?.detail
        dialog.error(detail || 'Ошибка регистрации')
      }
    }
  }
}
</script>


<style src="../styles/RegisterView.css" scoped></style>
