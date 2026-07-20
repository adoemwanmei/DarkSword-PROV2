import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from '../utils/axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  async function login(username, password) {
    try {
      const response = await axios.post('/api/auth/login', new URLSearchParams({
        username,
        password
      }), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      token.value = response.data.access_token
      localStorage.setItem('token', token.value)
      await getMe()
      return true
    } catch (error) {
      return false
    }
  }

  async function getMe() {
    try {
      const response = await axios.get('/api/auth/me')
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(user.value))
      return user.value
    } catch (error) {
      return null
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    token,
    user,
    login,
    getMe,
    logout
  }
})
