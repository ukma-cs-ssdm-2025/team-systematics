import axios from 'axios'
import { useAuth } from '../store/token'
import { useRouter } from 'vue-router'

const { logout } = useAuth()

export const http = axios.create({
  baseURL: 'http://127.0.0.1:3000',
})

// Додає токен до кожного запиту
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Обробляє помилки авторизації
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Токен недійсний або минув строк
      logout()
    } else if (error.response?.status === 403) {
      // Недостатньо прав
      const router = useRouter()
      router.push('/forbidden')
    }
    return Promise.reject(error)
  }
)
