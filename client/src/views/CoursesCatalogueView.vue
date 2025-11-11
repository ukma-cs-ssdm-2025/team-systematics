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
                        <span class="course-code">{{ course.code }}</span>
                        <h3 class="course-name">{{ course.name }}</h3>
                        <div v-if="course.description" class="card-description">
                            <p>{{ course.description }}</p>
                        </div>
                        <div class="card-stats">
                            <span>👩‍🎓 {{ course.student_count }} студентів</span>
                            <span>📝 {{ course.exam_count }} іспитів</span>
                        </div>
                        <div class="card-actions">
                            <CButton v-if="auth.isTeacher.value" @click="goToExams(course.id)">Керувати</CButton>
                            <CButton 
                                v-if="auth.isStudent.value" 
                                @click="handleEnroll(course)" 
                                :disabled="course.is_enrolled || isEnrolling[course.id]"
                            >
                                <span v-if="isEnrolling[course.id]">Запис...</span>
                                <span v-else-if="course.is_enrolled">✔ Ви записані</span>
                                <span v-else>Записатися</span>
                            </CButton>
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
import { getMyCourses, getAllCourses, enrollInCourse } from '../api/courses.js'
import { useAuth } from '../store/loginInfo.js'

const router = useRouter()
const courses = ref([])
const loading = ref(true)
const error = ref(null)
const isEnrolling = ref({})

const auth = useAuth()
const header = computed(() => {
    return auth.isTeacher.value ? 'Мої курси' : 'Каталог курсів'
})

onMounted(async () => {
    try {
        if (auth.isTeacher.value) {
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

async function handleEnroll(course) {
    isEnrolling.value[course.id] = true
    try {
        await enrollInCourse(course.id)
        course.is_enrolled = true
    } catch (err) {
        alert(err.message || 'Не вдалося записатися на курс.')
    } finally {
        isEnrolling.value[course.id] = false
    }
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

.course-code {
    color: var(--color-dark-gray);
    display: block;
}

.course-name {
    margin: 0;
}

.card-description {
    color: var(--color-dark-gray);
    font-size: 0.9rem;
    line-height: 1.5;
}

.card-description p {
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
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