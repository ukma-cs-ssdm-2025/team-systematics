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
import ExamSessionManagementView from '../views/ExamSessionManagementView.vue'
import CourseDetailsView from '../views/CourseDetailsView.vue'
import PlagiarismCheckView from '../views/PlagiarismCheckView.vue'
import PlagiarismComparisonView from '../views/PlagiarismComparisonView.vue'
import CreateCourseView from '../views/CreateCourseView.vue'
import CreateExamView from '../views/CreateExamView.vue'
import CourseAnalyticsView from '../views/CourseAnalyticsView.vue'
import RegisterView from '../views/RegisterView.vue'

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
      path: '/register',
      name: 'Register',
      component: RegisterView,
      meta: {
        title: 'Реєстрація'
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
      path: '/courses/:courseId/exams/create',
      name: 'CreateExam',
      component: CreateExamView,
      meta: {
        requiresAuth: true,
        requiresRole: 'teacher',
        title: 'Створити новий іспит'
      }
    },
    {
      path: '/courses/:courseId/exams/:examId/edit',
      name: 'EditExam',
      component: CreateExamView,
      meta: {
        requiresAuth: true,
        requiresRole: 'teacher',
        title: 'Редагувати іспит'
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
        requiresRole: ['teacher', 'supervisor'],
        title: 'Іспити курсу'
      }
    },
    {
      path: '/courses/:courseId/analytics',
      name: 'CourseAnalytics',
      component: CourseAnalyticsView,
      meta: {
        requiresAuth: true,
        requiresRole: 'teacher',
        title: 'Аналітика курсу'
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
      path: '/courses/:courseId/exams/:examId/session',
      name: 'ExamSessionManagement',
      component: ExamSessionManagementView,
      meta: {
        requiresAuth: true,
        requiresRole: 'supervisor',
        title: 'Управління сесією іспиту'
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
    {
      path: '/plagiarism-check',
      name: 'PlagiarismCheck',
      component: PlagiarismCheckView,
      meta: {
        requiresAuth: true,
        requiresRole: 'teacher',
        title: 'Перевірка плагіату'
      }
    },
    {
      path: '/plagiarism-check/compare/:answer1Id/:answer2Id',
      name: 'PlagiarismComparison',
      component: PlagiarismComparisonView,
      meta: {
        requiresAuth: true,
        requiresRole: 'teacher',
        title: 'Порівняння робіт'
      }
    },
    {
      path: '/courses/supervisor',
      name: 'CoursesSupervisor',
      component: CoursesCatalogueView,
      meta: {
        requiresAuth: true,
        requiresRole: 'supervisor',
        title: 'Курси'
      }
    },
    {
      path: '/courses/:courseId/details',
      name: 'CourseDetails',
      component: CourseDetailsView,
      meta: {
        requiresAuth: true,
        requiresRole: 'supervisor',
        title: 'Деталі курсу'
      }
    },
  ]
})

// Допоміжна функція для перевірки ролі користувача
function checkUserRole(role, auth) {
  if (role === 'teacher') return auth.isTeacher.value
  if (role === 'student') return auth.isStudent.value
  if (role === 'supervisor') return auth.isSupervisor.value
  return false
}

// Допоміжна функція для перевірки доступу за роллю
function hasRoleAccess(requiredRole, auth, to) {
  // Підтримка масиву ролей
  if (Array.isArray(requiredRole)) {
    return requiredRole.some(role => checkUserRole(role, auth))
  }
  
  // Одиночна роль
  if (checkUserRole(requiredRole, auth)) {
    return true
  }
  
  // Дозволяємо доступ до /exams як для студентів, так і для вчителів
  if (to.path === '/exams' && (auth.isTeacher.value || auth.isStudent.value)) {
    return true
  }
  
  return false
}

// Перевіряє доступ до маршрутів перед переходом
router.beforeEach((to, from, next) => {
  const auth = useAuth()

  if (to.meta.requiresAuth && !auth.token.value) {
    next({ path: '/unauthorized' })
    return
  }

  if (to.meta.requiresRole) {
    const hasAccess = hasRoleAccess(to.meta.requiresRole, auth, to)
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
