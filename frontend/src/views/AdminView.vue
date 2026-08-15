<template>
  <div class="admin-container">
    <div class="admin-header">
      <h1>Админ-панель</h1>
      <p>Управление пользователями и бронированиями</p>
    </div>
    
    <div class="admin-tabs">
      <button 
        :class="{ active: activeTab === 'users' }"
        @click="activeTab = 'users'"
      >
        Пользователи
      </button>
      <button 
        :class="{ active: activeTab === 'bookings' }"
        @click="activeTab = 'bookings'"
      >
        Все бронирования
      </button>
    </div>
    
    <div v-if="activeTab === 'users'" class="users-management">
      <div class="users-header">
        <h2 class="section-title">Список пользователей</h2>
        <button @click="showCreateUserModal" class="btn btn-primary create-user-btn">
          Создать пользователя
        </button>
      </div>
      
      <div v-if="loadingUsers" class="loading">Загрузка...</div>
      
      <div v-else class="users-list">
        <div class="user-card card" v-for="user in users" :key="user.id">
          <div class="user-header">
            <div class="user-title">
              <strong>{{ user.name }}</strong>
              <div :class="['user-role', user.role]">
                {{ user.role === 'admin' ? 'Администратор' : 'Пользователь' }}
              </div>
            </div>
            <div class="user-actions">
              <button @click="showUserDetails(user)" class="btn btn-primary">Подробнее</button>
              <button 
                v-if="user.role !== 'admin' || (user.role === 'admin' && user.id !== store.user?.id)"
                @click="deleteUser(user)"
                class="btn btn-secondary"
                :disabled="user.id === store.user?.id"
              >
                Удалить
              </button>
            </div>
          </div>
          <div class="user-info">
            <div><strong>Email:</strong> {{ user.email }}</div>
            <div v-if="user.phone"><strong>Телефон:</strong> {{ user.phone }}</div>
            <div><strong>Зарегистрирован:</strong> {{ formatDate(user.created_at) }}</div>
            <div v-if="user.last_login"><strong>Последний вход:</strong> {{ formatDate(user.last_login) }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else-if="activeTab === 'bookings'" class="bookings-management">
      <h2 class="section-title">Все бронирования</h2>
      
      <div class="filters">
        <input 
          type="date" 
          v-model="filterDate" 
          @change="loadAllBookings"
          placeholder="Фильтр по дате"
        >
        <select v-model="filterStatus" @change="loadAllBookings">
          <option value="">Все статусы</option>
          <option value="pending">Ожидает подтверждения</option>
          <option value="confirmed">Подтверждённые</option>
          <option value="cancelled_by_user">Отменённые пользователем</option>
          <option value="cancelled_by_admin">Отменённые администратором</option>
          <option value="rejected_by_admin">Отклонённые администратором</option>
          <option value="completed">Завершённые</option>
        </select>
        <button @click="resetFilters" class="btn btn-secondary">Сбросить</button>
      </div>
      
      <div v-if="loadingBookings" class="loading">Загрузка...</div>
      
      <div v-else-if="allBookings.length === 0" class="no-data">
        Нет бронирований
      </div>
      
      <div v-else class="bookings-list">
        <!-- Группировка по датам -->
        <div v-for="(group, date) in groupedBookings" :key="date" class="date-group">
          <h3 class="date-header">{{ formatDate(date) }}</h3>
          <div class="booking-cards">
            <div class="booking-card card" :class="booking.status" v-for="booking in group" :key="booking.id">
              <div class="booking-header">
                <span class="booking-date">{{ formatDate(booking.booking_date) }}</span>
                <span class="booking-status" :class="booking.status">
                  {{ statusText(booking.status) }}
                </span>
              </div>
              <div class="booking-details">
                <div class="booking-info">
                  <strong>Дорожка:</strong> {{ booking.lane_name }}
                </div>
                <div class="booking-info">
                  <strong>Время:</strong> {{ formatTime(booking.start_time) }} - {{ formatTime(booking.end_time) }}
                </div>
                <div class="booking-info">
                  <strong>Пользователь:</strong> 
                  <span v-if="booking.user_id">{{ booking.user_name }} ({{ booking.user_phone }})</span>
                  <span v-else>Гость</span>
                </div>
              </div>
              <div class="booking-actions">
                <button 
                  v-if="booking.status === 'pending' && !isPastBooking(booking)"
                  @click="confirmBooking(booking.id)"
                  class="btn btn-success"
                >
                  Подтвердить
                </button>

                <button
                  v-if="booking.status === 'pending' && !isPastBooking(booking)"
                  @click="rejectBooking(booking.id)"
                  class="btn btn-secondary"
                >
                  Отклонить
                </button>

                <button 
                  v-if="booking.status === 'confirmed' && !isPastBooking(booking)"
                  @click="forceCancelBooking(booking.id)"
                  class="btn btn-secondary"
                >
                  Отменить
                </button>
                <span v-else-if="isPastBooking(booking) && ['pending', 'confirmed'].includes(booking.status)" class="past-booking">
                  Прошло
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Модальное окно для деталей пользователя -->
    <div v-if="selectedUser" class="modal-overlay" @click="closeUserDetails">
      <div class="modal card" @click.stop>
        <div class="modal-header">
          <h3>Детали пользователя: {{ selectedUser.name }}</h3>
          <button @click="closeUserDetails" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="user-details">
            <div class="detail-row">
              <strong>Имя:</strong>
              <input v-model="selectedUser.name" type="text" class="form-input" />
            </div>
            <div class="detail-row">
              <strong>Email:</strong>
              <input v-model="selectedUser.email" type="email" class="form-input" />
            </div>
            <div class="detail-row">
              <strong>Телефон:</strong>
              <input v-model="selectedUser.phone" type="tel" class="form-input" />
            </div>
            <div class="detail-row">
              <strong>Роль:</strong>
              <select v-model="selectedUser.role" class="form-input">
                <option value="user">Пользователь</option>
                <option value="admin">Администратор</option>
              </select>
            </div>
            <div class="detail-row">
              <strong>Новый пароль:</strong>
              <input v-model="newPassword" type="password" placeholder="Оставьте пустым для сохранения текущего" class="form-input" />
            </div>
          </div>
          
          <div class="user-bookings">
            <h4 class="section-title">Бронирования пользователя</h4>
            <div v-if="userBookingsLoading" class="loading">Загрузка...</div>
            <div v-else-if="userBookings.length === 0" class="no-data">
              Нет бронирований
            </div>
            <div v-else class="bookings-list-small">
              <div class="booking-item card" :class="booking.status" v-for="booking in userBookings" :key="booking.id">
                <div class="booking-date">{{ formatDate(booking.booking_date) }}</div>
                <div class="booking-time">{{ formatTime(booking.start_time) }} - {{ formatTime(booking.end_time) }}</div>
                <div class="booking-status" :class="booking.status">
                  {{ statusText(booking.status) }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="saveUserChanges" class="btn btn-primary">Сохранить</button>
          <button @click="closeUserDetails" class="btn btn-secondary">Отмена</button>
        </div>
      </div>
    </div>
    
    <!-- Модальное окно для создания пользователя -->
    <div v-if="createUserModal" class="modal-overlay" @click="closeCreateUserModal">
      <div class="modal card" @click.stop>
        <div class="modal-header">
          <h3>Создать нового пользователя</h3>
          <button @click="closeCreateUserModal" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="user-details">
            <div class="detail-row">
              <strong>Имя *</strong>
              <input v-model="newUser.name" type="text" class="form-input" required />
            </div>
            <div class="detail-row">
              <strong>Email *</strong>
              <input v-model="newUser.email" type="email" class="form-input" required />
            </div>
            <div class="detail-row">
              <strong>Телефон</strong>
              <input v-model="newUser.phone" type="tel" class="form-input" />
            </div>
            <div class="detail-row">
              <strong>Пароль *</strong>
              <input v-model="newUser.password" type="password" class="form-input" required minlength="6" />
            </div>
            <div class="detail-row">
              <strong>Роль</strong>
              <select v-model="newUser.role" class="form-input">
                <option value="user">Пользователь</option>
                <option value="admin">Администратор</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="createUser" class="btn btn-primary">Создать</button>
          <button @click="closeCreateUserModal" class="btn btn-secondary">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { store } from '../store/store'
import api from '../services/api'
import { dialog } from '../services/dialog'

export default {
  data() {
    return {
      store,
      activeTab: 'users',
      users: [],
      allBookings: [],
      loadingUsers: false,
      loadingBookings: false,
      filterDate: '',
      filterStatus: '',
      selectedUser: null,
      newPassword: '',
      userBookings: [],
      userBookingsLoading: false,
      createUserModal: false,
      newUser: {
        name: '',
        email: '',
        phone: '',
        password: '',
        role: 'user'
      }
    }
  },
  computed: {
    groupedBookings() {
      const groups = {}
      this.allBookings.forEach(booking => {
        const date = booking.booking_date
        if (!groups[date]) {
          groups[date] = []
        }
        groups[date].push(booking)
      })
      return groups
    }
  },
  mounted() {
    this.loadUsers()
    this.loadAllBookings()
  },
  methods: {
    async loadUsers() {
      this.loadingUsers = true
      try {
        const response = await api.get('/admin/users')
        this.users = response.data.users
      } catch (error) {
        dialog.error(error.response?.data?.detail || 'Ошибка загрузки пользователей')
      } finally {
        this.loadingUsers = false
      }
    },
    async loadAllBookings() {
      this.loadingBookings = true
      try {
        const params = {}
        if (this.filterDate) {
          params.date = this.filterDate
        }
        if (this.filterStatus) {
          params.status = this.filterStatus
        }
        
        const response = await api.get('/admin/bookings', { params })
        this.allBookings = response.data.bookings
      } catch (error) {
        dialog.error(error.response?.data?.detail || 'Ошибка загрузки бронирований')
      } finally {
        this.loadingBookings = false
      }
    },
    resetFilters() {
      this.filterDate = ''
      this.filterStatus = ''
      this.loadAllBookings()
    },
    async showUserDetails(user) {
      this.selectedUser = { ...user }
      this.newPassword = ''
      this.loadUserBookings(user.id)
    },
    async loadUserBookings(userId) {
      this.userBookingsLoading = true
      try {
        const response = await api.get(`/admin/users/${userId}/bookings`)
        this.userBookings = response.data.bookings
      } catch (error) {
        dialog.error(error.response?.data?.detail || 'Ошибка загрузки бронирований пользователя')
      } finally {
        this.userBookingsLoading = false
      }
    },
    closeUserDetails() {
      this.selectedUser = null
      this.newPassword = ''
      this.userBookings = []
    },
    async saveUserChanges() {
      if (!await dialog.confirm(
        'Сохранить изменения данных пользователя?',
        {
          title: 'Сохранение пользователя',
          confirmText: 'Сохранить',
          cancelText: 'Отмена'
        }
      )) {
        return
      }
      
      try {
        const updateData = {
          name: this.selectedUser.name,
          phone: this.selectedUser.phone,
          email: this.selectedUser.email,
          role: this.selectedUser.role
        }
        
        if (this.newPassword) {
          updateData.password = this.newPassword
        }
        
        await api.put(`/admin/users/${this.selectedUser.id}`, updateData)
        await dialog.success('Данные пользователя успешно обновлены!')
        this.closeUserDetails()
        this.loadUsers()
      } catch (error) {
        dialog.error(error.response?.data?.detail || 'Ошибка обновления данных')
      }
    },
    async deleteUser(user) {
      if (user.id === this.store.user?.id) {
        dialog.error('Вы не можете удалить самого себя!')
        return
      }
      
      if (!await dialog.confirm(
        `Удалить пользователя ${user.name}? История его бронирований будет сохранена.`,
        {
          title: 'Удаление пользователя',
          confirmText: 'Удалить',
          cancelText: 'Отмена',
          tone: 'danger'
        }
      )) {
        return
      }
      
      try {
        await api.delete(`/admin/users/${user.id}`)
        await dialog.success('Пользователь удалён. История бронирований сохранена.')
        this.loadUsers()
      } catch (error) {
        dialog.error(error.response?.data?.detail || 'Ошибка удаления пользователя')
      }
    },
    async confirmBooking(bookingId) {
      if (!await dialog.confirm(
        'Подтвердить это бронирование?',
        {
          title: 'Подтверждение бронирования',
          confirmText: 'Подтвердить',
          cancelText: 'Отмена'
        }
      )) {
        return
      }
      
      try {
        await api.put(`/admin/bookings/${bookingId}/confirm`)
        await dialog.success('Бронирование подтверждено!')
        this.loadAllBookings()
      } catch (error) {
        dialog.error(error.response?.data?.detail || 'Ошибка подтверждения бронирования')
      }
    },
    formatDate(date) {
      const d = new Date(date)
      return d.toLocaleDateString('ru-RU', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      })
    },
    formatTime(time) {
      if (typeof time === 'string') {
        return time.substring(0, 5)
      } else if (typeof time === 'number' || (typeof time === 'string' && !isNaN(time))) {
        const totalSeconds = parseInt(time)
        const hours = Math.floor(totalSeconds / 3600)
        const minutes = Math.floor((totalSeconds % 3600) / 60)
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
      } else {
        return ''
      }
    },
    isPastBooking(booking) {
      const [year, month, day] = booking.booking_date.split('-').map(Number);
      const bookingDate = new Date(year, month - 1, day);
      
      let startHours, startMinutes;
      
      if (typeof booking.start_time === 'string' && booking.start_time.includes(':')) {
        [startHours, startMinutes] = booking.start_time.split(':').map(Number);
      } else {
        const totalSeconds = parseInt(booking.start_time) || 0;
        startHours = Math.floor(totalSeconds / 3600);
        startMinutes = Math.floor((totalSeconds % 3600) / 60);
      }
      
      bookingDate.setHours(startHours, startMinutes, 0, 0);
      const now = new Date();
      
      return bookingDate < now;
    },
    statusText(status) {
      const texts = {
        'pending': 'Ожидает подтверждения',
        'confirmed': 'Подтверждено',
        'cancelled_by_user': 'Отменено пользователем',
        'cancelled_by_admin': 'Отменено администратором',
        'rejected_by_admin': 'Отклонено администратором',
        'completed': 'Завершено'
      }
      return texts[status] || status
    },
    async rejectBooking(bookingId) {
      if (!await dialog.confirm(
        'Отклонить это бронирование?',
        {
          title: 'Отклонение бронирования',
          confirmText: 'Отклонить',
          cancelText: 'Отмена',
          tone: 'danger'
        }
      )) {
        return
      }

      try {
        await api.put(`/admin/bookings/${bookingId}/reject`)
        await dialog.success('Бронирование отклонено!')
        await this.loadAllBookings()
      } catch (error) {
        dialog.error(
          error.response?.data?.detail
          || 'Ошибка отклонения бронирования'
        )
      }
    },

    async forceCancelBooking(bookingId) {
      if (!await dialog.confirm(
        'Отменить это бронирование от имени администратора?',
        {
          title: 'Отмена бронирования',
          confirmText: 'Отменить бронь',
          cancelText: 'Оставить бронь',
          tone: 'danger'
        }
      )) {
        return
      }
      
      try {
        await api.put(`/bookings/${bookingId}/cancel`)
        await dialog.success('Бронирование отменено администратором!')
        this.loadAllBookings()
      } catch (error) {
        dialog.error(error.response?.data?.detail || 'Ошибка отмены бронирования')
      }
    },
    showCreateUserModal() {
      this.newUser = {
        name: '',
        email: '',
        phone: '',
        password: '',
        role: 'user'
      }
      this.createUserModal = true
    },
    closeCreateUserModal() {
      this.createUserModal = false
    },
    async createUser() {
      // Валидация
      if (!this.newUser.name || !this.newUser.email || !this.newUser.password) {
        dialog.error('Заполните все обязательные поля')
        return
      }
      
      if (this.newUser.password.length < 6) {
        dialog.error('Пароль должен содержать не менее 6 символов')
        return
      }
      
      try {
        await api.post('/admin/users', {
          name: this.newUser.name,
          email: this.newUser.email,
          phone: this.newUser.phone || '',
          password: this.newUser.password,
          role: this.newUser.role
        })
        
        await dialog.success('Пользователь успешно создан!')
        this.closeCreateUserModal()
        this.loadUsers()
      } catch (error) {
        dialog.error(error.response?.data?.detail || 'Ошибка создания пользователя')
      }
    }
  }
}
</script>


<style src="../styles/AdminView.css" scoped></style>
