import axios from 'axios'
import router from '../router'

export const http = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
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
            // Перевіряємо, чи користувач вже не на сторінці /forbidden, щоб уникнути циклу
            if (router.currentRoute.value.path !== '/forbidden') {
                router.push('/forbidden')
            }
            console.error('403 Forbidden:', error.response?.data?.detail || 'Недостатньо прав доступу')
        }

        return Promise.reject(error)
    }
)