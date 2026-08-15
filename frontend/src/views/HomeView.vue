<template>
  <div class="home">
    <!-- Заголовок -->
    <div class="welcome-section">
      <h1>Бронирование дорожек для Керлинга в Арене76</h1>
      
      <div v-if="store.isAuthenticated()" class="user-greeting">
        <p><span class="highlight-text">Привет, {{ store.user.name }}! 👋</span></p>
        <router-link to="/profile" class="profile-btn">Перейти в личный кабинет</router-link>
      </div>
      
      <div v-else class="auth-prompt">
        <p><span class="prompt-text">Войдите или зарегистрируйтесь для бронирования</span></p>
        <div class="auth-buttons">
          <router-link to="/login" class="btn login-btn">Вход</router-link>
          <router-link to="/register" class="btn register-btn">Регистрация</router-link>
        </div>
      </div>
    </div>
    
    <div class="content">
      <p>Статус API: <span :class="apiStatusClass">{{ apiStatusMessage }}</span></p>
      
      <!-- Переключатель режимов -->
      <div class="view-toggle">
        <button :class="{ active: currentView === 'day' }" @click="switchToDay">День</button>
        <button :class="{ active: currentView === 'week' }" @click="switchToWeek">Неделя</button>
      </div>
      
      <!-- ========== РАСПИСАНИЕ ДНЯ ========== -->
      <div v-if="currentView === 'day'" class="day-schedule">
        <div class="date-selector">
          <button @click="prevDay">←</button>
          <span class="date-display">{{ formatDisplayDate(currentDate) }}</span>
          <button @click="nextDay">→</button>
        </div>
        
        <div v-if="schedule.length > 0" class="schedule">
          <div class="lanes-container">
            <div v-for="lane in schedule" :key="lane.lane_id" class="lane">
              <h2>{{ lane.lane_name }}</h2>
              <div class="slots">
                <div 
                  v-for="slot in lane.slots" 
                  :key="slot.id"
                  class="slot" 
                  :class="{
                    booked: slot.is_booked,
                    privateBooked: slot.is_booked && !slot.status,
                    pending: slot.is_booked && slot.status === 'pending',
                    confirmed: slot.is_booked && slot.status === 'confirmed',
                    past: isPastSlot(slot)
                  }"
                  @click="handleSlotClick(lane.lane_id, slot, lane.lane_name)"
                >
                  <div class="slot-time">
                    {{ formatTime(slot.start_time) }} - {{ formatTime(slot.end_time) }}
                  </div>
                  <div v-if="slot.is_booked" class="slot-info">
                    <template v-if="slot.status">
                      <div
                        v-if="slot.user_name"
                        class="user-name"
                      >
                        {{ slot.user_name }}
                      </div>

                      <div
                        v-if="store.user?.role === 'admin' && slot.user_phone"
                        class="user-phone"
                      >
                        {{ slot.user_phone }}
                      </div>

                      <div
                        v-if="!slot.user_name"
                        class="booking-status-text"
                      >
                        {{
                          slot.status === 'pending'
                            ? 'Ожидает подтверждения'
                            : 'Забронировано'
                        }}
                      </div>
                    </template>

                    <div v-else class="occupied-text">
                      Занято
                    </div>
                  </div>
                  <div v-else>
                    <div class="placeholder"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else class="loading">
          Загрузка расписания...
        </div>
        
        <div class="legend">
          <div class="legend-item">
            <span class="legend-color pending"></span>
            <span>🕗 Ожидает подтверждения</span>
          </div>
          <div class="legend-item">
            <span class="legend-color confirmed"></span>
            <span>✅ Подтверждено</span>
          </div>
          <div class="legend-item">
            <span class="legend-color past"></span>
            <span>🕒 Прошло</span>
          </div>
        </div>
      </div>
      
      <!-- ========== РАСПИСАНИЕ НЕДЕЛИ ========== -->
      <div v-else class="week-schedule">
        <div class="week-navigation">
          <button @click="prevWeek" class="nav-btn">←</button>
          <h3 class="week-title">{{ weekRange }}</h3>
          <button @click="nextWeek" class="nav-btn">→</button>
        </div>
        
        <div v-if="weekLoading" class="loading-state">
          <div class="loader"></div>
          <p>Загрузка расписания...</p>
        </div>
        
        <div v-else-if="!hasWeekBookings" class="empty-state">
          <p>📅 Нет бронирований на эту неделю</p>
        </div>
        
        <div v-else class="week-days">
          <div v-for="day in weekSchedule" :key="day.date" class="day-row">
            <div class="day-header">
              <div class="day-name">{{ day.day_of_week_short }}</div>
              <div class="day-date">{{ day.day_number }}.{{ day.month }}</div>
            </div>
            
            <div class="day-bookings">
              <div v-if="!day.has_bookings" class="no-bookings">
                Нет броней
              </div>
              <div v-else v-for="booking in day.bookings" :key="booking.id" 
                   class="booking-card" :class="booking.status">
                <div class="booking-info">
                  <div class="booking-time">{{ booking.start_time }}–{{ booking.end_time }}</div>
                  <div class="booking-lane">{{ booking.lane_name }}</div>
                  <div class="booking-user">{{ booking.user_name }}</div>
                </div>
                
                <div class="booking-actions">
                  <button 
                    @click="confirmWeekBooking(booking.id)" 
                    class="action-btn confirm"
                    :class="{ disabled: booking.status !== 'pending' }"
                    :disabled="booking.status !== 'pending'"
                    title="Подтвердить"
                  >✓</button>
                  <button 
                    @click="cancelWeekBooking(booking.id)" 
                    class="action-btn cancel"
                    title="Отменить"
                  >✗</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Модальное окно для админа -->
    <div v-if="adminActionModal" class="modal-overlay" @click="closeAdminActionModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>Действие с бронированием</h3>
          <button @click="closeAdminActionModal" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <p><strong>Дорожка:</strong> {{ adminActionModal.lane_name }}</p>
          <p><strong>Время:</strong> {{ formatTime(adminActionModal.start_time) }} - {{ formatTime(adminActionModal.end_time) }}</p>
          <p><strong>Пользователь:</strong> {{ adminActionModal.user_name }} 
            <span v-if="adminActionModal.user_phone">({{ adminActionModal.user_phone }})</span>
          </p>
          <p><strong>Статус:</strong> 
            <span :class="['status-badge', adminActionModal.status]">
              {{ adminActionModal.status === 'pending' ? 'Ожидает подтверждения' : 'Подтверждено' }}
            </span>
          </p>
        </div>
        <div class="modal-footer">
          <button 
            v-if="adminActionModal.status === 'pending'"
            @click="confirmBooking(adminActionModal.booking_id)" 
            class="confirm-btn"
          >
            Подтвердить
          </button>
          <button @click="cancelBooking(adminActionModal.booking_id)" class="cancel-btn">
            Отменить
          </button>
          <button @click="closeAdminActionModal" class="close-modal-btn">
            Закрыть
          </button>
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
      apiStatus: 'loading',
      apiStatusClass: 'loading',
      apiStatusMessage: 'Проверка соединения...',
      currentDate: new Date().toISOString().split('T')[0],
      schedule: [],
      currentView: 'day',
      adminActionModal: null,
      weekSchedule: [],
      weekLoading: false,
      weekStartDate: new Date().toISOString().split('T')[0]
    }
  },
  computed: {
    isAdmin() {
      return this.store.user?.role === 'admin'
    },
    weekRange() {
      if (!this.weekSchedule.length) return ''
      const firstDay = this.weekSchedule[0]
      const lastDay = this.weekSchedule[this.weekSchedule.length - 1]
      if (!firstDay || !lastDay) return ''
      return `${firstDay.day_number}.${firstDay.month} – ${lastDay.day_number}.${lastDay.month}`
    },
    hasWeekBookings() {
      return this.weekSchedule.some(day => day.has_bookings)
    }
  },
  mounted() {
    this.checkApiStatus()
    this.loadSchedule(this.currentDate)
  },
  methods: {
    formatTime(time) {
      return time?.substring(0, 5) || ''
    },
    
    formatDisplayDate(dateStr) {
      const date = new Date(dateStr)
      return date.toLocaleDateString('ru-RU', { 
        day: 'numeric', 
        month: 'long',
        year: 'numeric'
      })
    },
    
    async checkApiStatus() {
      try {
        const response = await api.get('/health')
        if (response.data.status === 'ok') {
          this.apiStatus = 'ok'
          this.apiStatusClass = 'ok'
          this.apiStatusMessage = '✅ работает'
        }
      } catch (error) {
        this.apiStatus = 'error'
        this.apiStatusClass = 'error'
        this.apiStatusMessage = '❌ недоступен'
      }
    },
    
    async loadSchedule(date) {
      try {
        const response = await api.get(`/schedule/${date}`)
        this.schedule = response.data.schedule
      } catch (error) {
        console.error('Ошибка загрузки расписания:', error)
        dialog.error('Ошибка загрузки расписания. Проверьте соединение с сервером.')
      }
    },
    
    isPastSlot(slot) {
      const now = new Date()
      const slotDate = new Date(this.currentDate)
      const [hours, minutes] = slot.start_time.split(':')
      slotDate.setHours(hours, minutes, 0, 0)
      return slotDate < now
    },
    
    async handleSlotClick(laneId, slot, laneName) {
      if (this.isAdmin && slot.is_booked) {
        this.adminActionModal = {
          booking_id: slot.booking_id,
          lane_name: laneName,
          start_time: slot.start_time,
          end_time: slot.end_time,
          user_name: slot.user_name,
          user_phone: slot.user_phone,
          status: slot.status
        }
        return
      }
      
      if (this.isPastSlot(slot)) return
      
      if (slot.is_booked) {
        // Чужая бронь: backend раскрывает только занятость.
        if (!slot.status) {
          return
        }

        if (slot.status === 'pending') {
          if (!this.isPastSlot(slot)) {
            if (await dialog.confirm(
              'Бронирование ожидает подтверждения администратором. Хотите отменить его?',
              {
                title: 'Ожидает подтверждения',
                confirmText: 'Отменить бронь',
                cancelText: 'Оставить бронь',
                tone: 'danger'
              }
            )) {
              await this.cancelBookingDirect(slot.booking_id)
            }
          }
          return
        }
        if (slot.status === 'confirmed') {
          if (await dialog.confirm(
            'Этот слот уже забронирован. Хотите отменить бронирование?',
            {
              title: 'Отмена бронирования',
              confirmText: 'Отменить бронь',
              tone: 'danger'
            }
          )) {
            await this.cancelBookingDirect(slot.booking_id)
          }
          return
        }
      }
      
      if (!this.store.isAuthenticated()) {
        if (await dialog.confirm(
          'Для бронирования нужно войти в систему. Перейти на страницу входа?',
          {
            title: 'Требуется вход',
            confirmText: 'Перейти ко входу'
          }
        )) {
          this.$router.push('/login')
        }
        return
      }
      
      if (!await dialog.confirm(
        `Дорожка: ${laneName}\nВремя: ${this.formatTime(slot.start_time)} - ${this.formatTime(slot.end_time)}`,
        {
          title: 'Подтверждение бронирования',
          confirmText: 'Забронировать',
          cancelText: 'Отмена'
        }
      )) {
        return
      }
      
      try {
        const response = await api.post('/bookings', {
          lane_id: laneId,
          booking_date: this.currentDate,
          start_time: slot.start_time,
          end_time: slot.end_time
        })
        
        this.loadSchedule(this.currentDate)
        
        if (response.data.status === 'pending') {
          dialog.success(
            `Бронирование создано и ожидает подтверждения администратором!\n\nДорожка: ${laneName}\nВремя: ${this.formatTime(slot.start_time)} - ${this.formatTime(slot.end_time)}`,
            { title: 'Бронирование создано' }
          )
        } else {
          dialog.success(
            `Бронирование успешно создано!\n\nДорожка: ${laneName}\nВремя: ${this.formatTime(slot.start_time)} - ${this.formatTime(slot.end_time)}`,
            { title: 'Бронирование создано' }
          )
        }
      } catch (error) {
        dialog.error(
          error.response?.data?.detail || 'Ошибка бронирования'
        )
      }
    },
    
    prevDay() {
      const date = new Date(this.currentDate)
      date.setDate(date.getDate() - 1)
      this.currentDate = date.toISOString().split('T')[0]
      this.loadSchedule(this.currentDate)
    },
    
    nextDay() {
      const date = new Date(this.currentDate)
      date.setDate(date.getDate() + 1)
      this.currentDate = date.toISOString().split('T')[0]
      this.loadSchedule(this.currentDate)
    },
    
    async loadWeekSchedule() {
      if (!this.isAdmin) {
        dialog.info('Расписание на неделю доступно только администратору')
        return
      }
      
      this.weekLoading = true
      try {
        const response = await api.get(`/schedule/week?start_date=${this.weekStartDate}`)
        this.weekSchedule = response.data.schedule
      } catch (error) {
        console.error('Ошибка загрузки недельного расписания:', error)
        dialog.error('Ошибка загрузки расписания на неделю')
      } finally {
        this.weekLoading = false
      }
    },
    
    prevWeek() {
      const date = new Date(this.weekStartDate)
      date.setDate(date.getDate() - 7)
      this.weekStartDate = date.toISOString().split('T')[0]
      this.loadWeekSchedule()
    },
    
    nextWeek() {
      const date = new Date(this.weekStartDate)
      date.setDate(date.getDate() + 7)
      this.weekStartDate = date.toISOString().split('T')[0]
      this.loadWeekSchedule()
    },
    
    switchToDay() {
      this.currentView = 'day'
      this.loadSchedule(this.currentDate)
    },
    
    switchToWeek() {
      this.currentView = 'week'
      if (this.isAdmin) {
        this.loadWeekSchedule()
      } else {
        dialog.info('Расписание на неделю доступно только администратору')
        this.currentView = 'day'
      }
    },
    
    async confirmBooking(bookingId) {
      if (!this.adminActionModal) return
      try {
        await api.put(`/admin/bookings/${bookingId}/confirm`)
        dialog.success('Бронирование подтверждено!')
        this.loadSchedule(this.currentDate)
        this.closeAdminActionModal()
      } catch (error) {
        dialog.error(
          'Ошибка подтверждения: '
          + (error.response?.data?.detail || 'неизвестно')
        )
      }
    },
    
    async confirmWeekBooking(bookingId) {
      if (!await dialog.confirm(
        'Подтвердить это бронирование?',
        {
          title: 'Подтверждение бронирования',
          confirmText: 'Подтвердить'
        }
      )) return
      try {
        await api.put(`/admin/bookings/${bookingId}/confirm`)
        dialog.success('Бронирование подтверждено!')
        this.loadWeekSchedule()
      } catch (error) {
        dialog.error(
          'Ошибка подтверждения: '
          + (error.response?.data?.detail || 'неизвестно')
        )
      }
    },
    
    async cancelBooking(bookingId) {
      if (!this.adminActionModal) return
      if (!await dialog.confirm(
        'Вы уверены, что хотите отменить бронирование?',
        {
          title: 'Отмена бронирования',
          confirmText: 'Отменить бронь',
          tone: 'danger'
        }
      )) return
      try {
        await api.put(`/bookings/${bookingId}/cancel`)
        dialog.success('Бронирование отменено!')
        this.loadSchedule(this.currentDate)
        this.closeAdminActionModal()
      } catch (error) {
        dialog.error(
          'Ошибка отмены: '
          + (error.response?.data?.detail || 'неизвестно')
        )
      }
    },
    
    async cancelWeekBooking(bookingId) {
      if (!await dialog.confirm(
        'Вы уверены, что хотите отменить это бронирование?',
        {
          title: 'Отмена бронирования',
          confirmText: 'Отменить бронь',
          tone: 'danger'
        }
      )) return
      try {
        await api.put(`/bookings/${bookingId}/cancel`)
        dialog.success('Бронирование отменено!')
        this.loadWeekSchedule()
      } catch (error) {
        dialog.error(
          'Ошибка отмены: '
          + (error.response?.data?.detail || 'неизвестно')
        )
      }
    },
    
    async cancelBookingDirect(bookingId) {
      if (!await dialog.confirm(
        'Вы уверены, что хотите отменить бронирование?',
        {
          title: 'Отмена бронирования',
          confirmText: 'Отменить бронь',
          tone: 'danger'
        }
      )) return
      try {
        await api.put(`/bookings/${bookingId}/cancel`)
        dialog.success('Бронирование отменено!')
        this.loadSchedule(this.currentDate)
      } catch (error) {
        dialog.error(
          'Ошибка отмены: '
          + (error.response?.data?.detail || 'неизвестно')
        )
      }
    },
    
    closeAdminActionModal() {
      this.adminActionModal = null
    }
  }
}
</script>

<style src="../styles/HomeView.css" scoped></style>
