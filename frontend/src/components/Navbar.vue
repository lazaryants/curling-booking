<template>
  <nav class="navbar">
    <div class="navbar-container">
      <router-link to="/" class="logo">
        <img
          src="/curling-stone.svg"
          alt=""
          class="logo-stone"
        />
        <span>Бронирование</span>
      </router-link>

      <div class="nav-links">
        <router-link to="/" class="nav-link">
          Главная
        </router-link>

        <template v-if="store.isAuthenticated()">
          <router-link to="/profile" class="nav-link">
            Личный кабинет
          </router-link>

          <button
            @click="logout"
            class="nav-link logout-btn"
          >
            Выйти
          </button>

          <template v-if="store.isAdmin()">
            <router-link
              to="/admin"
              class="nav-link admin-link"
            >
              Админ
            </router-link>
          </template>
        </template>

        <template v-else>
          <router-link to="/login" class="nav-link">
            Вход
          </router-link>

          <router-link to="/register" class="nav-link">
            Регистрация
          </router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script>
import { store } from '../store/store'

export default {
  data() {
    return {
      store
    }
  },

  methods: {
    logout() {
      store.logout()
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.navbar {
  background: #01579b;
  padding: 10px 0;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.navbar-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
  text-decoration: none;
  white-space: nowrap;
}

.logo-stone {
  width: 38px;
  height: 38px;
  display: block;
  flex: 0 0 auto;
}

.nav-links {
  display: flex;
  gap: 20px;
  align-items: center;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background 0.3s;
}

.nav-link:hover {
  background: rgba(255,255,255,0.1);
}

.logout-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 4px;
}

.logout-btn:hover {
  background: rgba(255,255,255,0.1);
}

.admin-link {
  background: #d32f2f;
  padding: 5px 10px;
  border-radius: 4px;
}

@media (max-width: 720px) {
  .navbar-container {
    gap: 10px;
  }

  .logo {
    font-size: 1.2rem;
    gap: 7px;
  }

  .logo-stone {
    width: 32px;
    height: 32px;
  }

  .nav-links {
    gap: 6px;
  }

  .nav-link,
  .logout-btn {
    padding: 5px 7px;
    font-size: 0.9rem;
  }
}


/* ==========================================================
   2026-08 — COMPACT FULLHD NAVBAR
   ========================================================== */

.navbar {
  padding: 5px 0;
  box-shadow: 0 2px 8px rgba(18, 68, 104, 0.18);
}

.navbar-container {
  max-width: 1360px;
  padding: 0 16px;
}

.logo {
  gap: 8px;
  font-size: 1.35rem;
}

.logo-stone {
  width: 34px;
  height: 34px;
}

.nav-links {
  gap: 12px;
}

.nav-link,
.logout-btn {
  padding: 5px 8px;
}

@media (max-width: 720px) {
  .navbar {
    padding: 5px 0;
  }

  .navbar-container {
    padding: 0 10px;
  }

  .logo {
    font-size: 1.1rem;
  }

  .logo-stone {
    width: 30px;
    height: 30px;
  }
}

</style>
