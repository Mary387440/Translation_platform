import { defineStore } from 'pinia'
import axios from 'axios'

export const api = axios.create({
  baseURL: 'http://127.0.0.1:5000',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function loadUser() {
  try {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: loadUser(),
  }),
  actions: {
    async login(email, password) {
      const res = await api.post('/api/auth/login', { email, password })
      this.token = res.data.access_token
      this.user = res.data.user
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
    async fetchMe() {
      const { data } = await api.get('/api/auth/me')
      this.user = data
      localStorage.setItem('user', JSON.stringify(data))
    },
  },
})
