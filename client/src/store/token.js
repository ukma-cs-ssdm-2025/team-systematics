import { ref } from 'vue'
import { useRouter } from 'vue-router'

const token = ref(localStorage.getItem('token'))
let inactivityTimer = null

export function useAuth() {
    const router = useRouter()
    
  // Зберігає токен після успішного входу
  const login = (jwt) => {
    token.value = jwt
    localStorage.setItem('token', jwt)
    startInactivityTimer()
  }

  // Завершує сесію користувача
  const logout = () => {
    token.value = null
    localStorage.removeItem('token')
    clearTimeout(inactivityTimer)
    router.push('/login')
  }

  // Запускає таймер бездіяльності (25 хв)
  const startInactivityTimer = () => {
    clearTimeout(inactivityTimer)
    inactivityTimer = setTimeout(() => {
      alert('Сесію завершено через 25 хвилин бездіяльності.')
      logout()
    }, 25 * 60 * 1000)

    // Скидаємо таймер при активності користувача
    window.onmousemove = window.onkeydown = () => {
      clearTimeout(inactivityTimer)
      inactivityTimer = setTimeout(() => {
        alert('Сесію завершено через 25 хвилин бездіяльності.')
        logout()
      }, 25 * 60 * 1000)
    }
  }

  return { token, login, logout, startInactivityTimer }
}