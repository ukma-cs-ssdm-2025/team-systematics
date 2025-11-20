<template>
    <nav v-if="breadcrumbs.length > 0" class="breadcrumbs">
        <ol class="breadcrumbs-list">
            <li v-for="(crumb, index) in breadcrumbs" :key="index" class="breadcrumb-item">
                <router-link 
                    v-if="index < breadcrumbs.length - 1 && crumb.path" 
                    :to="crumb.path" 
                    class="breadcrumb-link"
                >
                    {{ crumb.title }}
                </router-link>
                <span v-else class="breadcrumb-current">{{ crumb.title }}</span>
                <span v-if="index < breadcrumbs.length - 1" class="breadcrumb-separator">/</span>
            </li>
        </ol>
    </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '../../store/loginInfo'

const route = useRoute()
const auth = useAuth()

// Мапа маршрутів для breadcrumbs
const routeMap = {
    '/exams': { title: 'Мої іспити', parent: null },
    '/transcript': { title: 'Мій атестат', parent: null },
    '/courses': { title: 'Каталог курсів', parent: null },
    '/courses/supervisor': { title: 'Курси', parent: null },
    '/courses/my': { title: 'Мої курси', parent: null },
    '/plagiarism-check': { title: 'Перевірка плагіату', parent: null },
    '/my-profile': { title: 'Налаштування профіля', parent: null },
}

// Допоміжна функція для додавання головної сторінки
function addHomePage(crumbs) {
    if (auth.isStudent.value) {
        crumbs.push({ title: 'Головна', path: '/exams' })
    } else if (auth.isTeacher.value) {
        crumbs.push({ title: 'Головна', path: '/courses/my' })
    } else if (auth.isSupervisor.value) {
        crumbs.push({ title: 'Головна', path: '/courses/supervisor' })
    }
}

// Допоміжна функція для додавання курсу до breadcrumbs
function addCourseBreadcrumb(crumbs) {
    if (auth.isSupervisor.value) {
        crumbs.push({ title: 'Курси', path: '/courses/supervisor' })
    } else if (auth.isTeacher.value) {
        crumbs.push({ title: 'Мої курси', path: '/courses/my' })
    }
}

// Допоміжна функція для обробки маршрутів курсів з іспитами
function handleCourseExamsRoutes(crumbs, path) {
    const courseId = route.params.courseId
    const examId = route.params.examId
    
    addCourseBreadcrumb(crumbs)
    
    if (path.includes('/exams/create')) {
        crumbs.push({ title: 'Створити іспит', path: null })
    } else if (path.match(/\/courses\/[^/]+\/exams$/) || (path.includes('/exams') && !examId && !path.includes('/create'))) {
        crumbs.push({ title: 'Іспити курсу', path: null })
    } else if (examId) {
        crumbs.push({ title: 'Іспити курсу', path: `/courses/${courseId}/exams` })
        if (path.includes('/edit')) {
            crumbs.push({ title: 'Редагувати іспит', path: null })
        } else if (path.includes('/session')) {
            crumbs.push({ title: 'Управління сесією', path: null })
        } else if (path.includes('/journal')) {
            crumbs.push({ title: 'Журнал іспиту', path: null })
        } else if (path.includes('/review')) {
            crumbs.push({ title: 'Перегляд іспиту', path: null })
        }
    }
}

// Допоміжна функція для обробки маршрутів спроб іспиту
function handleExamAttemptRoutes(crumbs, path) {
    if (auth.isTeacher.value) {
        crumbs.push({ title: 'Мої курси', path: '/courses/my' })
        const examId = route.query.examId
        if (examId) {
            crumbs.push({ title: 'Журнал іспиту', path: `/exams/${examId}/journal` })
        }
    } else {
        crumbs.push({ title: 'Мої іспити', path: '/exams' })
    }
    
    if (path.includes('/review')) {
        crumbs.push({ title: 'Перегляд відповідей', path: null })
    } else {
        crumbs.push({ title: 'Проходження іспиту', path: null })
    }
}

