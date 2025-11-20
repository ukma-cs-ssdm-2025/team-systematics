<template>
    <div>
        <Header />
        <main class="container">
            <Breadcrumbs />
            <div v-if="loading" class="status-message">Завантаження деталей курсу...</div>
            <div v-else-if="error" class="status-message error">{{ error }}</div>

            <div v-else-if="course">
                <div class="exams-section">
                    <div class="page-header">
                        <h2>{{ course.name }} ({{ course.code }})</h2>
                    </div>

                    <!-- Студенти -->
                    <div class="participants-section">
                        <h3>Студенти ({{ course.students?.length || 0 }})</h3>
                        <table v-if="course.students && course.students.length > 0" class="exams-table">
                            <colgroup>
                                <col style="width: 35%">
                                <col style="width: 40%">
                                <col style="width: 25%">
                            </colgroup>
                            <thead>
                                <tr>
                                    <th class="left"><span class="pill">ПІБ студента</span></th>
                                    <th class="left"><span class="pill">Email</span></th>
                                    <th class="left"><span class="pill">Статус</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="student in course.students" :key="student.id">
                                    <td class="left">{{ student.full_name }}</td>
                                    <td class="left">{{ student.email }}</td>
                                    <td class="left">
                                        <span class="status-pill enrolled">Зараховано</span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <p v-else class="empty-list-message">Немає зареєстрованих студентів</p>
                    </div>

                    <!-- Викладачі -->
                    <div class="participants-section">
                        <h3>Викладачі ({{ course.teachers?.length || 0 }})</h3>
                        <table v-if="course.teachers && course.teachers.length > 0" class="exams-table">
                            <colgroup>
                                <col style="width: 35%">
                                <col style="width: 40%">
                                <col style="width: 25%">
                            </colgroup>
                            <thead>
                                <tr>
                                    <th class="left"><span class="pill">ПІБ викладача</span></th>
                                    <th class="left"><span class="pill">Email</span></th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="teacher in course.teachers" :key="teacher.id">
                                    <td class="left">{{ teacher.full_name }}</td>
                                    <td class="left">{{ teacher.email }}</td>
                                    <td></td>
                                </tr>
                            </tbody>
                        </table>
                        <p v-else class="empty-list-message">Немає зареєстрованих викладачів</p>
                    </div>

                    <div class="page-header" style="margin-top: 32px;">
                        <CButton @click="viewCourseExams">Переглянути іспити</CButton>
                    </div>
                </div>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import Breadcrumbs from '../components/global/Breadcrumbs.vue'
import CButton from '../components/global/CButton.vue'
import { getCourseDetailsForSupervisor } from '../api/courses.js'

const route = useRoute()
const router = useRouter()
const courseId = route.params.courseId

const loading = ref(true)
const error = ref(null)
const course = ref(null)

function viewCourseExams() {
    router.push(`/courses/${courseId}/exams`)
}

onMounted(async () => {
    try {
        loading.value = true
        const details = await getCourseDetailsForSupervisor(courseId)
        if (details?.message) {
            error.value = details.message
        } else {
            course.value = details
            document.title = `${details.name} (${details.code}) | Systematics`
        }
    } catch (err) {
        error.value = err.message || 'Не вдалося завантажити деталі курсу.'
    } finally {
        loading.value = false
    }
})
</script>

<style scoped>
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
}

.participants-section {
    margin-bottom: 32px;
}

.participants-section:last-child {
    margin-bottom: 0;
}

.participants-section h3 {
    margin-bottom: 16px;
    font-size: 1.2rem;
}

.status-pill {
    padding: 4px 12px;
    border-radius: 12px;
    white-space: nowrap;
    display: inline-block;
}

.status-pill.enrolled {
    background-color: var(--color-green-half-opacity);
}

.empty-list-message {
    text-align: center;
    padding: 24px;
    color: var(--color-dark-gray);
    font-style: italic;
}
</style>

