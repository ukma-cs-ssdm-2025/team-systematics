<template>
    <div>
        <Header />
        <main class="container">
            <div v-if="loading" class="status-message">Завантаження іспитів...</div>
            <div v-else-if="error" class="status-message error">{{ error }}</div>

            <div v-else>
                <div class="page-header">
                    <h1>Іспити курсу {{ courseName }}</h1>
                    <CButton @click="createNewExam" class="create-exam-btn">
                        + Створити новий іспит
                    </CButton>
                </div>

                <section class="exams-section">
                    <table v-if="exams.length" class="exams-table">
                        <thead>
                            <tr>
                                <th class="left"><span class="pill">Назва іспиту</span></th>
                                <th class="left"><span class="pill">Статус</span></th>
                                <th class="right"><span class="pill">К-сть питань</span></th>
                                <th class="right"><span class="pill">Студентів склало</span></th>
                                <th class="right"><span class="pill">Середній бал</span></th>
                                <th class="right"><span class="pill">Дії</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="exam in exams" :key="exam.id">
                                <td class="left exam-title">
                                    <div class="title-container">
                                        <span>{{ exam.title }}</span>
                                        <CTooltip v-if="exam.pending_reviews > 0">
                                            <template #trigger>
                                                <span class="info-icon">{{ exam.pending_reviews }}</span>
                                            </template>
                                            <template #content>
                                                <p><strong>{{ exam.pending_reviews }}</strong> робіт потребують вашої
                                                    ручної перевірки.</p>
                                            </template>
                                        </CTooltip>
                                    </div>
                                </td>
                                <td class="left">{{ exam.status }}</td>
                                <td class="right">{{ exam.questions_count }}</td>
                                <td class="right">{{ exam.students_completed }}</td>
                                <td class="right">{{ exam.average_grade || '--' }}</td>
                                <td class="right actions-cell">

                                    <button @click="goToExamJournal(exam.id)" class="icon-button"
                                        aria-label="Перейти до журналу і перевірки робот" title="Журнал і перевірка">
                                        📖
                                    </button>
                                    <button class="icon-button" aria-label="Перейти до редагування питань іспиту"
                                        title="Редагувати питання">✏️</button>
                                    <button class="icon-button" aria-label="Видалити іспит"
                                        title="Видалити іспит">🗑️</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <p v-else class="empty-list-message">Для цього курсу ще не створено жодного іспиту.</p>
                </section>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import CTooltip from '../components/global/CTooltip.vue'
import { getCourseExams } from '../api/courses.js'

const route = useRoute()
const router = useRouter()
const courseId = route.params.id

const exams = ref([])
const courseName = ref('')
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
    try {
        const response = await getCourseExams(courseId)
        exams.value = response.exams
        courseName.value = response.course_name
        document.title = `Іспити курсу ${courseName.value} | Systematics`
    } catch (err) {
        error.value = err.message
    } finally {
        loading.value = false
    }
})

function goToExamJournal(examId) {
    router.push(`/exams/${examId}/journal`)
}

function createNewExam() {
    router.push(`/exams/create`)
}

function editExam(examId) {
    router.push(`/exams/${examId}/edit`)
}
</script>

<style scoped>
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.exam-title {
    font-weight: bold;
}

.title-container {
    display: flex;
    align-items: center;
    gap: 12px; 
}

.tooltip {
    font-weight: 200;
}

.actions-cell {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px
}

.info-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background-color: var(--color-orange);
    color: var(--color-white);
    font-weight: bold;
    font-size: 0.8rem;
    cursor: help;
    user-select: none;
}

.icon-button {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
    padding: 4px;
    border-radius: 50%;
}

.icon-button:hover {
    background-color: #f0f0f0
}
</style>