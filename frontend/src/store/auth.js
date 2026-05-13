import { computed, reactive } from 'vue'

const TOKEN_KEY = 'apm_token'
const USER_KEY = 'apm_user'

const state = reactive({
  token: localStorage.getItem(TOKEN_KEY) || '',
  user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
})

export const auth = {
  state,
  isLoggedIn: computed(() => !!state.token),
  isAdmin: computed(() => state.user?.role === 'admin'),

  setSession(token, user) {
    state.token = token
    state.user = user
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },

  setUser(user) {
    state.user = user
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },

  clear() {
    state.token = ''
    state.user = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },
}
