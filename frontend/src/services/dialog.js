import { reactive } from 'vue'

const state = reactive({
  visible: false,
  mode: 'info',
  title: '',
  message: '',
  confirmText: 'Подтвердить',
  cancelText: 'Отмена',
  tone: 'default'
})

let currentResolve = null

function close(result) {
  state.visible = false

  if (currentResolve) {
    currentResolve(result)
    currentResolve = null
  }
}

function open(options = {}) {
  if (currentResolve) {
    currentResolve(false)
    currentResolve = null
  }

  state.mode = options.mode || 'info'
  state.title = options.title || ''
  state.message = options.message || ''
  state.confirmText = options.confirmText || 'Подтвердить'
  state.cancelText = options.cancelText || 'Отмена'
  state.tone = options.tone || 'default'
  state.visible = true

  return new Promise((resolve) => {
    currentResolve = resolve
  })
}

export const dialog = {
  state,

  info(message, options = {}) {
    return open({
      mode: 'info',
      title: options.title || 'Сообщение',
      message,
      confirmText: options.confirmText || 'Понятно',
      tone: options.tone || 'default'
    })
  },

  success(message, options = {}) {
    return open({
      mode: 'info',
      title: options.title || 'Готово',
      message,
      confirmText: options.confirmText || 'Понятно',
      tone: 'success'
    })
  },

  error(message, options = {}) {
    return open({
      mode: 'info',
      title: options.title || 'Ошибка',
      message,
      confirmText: options.confirmText || 'Понятно',
      tone: 'danger'
    })
  },

  confirm(message, options = {}) {
    return open({
      mode: 'confirm',
      title: options.title || 'Подтверждение',
      message,
      confirmText: options.confirmText || 'Подтвердить',
      cancelText: options.cancelText || 'Отмена',
      tone: options.tone || 'default'
    })
  },

  accept() {
    close(true)
  },

  cancel() {
    close(false)
  }
}
