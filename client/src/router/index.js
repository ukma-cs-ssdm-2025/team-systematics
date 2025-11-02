import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../store/loginInfo'
import LoginView from '../views/LoginView.vue'
import MyExamsView from '../views/MyExamsView.vue'
import ExamAttemptView from '../views/ExamAttemptView.vue'
import ForbiddenView from '../views/ForbiddenView.vue'
import UnauthorizedView from '../views/UnauthorizedView.vue'
import ExamResultsView from '../views/ExamResultsView.vue'
import ExamReviewView from '../views/ExamReviewView.vue'
import MyTranscriptView from '../views/MyTranscriptView.vue'
import MyCoursesView from '../views/MyCoursesView.vue'
import CourseJournalView from '../views/ExamJournalView.vue'
import CourseExamsView from '../views/CourseExamsView.vue'

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
      path: '/transcript',
      name: 'MyTranscript',
      component: MyTranscriptView,
      meta: {
        requiresAuth: true,
        title: 'Мій атестат'
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
    },
    {
      path: '/exams-results/:attemptId',
      name: 'ExamResults',
      component: ExamResultsView,
      meta: {
        requiresAuth: true,
        title: 'Результати іспиту'
      }
    },
    {
      path: '/exam/:attemptId/review',
      name: 'ExamReview',
      component: ExamReviewView,
      meta: {
        requiresAuth: true,
        title: 'Перегляд відповідей'
      }
    },
    {
      path: '/courses',
      name: 'MyCourses',
      component: MyCoursesView,
      meta: {
        requiresAuth: true,
        requiresRole: 'teacher',
        title: 'Мої курси'
      },
    },
    {
      path: '/courses/:courseId/exams',
      name: 'CourseExams',
      component: CourseExamsView,
      meta: {
        requiresAuth: true,
        requiresRole: 'teacher',
        title: 'Іспити курсу'
      }
    },
    {
      path: '/courses/:courseId/journal',
      name: 'CourseJournal',
      component: CourseJournalView,
      meta: {
        requiresAuth: true,
        requiresRole: 'teacher',
        title: 'Журнал курсу'
      },
    }
  ]
})

// Перевіряє доступ до маршрутів перед переходом
router.beforeEach((to) => {
  const auth = useAuth()
  console.log(auth)

  if (to.meta.requiresAuth && !auth.token.value) {
    // Якщо немає токена — перенаправляємо на /unauthorized
    return '/unauthorized'
  }

  // Перевірка на необхідну роль
  if (to.meta.requiresRole) {
    let hasAccess = false
    if (to.meta.requiresRole === 'teacher' && auth.isTeacher.value) {
      hasAccess = true
    }
    
    if (!hasAccess) {
      return '/forbidden' 
    }
  }
  return true
})

router.afterEach((to) => {
  const defaultTitle = 'Онлайн-платформа іспитів | Systematics'

  // Встановлюємо title сторінки
  document.title = to.meta.title
    ? `${to.meta.title} | Systematics`
    : defaultTitle;
});

export default router