// Допоміжна функція для обробки маршрутів результатів іспиту
function handleExamResultsRoutes(crumbs) {
    if (auth.isTeacher.value) {
        crumbs.push({ title: 'Мої курси', path: '/courses/my' })
        const examId = route.query.examId
        if (examId) {
            crumbs.push({ title: 'Журнал іспиту', path: `/exams/${examId}/journal` })
        }
    } else {
        crumbs.push({ title: 'Мої іспити', path: '/exams' })
    }
    crumbs.push({ title: 'Результати іспиту', path: null })
}

// Допоміжна функція для обробки журналу іспиту
function handleExamJournalRoute(crumbs) {
    if (auth.isTeacher.value) {
        crumbs.push({ title: 'Мої курси', path: '/courses/my' })
    }
    crumbs.push({ title: 'Журнал іспиту', path: null })
}

// Допоміжна функція для обробки створення курсу
function handleCreateCourseRoute(crumbs) {
    if (auth.isTeacher.value) {
        crumbs.push({ title: 'Мої курси', path: '/courses/my' })
    }
    crumbs.push({ title: 'Створити новий курс', path: null })
}

// Допоміжна функція для обробки маршрутів з мапи
function handleRouteMapRoute(crumbs, path) {
    const routeInfo = routeMap[path]
    if (routeInfo.parent) {
        crumbs.push({ title: routeMap[routeInfo.parent].title, path: routeInfo.parent })
    }
    crumbs.push({ title: routeInfo.title, path: null })
}

// Допоміжна функція для перевірки публічних сторінок
function isPublicPage(path) {
    return path === '/login' || path === '/' || path === '/forbidden' || path === '/unauthorized'
}

// Допоміжна функція для обробки різних типів маршрутів
function processRoute(crumbs, path) {
    if (path.startsWith('/courses/') && path.includes('/exams')) {
        handleCourseExamsRoutes(crumbs, path)
        return true
    }
    if (path.startsWith('/courses/') && path.includes('/details')) {
        addCourseBreadcrumb(crumbs)
        crumbs.push({ title: 'Деталі курсу', path: null })
        return true
    }
    if (path.startsWith('/exams/') && path.includes('/journal')) {
        handleExamJournalRoute(crumbs)
        return true
    }
    if (path.startsWith('/exam/')) {
        handleExamAttemptRoutes(crumbs, path)
        return true
    }
    if (path.startsWith('/exams-results/')) {
        handleExamResultsRoutes(crumbs)
        return true
    }
    if (path.startsWith('/plagiarism-check/compare')) {
        crumbs.push(
            { title: 'Перевірка плагіату', path: '/plagiarism-check' },
            { title: 'Порівняння робіт', path: null }
        )
        return true
    }
    if (path.startsWith('/courses/create')) {
        handleCreateCourseRoute(crumbs)
        return true
    }
    if (routeMap[path]) {
        handleRouteMapRoute(crumbs, path)
        return true
    }
    if (route.meta?.title) {
        crumbs.push({ title: route.meta.title, path: null })
        return true
    }
    return false
}

const breadcrumbs = computed(() => {
    const crumbs = []
    const path = route.path
    
    if (isPublicPage(path)) {
        return []
    }
    
    addHomePage(crumbs)
    processRoute(crumbs, path)
    
    return crumbs
})
</script>

<style scoped>

.breadcrumbs-list {
    display: flex;
    align-items: center;
    gap: 8px;
    list-style: none;
    margin: 0;
    padding: 0;
    flex-wrap: wrap;
}

.breadcrumb-item {
    display: flex;
    align-items: center;
    gap: 8px;
}

.breadcrumb-link {
    color: var(--color-violet);
    text-decoration: none;
    transition: color 0.2s ease;
}

.breadcrumb-link:hover {
    color: var(--color-purple);
    text-decoration: underline;
}

.breadcrumb-current {
    color: var(--color-dark-gray);
    font-weight: 500;
}

.breadcrumb-separator {
    color: var(--color-gray);
    margin: 0 4px;
}
</style>

