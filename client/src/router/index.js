import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../store/token'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  
  routes: [
        {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'Login',
      component: LoginView
    },
    {
      // path: '/forbidden'
      // name: 'Forbidden',
      // component: ForbiddenView
    },
    {
      // path: '/exams',
      // name: 'Exams',
      // component: ExamsComponent,
      // meta: { requiresAuth: true } // доступ лише для авторизованих
    },
  ]
})

// Перевіряє доступ до маршрутів перед переходом
router.beforeEach((to) => {
  const { token } = useAuth()

  if (to.meta.requiresAuth && !token.value) {
    // Якщо немає токена — перенаправляємо на /login
    return '/login'
  }
})

export default router
