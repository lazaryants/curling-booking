<template>
  <div
    v-if="dialog.state.visible"
    class="app-dialog-overlay"
    @click.self="dialog.cancel()"
  >
    <div
      class="app-dialog"
      :class="`tone-${dialog.state.tone}`"
      role="dialog"
      aria-modal="true"
    >
      <div class="app-dialog-header">
        <h3>{{ dialog.state.title }}</h3>

        <button
          type="button"
          class="app-dialog-close"
          aria-label="Закрыть"
          @click="dialog.cancel()"
        >
          ×
        </button>
      </div>

      <div class="app-dialog-body">
        <div class="app-dialog-icon">
          <span v-if="dialog.state.tone === 'success'">✓</span>
          <span v-else-if="dialog.state.tone === 'danger'">!</span>
          <span v-else-if="dialog.state.mode === 'confirm'">?</span>
          <span v-else>i</span>
        </div>

        <div class="app-dialog-message">
          {{ dialog.state.message }}
        </div>
      </div>

      <div class="app-dialog-footer">
        <button
          v-if="dialog.state.mode === 'confirm'"
          type="button"
          class="dialog-btn dialog-btn-secondary"
          @click="dialog.cancel()"
        >
          {{ dialog.state.cancelText }}
        </button>

        <button
          type="button"
          class="dialog-btn dialog-btn-primary"
          @click="dialog.accept()"
        >
          {{ dialog.state.confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { dialog } from '../services/dialog'

export default {
  name: 'AppDialog',

  data() {
    return {
      dialog
    }
  },

  mounted() {
    window.addEventListener('keydown', this.handleKeydown)
  },

  beforeUnmount() {
    window.removeEventListener('keydown', this.handleKeydown)
  },

  methods: {
    handleKeydown(event) {
      if (!this.dialog.state.visible) {
        return
      }

      if (event.key === 'Escape') {
        this.dialog.cancel()
      }
    }
  }
}
</script>

<style scoped>
.app-dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 5000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(0, 33, 71, 0.62);
  backdrop-filter: blur(2px);
}

.app-dialog {
  width: min(460px, 100%);
  overflow: hidden;
  background: #ffffff;
  border: 3px solid #01579b;
  border-radius: 14px;
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.35);
}

.app-dialog.tone-success {
  border-color: #2e7d32;
}

.app-dialog.tone-danger {
  border-color: #c62828;
}

.app-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  padding: 17px 20px;
  background: linear-gradient(135deg, #01579b 0%, #004d40 100%);
  color: #ffffff;
}

.tone-success .app-dialog-header {
  background: linear-gradient(135deg, #2e7d32 0%, #00695c 100%);
}

.tone-danger .app-dialog-header {
  background: linear-gradient(135deg, #c62828 0%, #8e0000 100%);
}

.app-dialog-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.app-dialog-close {
  padding: 0;
  background: none;
  border: none;
  color: #ffffff;
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
}

.app-dialog-body {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 25px 22px;
}

.app-dialog-icon {
  flex: 0 0 46px;
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e3f2fd;
  border: 2px solid #01579b;
  border-radius: 50%;
  color: #01579b;
  font-size: 1.45rem;
  font-weight: bold;
}

.tone-success .app-dialog-icon {
  background: #e8f5e9;
  border-color: #2e7d32;
  color: #2e7d32;
}

.tone-danger .app-dialog-icon {
  background: #ffebee;
  border-color: #c62828;
  color: #c62828;
}

.app-dialog-message {
  flex: 1;
  color: #263238;
  font-size: 1rem;
  line-height: 1.55;
  white-space: pre-line;
}

.app-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 15px 20px 20px;
  border-top: 1px solid #e0e0e0;
}

.dialog-btn {
  min-width: 120px;
  padding: 11px 20px;
  border: none;
  border-radius: 7px;
  font-size: 0.95rem;
  font-weight: bold;
  cursor: pointer;
  transition: 0.2s ease;
}

.dialog-btn-primary {
  background: #01579b;
  color: #ffffff;
}

.dialog-btn-primary:hover {
  background: #004d40;
}

.tone-success .dialog-btn-primary {
  background: #2e7d32;
}

.tone-danger .dialog-btn-primary {
  background: #c62828;
}

.dialog-btn-secondary {
  background: #eeeeee;
  color: #424242;
}

.dialog-btn-secondary:hover {
  background: #dddddd;
}

@media (max-width: 520px) {
  .app-dialog-overlay {
    padding: 12px;
  }

  .app-dialog-body {
    align-items: flex-start;
    padding: 20px 17px;
  }

  .app-dialog-footer {
    flex-direction: column-reverse;
  }

  .dialog-btn {
    width: 100%;
  }
}
</style>
