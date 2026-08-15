<template>
  <div class="profile-container">
    <div class="profile-header">
      <h1>Личный кабинет</h1>
      <p>Добро пожаловать, {{ store.user?.name }}!</p>
    </div>

    <div class="profile-content">
      <div class="user-info card">
        <h2 class="section-title">Информация о пользователе</h2>

        <div class="info-item">
          <strong>Имя:</strong> {{ store.user?.name }}
        </div>

        <div class="info-item">
          <strong>Телефон:</strong> {{ store.user?.phone }}
        </div>

        <div class="info-item">
          <strong>Email:</strong> {{ store.user?.email }}
        </div>

        <div class="info-item">
          <strong>Роль:</strong>
          <span :class="roleClass">{{ roleText }}</span>
        </div>
      </div>

      <div class="bookings-section card">
        <h2 class="section-title">Мои бронирования</h2>

        <div v-if="loading" class="loading">
          Загрузка...
        </div>

        <div v-else-if="bookings.length === 0" class="no-data">
          У вас пока нет бронирований
        </div>

        <div v-else class="bookings-list">
          <div
            v-for="booking in bookings"
            :key="booking.id"
            class="booking-card card"
            :class="booking.status"
          >
            <div class="booking-header">
              <span class="booking-date">
                {{ formatDate(booking.booking_date) }}
              </span>

              <span
                class="booking-status"
                :class="booking.status"
              >
                {{ statusText(booking.status) }}
              </span>
            </div>

            <div class="booking-details">
              <div class="booking-info">
                <strong>Дорожка:</strong>
                {{ booking.lane_name }}
              </div>

              <div class="booking-info">
                <strong>Время:</strong>
                {{ formatTime(booking.start_time) }}
                -
                {{ formatTime(booking.end_time) }}
              </div>
            </div>

            <div class="booking-actions">
              <button
                v-if="canCancelBooking(booking)"
                class="btn btn-secondary"
                @click="cancelBooking(booking.id)"
              >
                Отменить
              </button>

              <span
                v-else-if="isActiveStatus(booking.status) && isPastBooking(booking)"
                class="past-booking"
              >
                Прошло
              </span>

              <span
                v-else-if="isActiveStatus(booking.status) && !hasEnoughTimeToCancel(booking)"
                class="pending-notice"
              >
                Отмена доступна не позднее чем за 2 часа до начала
              </span>

              <span
                v-else-if="booking.status === 'pending'"
                class="pending-notice"
              >
                Ожидает подтверждения
              </span>
            </div>
          </div>
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
      bookings: [],
      loading: false
    }
  },

  computed: {
    roleText() {
      return this.store.user?.role === 'admin'
        ? 'Администратор'
        : 'Пользователь'
    },

    roleClass() {
      return this.store.user?.role === 'admin'
        ? 'admin'
        : 'user'
    }
  },

  mounted() {
    if (this.store.isAuthenticated()) {
      this.loadBookings()
    } else {
      this.$router.push('/login')
    }
  },

  methods: {
    async loadBookings() {
      this.loading = true

      try {
        const response = await api.get('/my-bookings')
        this.bookings = response.data.bookings
      } catch (error) {
        console.error(
          'Ошибка загрузки бронирований:',
          error
        )

        if (error.response?.status === 401) {
          this.store.logout()
          this.$router.push('/login')
        }
      } finally {
        this.loading = false
      }
    },

    formatDate(date) {
      const [year, month, day] = date
        .split('-')
        .map(Number)

      const d = new Date(
        year,
        month - 1,
        day
      )

      return d.toLocaleDateString(
        'ru-RU',
        {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        }
      )
    },

    formatTime(time) {
      if (
        typeof time === 'string'
        && time.includes(':')
      ) {
        return time.substring(0, 5)
      }

      const totalSeconds = parseInt(time)

      if (Number.isNaN(totalSeconds)) {
        return ''
      }

      const hours = Math.floor(
        totalSeconds / 3600
      )

      const minutes = Math.floor(
        (totalSeconds % 3600) / 60
      )

      return (
        `${hours.toString().padStart(2, '0')}:`
        + `${minutes.toString().padStart(2, '0')}`
      )
    },

    getBookingStart(booking) {
      const [year, month, day] = booking
        .booking_date
        .split('-')
        .map(Number)

      let startHours = 0
      let startMinutes = 0

      if (
        typeof booking.start_time === 'string'
        && booking.start_time.includes(':')
      ) {
        const parts = booking.start_time
          .split(':')
          .map(Number)

        startHours = parts[0]
        startMinutes = parts[1]
      } else {
        const totalSeconds =
          parseInt(booking.start_time) || 0

        startHours = Math.floor(
          totalSeconds / 3600
        )

        startMinutes = Math.floor(
          (totalSeconds % 3600) / 60
        )
      }

      return new Date(
        year,
        month - 1,
        day,
        startHours,
        startMinutes,
        0,
        0
      )
    },

    isPastBooking(booking) {
      return this.getBookingStart(booking) <= new Date()
    },

    isActiveStatus(status) {
      return [
        'pending',
        'confirmed'
      ].includes(status)
    },

    hasEnoughTimeToCancel(booking) {
      const millisecondsUntilStart =
        this.getBookingStart(booking).getTime()
        - Date.now()

      return millisecondsUntilStart >= 2 * 60 * 60 * 1000
    },

    canCancelBooking(booking) {
      return (
        this.isActiveStatus(booking.status)
        && !this.isPastBooking(booking)
        && this.hasEnoughTimeToCancel(booking)
      )
    },

    statusText(status) {
      const texts = {
        pending: 'Ожидает подтверждения',
        confirmed: 'Подтверждено',
        cancelled_by_user: 'Отменено вами',
        cancelled_by_admin: 'Отменено администратором',
        rejected_by_admin: 'Отклонено администратором',
        completed: 'Завершено'
      }

      return texts[status] || status
    },

    async cancelBooking(bookingId) {
      const confirmed = await dialog.confirm(
        'Вы уверены, что хотите отменить бронирование?',
        {
          title: 'Отмена бронирования',
          confirmText: 'Отменить бронь',
          cancelText: 'Оставить бронь',
          tone: 'danger'
        }
      )

      if (!confirmed) {
        return
      }

      try {
        await api.put(
          `/bookings/${bookingId}/cancel`
        )

        dialog.success(
          'Бронирование отменено!',
          {
            title: 'Бронирование отменено'
          }
        )

        await this.loadBookings()
      } catch (error) {
        dialog.error(
          error.response?.data?.detail
          || 'Ошибка отмены бронирования'
        )
      }
    }
  }
}
</script>

<style src="../styles/ProfileView.css" scoped></style>
