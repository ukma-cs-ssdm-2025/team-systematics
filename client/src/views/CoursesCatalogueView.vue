<template>
    <div>
        <Header />
        <main class="container">
            <section class="content-section">
                <div class="page-header">
                    <h2> {{ header }}</h2>
                    <CButton v-if="auth.isTeacher.value" @click="createNewCourse">+ Створити новий курс</CButton>
                </div>

                <div v-if="loading" class="status-message">Завантаження...</div>
                <div v-else-if="error" class="status-message error">{{ error }}</div>

                <div v-else-if="courses.length > 0" class="courses-grid">
                    <div v-for="course in courses" :key="course.id" class="course-card">
                        <div class="card-header">
                            <span class="course-code">{{ course.code }}</span>
                            <h3>{{ course.name }}</h3>
                        </div>
                        <div class="card-stats">
                            <span>👩‍🎓 {{ course.student_count }} студентів</span>
                            <span>📝 {{ course.exam_count }} іспитів</span>
                        </div>
                        <div class="card-actions">
                            <CButton v-if="auth.isTeacher.value" @click="goToExams(course.id)">Керувати</CButton>
                            <CButton v-if="auth.isStudent.value" @click="enrollToCourse(course.id)">Записати мене</CButton>
                        </div>
                    </div>
                </div>

                <div v-else class="empty-state">
                    <h2>У вас ще немає створених курсів</h2>
                    <CButton @click="createNewCourse">+ Створити свій перший курс</CButton>
                </div>
            </section>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import { getMyCourses, getAllCourses } from '../api/courses.js'
import { useAuth } from '../store/loginInfo.js'

const router = useRouter()
const courses = ref([])
const loading = ref(true)
const error = ref(null)

const auth = useAuth()
const header = computed(() => {
    return auth.isTeacher.value ? 'Мої курси' : 'Каталог курсів'
})

console.log(auth.isTeacher.value)

onMounted(async () => {
    try {
        if (auth.isTeacher.value) {
            console.log("HERE")
            const response = await getMyCourses()    
            courses.value = response.items
        }
        else if (auth.isStudent.value) {
            const response = await getAllCourses()
            courses.value = response.items
        }
    } catch (err) {
        error.value = err.message
    } finally {
        loading.value = false
    }
})

function goToExams(courseId) {
    router.push(`/courses/${courseId}/exams`)
}

function createNewCourse() {
    router.push('/courses/create')
}
</script>

<style scoped>
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.courses-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 36px;
}

.course-card {
    background-color: #f9f9f9;
    border: 1px solid var(--color-gray);
    border-radius: 12px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.card-header .course-code {
    color: var(--color-dark-gray);
    display: block;
}

.card-stats {
    display: flex;
    gap: 24px;
    color: var(--color-dark-gray);
}

.card-actions {
    display: flex;
    justify-content: space-between;
    gap: 12px;
}

.empty-state {
    text-align: center;
    padding: 80px;
}
</style>