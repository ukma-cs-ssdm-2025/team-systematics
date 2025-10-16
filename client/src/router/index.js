import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../store/loginInfo'
import LoginView from '../views/LoginView.vue'
import MyExamsView from '../views/MyExamsView.vue'
import ExamAttemptView from '../views/ExamAttemptView.vue'
import ForbiddenView from '../views/ForbiddenView.vue'
import UnauthorizedView from '../views/UnauthorizedView.vue'

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
      component: LoginView,
      meta: {
        title: 'Увійти'
      }
    },
    {
      path: '/forbidden',
      name: 'Forbidden',
      component: ForbiddenView,
      meta:
      {
        title: '403: Доступ заборонено'
      }
    },
    {
      path: '/unauthorized',
      name: 'Unauthorized',
      component: UnauthorizedView,
      meta:
      {
        title: '401: Неавторизований доступ'
      },
    },
    {
      path: '/exams',
      name: 'MyExams',
      component: MyExamsView,
      meta:
      {
        requiresAuth: true,  // доступ лише для авторизованих
        title: 'Мої іспити'
      }
    },
    {
      path: '/exam/:attemptId',
      name: 'ExamAttempt',
      component: ExamAttemptView,
      meta: {
        requiresAuth: true,
        title: 'Проходження іспиту'
      }
    }
  ]
})

// Перевіряє доступ до маршрутів перед переходом
router.beforeEach((to) => {
  const { token } = useAuth()

  if (to.meta.requiresAuth && !token.value) {
    // Якщо немає токена — перенаправляємо на /unauthorized
    return '/unauthorized'
  }
})

router.afterEach((to) => {
  const defaultTitle = 'Онлайн-платформа іспитів | Systematics'

  // Встановлюємо title сторінки
  document.title = to.meta.title
    ? `${to.meta.title} | Systematics`
    : defaultTitle;
});

export default router
