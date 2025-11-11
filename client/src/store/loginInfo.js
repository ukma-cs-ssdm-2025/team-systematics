import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

// Стан користувача
const token = ref(localStorage.getItem('token') || null)
const userRole = ref(localStorage.getItem('userRole') || null)
const userFullName = ref(localStorage.getItem('userFullName') || null)
const userMajor = ref(localStorage.getItem('userMajor') || null)
const avatarUrl = ref(localStorage.getItem('avatarUrl') || null)

let inactivityTimer = null
let updateAvatarUrl = null

export function useAuth() {
  const router = useRouter()

  const isStudent = computed(() => userRole.value === 'student')
  const isTeacher = computed(() => userRole.value === 'teacher')
  const isSupervisor = computed(() => userRole.value === 'supervisor')

  // Зберігає всі дані користувача після успішного входу
  const login = (data) => {
    // data = { access_token, token_type, role, full_name, major_name, avatar_url }

    token.value = data.access_token
    userRole.value = data.role
    userFullName.value = data.full_name
    userMajor.value = data.major_name
    avatarUrl.value = data.avatar_url

    localStorage.setItem('token', data.access_token)
    localStorage.setItem('userRole', data.role)
    localStorage.setItem('userFullName', data.full_name)
    localStorage.setItem('userMajor', data.major_name)
    localStorage.setItem('avatarUrl', data.avatar_url)

    startInactivityTimer()
  }

  // Завершує сесію користувача
  const logout = () => {
    token.value = null
    userRole.value = null
    userFullName.value = null
    userMajor.value = null
    avatarUrl.value = null

    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    localStorage.removeItem('userFullName')
    localStorage.removeItem('userMajor')
    localStorage.removeItem('avatarUrl')

    // Видаляємо всі збережені чернетки створення іспитів
    try {
      const keysToRemove = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('exam-draft-')) {
          keysToRemove.push(key)
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key))
    } catch (err) {
      console.error('Не вдалося видалити чернетки іспитів з localStorage:', err)
    }

    clearTimeout(inactivityTimer)
    router.push('/login')
  }

  // Запускає таймер бездіяльності (25 хв)
  const startInactivityTimer = () => {
    clearTimeout(inactivityTimer)
    const timeoutDuration = 25 * 60 * 1000 // 25 хвилин

    inactivityTimer = setTimeout(() => {
      logout()
    }, timeoutDuration)

    // Скидаємо таймер при активності користувача
    globalThis.onmousemove = globalThis.onkeydown = () => {
      clearTimeout(inactivityTimer)
      inactivityTimer = setTimeout(() => {
        logout()
      }, timeoutDuration)
    }
  }

  const updateAvatarUrl = (newUrl) => {
    if (newUrl) {
      avatarUrl.value = newUrl
      localStorage.setItem('avatarUrl', newUrl)
    }
  }

  return {
    token,
    role: userRole,
    fullName: userFullName,
    major: userMajor,
    avatarUrl: avatarUrl,
    isStudent,
    isTeacher,
    isSupervisor,
    login,
    logout,
    startInactivityTimer,
    updateAvatarUrl,
  }
}
