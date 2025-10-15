import axios from 'axios'
import router from '../router'

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
        const status = error.response?.status

        if (status === 401) {
            // Токен недійсний або минув строк — чистимо локальний стан і відправляємо на логін
            localStorage.removeItem('token')
            localStorage.removeItem('userRole')
            localStorage.removeItem('userFullName')
            localStorage.removeItem('userMajor')
            router.push('/unauthorized')
        } else if (status === 403) {
            // Недостатньо прав — перенаправляємо на сторінку 403
            router.push('/forbidden')
        }

        return Promise.reject(error)
    }
)