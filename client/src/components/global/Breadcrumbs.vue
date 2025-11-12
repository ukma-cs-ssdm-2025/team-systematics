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

const breadcrumbs = computed(() => {
    const crumbs = []
    const path = route.path
    
    // Не показуємо breadcrumbs на публічних сторінках
    if (path === '/login' || path === '/' || path === '/forbidden' || path === '/unauthorized') {
        return []
    }
    
    // Додаємо головну сторінку
    if (auth.isStudent.value) {
        crumbs.push({ title: 'Головна', path: '/exams' })
    } else if (auth.isTeacher.value) {
        crumbs.push({ title: 'Головна', path: '/courses/my' })
    } else if (auth.isSupervisor.value) {
        crumbs.push({ title: 'Головна', path: '/courses/supervisor' })
    }
    
    // Обробляємо різні маршрути
    if (path.startsWith('/courses/') && path.includes('/exams')) {
        const courseId = route.params.courseId
        const examId = route.params.examId
        
        // Курси
        if (auth.isSupervisor.value) {
            crumbs.push({ title: 'Курси', path: '/courses/supervisor' })
        } else if (auth.isTeacher.value) {
            crumbs.push({ title: 'Мої курси', path: '/courses/my' })
        }
        
        // Створення іспиту
        if (path.includes('/exams/create')) {
            crumbs.push({ title: 'Створити іспит', path: null })
        } 
        // Іспити курсу (без examId)
        else if (path.match(/\/courses\/[^/]+\/exams$/) || (path.includes('/exams') && !examId && !path.includes('/create'))) {
            crumbs.push({ title: 'Іспити курсу', path: null })
        }
        // Конкретний іспит з examId
        else if (examId) {
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
    } else if (path.startsWith('/courses/') && path.includes('/details')) {
        // Деталі курсу
        const courseId = route.params.courseId
        if (auth.isSupervisor.value) {
            crumbs.push({ title: 'Курси', path: '/courses/supervisor' })
        } else if (auth.isTeacher.value) {
            crumbs.push({ title: 'Мої курси', path: '/courses/my' })
        }
        crumbs.push({ title: 'Деталі курсу', path: null })
    } else if (path.startsWith('/exams/') && path.includes('/journal')) {
        // Журнал іспиту (для вчителя, маршрут /exams/:examId/journal)
        if (auth.isTeacher.value) {
            crumbs.push({ title: 'Мої курси', path: '/courses/my' })
        }
        crumbs.push({ title: 'Журнал іспиту', path: null })
    } else if (path.startsWith('/exam/')) {
        // Спроба іспиту
        crumbs.push({ title: 'Мої іспити', path: '/exams' })
        if (path.includes('/review')) {
            crumbs.push({ title: 'Перегляд відповідей', path: null })
        } else {
            crumbs.push({ title: 'Проходження іспиту', path: null })
        }
    } else if (path.startsWith('/exams-results/')) {
        // Результати спроби
        crumbs.push({ title: 'Мої іспити', path: '/exams' })
        crumbs.push({ title: 'Результати іспиту', path: null })
    } else if (path.startsWith('/plagiarism-check/compare')) {
        // Порівняння плагіату
        crumbs.push({ title: 'Перевірка плагіату', path: '/plagiarism-check' })
        crumbs.push({ title: 'Порівняння робіт', path: null })
    } else if (path.startsWith('/courses/create')) {
        // Створення курсу
        if (auth.isTeacher.value) {
            crumbs.push({ title: 'Мої курси', path: '/courses/my' })
        }
        crumbs.push({ title: 'Створити новий курс', path: null })
    } else if (routeMap[path]) {
        // Прості маршрути з мапи
        const routeInfo = routeMap[path]
        if (routeInfo.parent) {
            crumbs.push({ title: routeMap[routeInfo.parent].title, path: routeInfo.parent })
        }
        crumbs.push({ title: routeInfo.title, path: null })
    } else if (route.meta?.title) {
        // Використовуємо title з мета-даних маршруту
        crumbs.push({ title: route.meta.title, path: null })
    }
    
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

