import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../store/loginInfo'
import LoginView from '../views/LoginView.vue'
import MyExamsView from '../views/MyExamsView.vue'

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
      // path: '/forbidden'
      // name: 'Forbidden',
      // component: ForbiddenView,
      // meta:
      // {
      //   title: '403: Доступ заборонено'
      // }
    },
    {
      path: '/exams',
      name: 'MyExams',
      component: MyExamsView,
      meta:
      {
        requiresAuth: false,  // доступ лише для авторизованих
        title: 'Мої іспити'
      }
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

router.afterEach((to) => {
    const defaultTitle = 'Онлайн-платформа іспитів | Systematics'
    
    // Встановлюємо title сторінки
    document.title = to.meta.title 
        ? `${to.meta.title} | Systematics`
        : defaultTitle;
});

export default router
