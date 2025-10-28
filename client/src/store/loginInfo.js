import { ref } from 'vue'
import { useRouter } from 'vue-router'

// Стан користувача
const token = ref(localStorage.getItem('token') || null)
const userRole = ref(localStorage.getItem('userRole') || null)
const userFullName = ref(localStorage.getItem('userFullName') || null)
const userMajor = ref(localStorage.getItem('userMajor') || null)

let inactivityTimer = null

export function useAuth() {
  const router = useRouter()

  // Зберігає всі дані користувача після успішного входу
  const login = (data) => {
    // data = { access_token, token_type, role, full_name, major_name }

    token.value = data.access_token
    userRole.value = data.role
    userFullName.value = data.full_name
    userMajor.value = data.major_name

    localStorage.setItem('token', data.access_token)
    localStorage.setItem('userRole', data.role)
    localStorage.setItem('userFullName', data.full_name)
    localStorage.setItem('userMajor', data.major_name)

    startInactivityTimer()
  }

  // Завершує сесію користувача
  const logout = () => {
    token.value = null
    userRole.value = null
    userFullName.value = null
    userMajor.value = null

    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    localStorage.removeItem('userFullName')
    localStorage.removeItem('userMajor')

    clearTimeout(inactivityTimer)
    router.push('/login')
  }

  // Запускає таймер бездіяльності (25 хв)
  const startInactivityTimer = () => {
    clearTimeout(inactivityTimer)
    const timeoutDuration = 25 * 60 * 1000 // 25 хвилин

    inactivityTimer = setTimeout(() => {
      console.log('Сесію завершено через 25 хвилин бездіяльності.')
      logout()
    }, timeoutDuration)

    // Скидаємо таймер при активності користувача
    window.onmousemove = window.onkeydown = () => {
      clearTimeout(inactivityTimer)
      inactivityTimer = setTimeout(() => {
        console.log('Сесію завершено через 25 хвилин бездіяльності.')
        logout()
      }, timeoutDuration)
    }
  }

  return {
    token,
    role: userRole,
    fullName: userFullName,
    major: userMajor,
    login,
    logout,
    startInactivityTimer
  }
}
