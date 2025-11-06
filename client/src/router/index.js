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
import CoursesCatalogueView from '../views/CoursesCatalogueView.vue'
import ExamJournalView from '../views/ExamJournalView.vue'
import CourseExamsView from '../views/CourseExamsView.vue'
import MyProfileView from '../views/MyProfileView.vue'
import CreateCourseView from '../views/CreateCourseView.vue'

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
        requiresRole: 'student',
        title: 'Мої іспити'
      }
    },
    {
      path: '/transcript',
      name: 'MyTranscript',
      component: MyTranscriptView,
      meta: {
        requiresAuth: true,
        requiresRole: 'student',
        title: 'Мій атестат'
      }
    },
    {
      path: '/exam/:attemptId',
      name: 'ExamAttempt',
      component: ExamAttemptView,
      meta: {
        requiresAuth: true,
        requiresRole: 'student',
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
      path: '/courses/my',
      name: 'MyCoursesCatalogue',
      component: CoursesCatalogueView,
      meta: {
        requiresAuth: true,
        requiresRole: 'teacher',
        title: 'Мої курси'
      }
    },
    {
      path: '/courses/create',
      name: 'CreateNewCourse',
      component: CreateCourseView,
         meta: {
        requiresAuth: true,
        requiresRole: 'teacher',
        title: 'Створити новий курс'
      }
    },
    {
      path: '/courses',
      name: 'CoursesCatalogue',
      component: CoursesCatalogueView,
      meta: {
        requiresAuth: true,
        requiresRole: 'student',
        title: 'Каталог курсів'
      }
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
      path: '/exams/:examId/journal',
      name: 'ExamJournal',
      component: ExamJournalView,
      meta: {
        requiresAuth: true,
        requiresRole: 'teacher',
        title: 'Журнал іспиту'
      },
    },
    {
      path: '/my-profile',
      name: 'MyProfile',
      component: MyProfileView,
      meta: {
        requiresAuth: true,
        title: 'Мій профіль'
      }
    },
  ]
})

// Перевіряє доступ до маршрутів перед переходом
router.beforeEach((to, from, next) => {
  const auth = useAuth()

  if (to.meta.requiresAuth && !auth.token.value) {
    next({ path: '/unauthorized' })
    return
  }

  if (to.meta.requiresRole) {
    let hasAccess = false
    if (to.meta.requiresRole === 'teacher' && auth.isTeacher.value) {
      hasAccess = true
    }
    if (to.meta.requiresRole === 'student' && auth.isStudent.value) {
      hasAccess = true
    }

    if (!hasAccess) {
      next({ path: '/forbidden' })
      return
    }
  }
  next()
})

router.afterEach((to) => {
  const defaultTitle = 'Онлайн-платформа іспитів | Systematics'
  const rawTitle = to.meta.title

  const pageTitle =
    typeof rawTitle === 'string'
      ? `${rawTitle} | Systematics`
      : defaultTitle

  document.title = pageTitle
})

export default router
