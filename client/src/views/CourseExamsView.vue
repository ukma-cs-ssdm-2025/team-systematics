<template>
    <div>
        <Header />
        <main class="container">
            <div v-if="loading" class="status-message">Завантаження іспитів...</div>
            <div v-else-if="error" class="status-message error">{{ error }}</div>

            <div v-else>
                <section class="exams-section">
                    <div class="page-header">
                        <h2>Іспити курсу {{ courseName }}</h2>
                        <CButton @click="createNewExam" class="create-exam-btn">
                            + Створити новий іспит
                        </CButton>
                    </div>
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
                                <td class="left">{{ statusLabel(exam) }}</td>
                                <td class="right">{{ exam.questions_count }}</td>
                                <td class="right">{{ exam.students_completed }}</td>
                                <td class="right">{{ formatAverageGrade(exam.average_grade)     }}</td>
                                <td class="right actions-cell" style="vertical-align: middle;">
                                    <div class="actions-wrapper">
                                        <CButton v-if="exam.status === 'draft'" 
                                            @click="showPublishConfirm(exam.id)" 
                                            variant="green"
                                            :disabled="publishingExamId === exam.id"
                                            aria-label="Опублікувати іспит" 
                                            title="Опублікувати іспит"
                                            class="publish-button">
                                            {{ publishingExamId === exam.id ? '...' : '📢 Опублікувати' }}
                                        </CButton>
                                        <button @click="goToExamJournal(exam.id)" class="icon-button"
                                            aria-label="Перейти до журналу і перевірки робот" title="Журнал і перевірка">
                                            📖
                                        </button>
                                        <button @click="editExam(exam.id)" class="icon-button" aria-label="Перейти до редагування питань іспиту"
                                            title="Редагувати питання">✏️</button>
                                        <button @click="showDeleteConfirm(exam.id)" class="icon-button" aria-label="Видалити іспит"
                                            title="Видалити іспит">🗑️</button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <p v-else class="empty-list-message">Для цього курсу ще не створено жодного іспиту.</p>
                </section>
            </div>
        </main>
        
        <!-- Попап підтвердження публікації -->
        <CPopup
            v-if="examToPublish"
            :visible="showPublishDialog"
            header="Підтвердження публікації іспиту"
            :disclaimer="publishConfirmMessage"
            fst-button="Опублікувати"
            snd-button="Скасувати"
            fst-button-variant="green"
            @fstAction="confirmPublishExam"
            @sndAction="cancelPublishExam"
        />
        
        <!-- Попап підтвердження видалення -->
        <CPopup
            v-if="examToDelete"
            :visible="showDeleteDialog"
            header="Підтвердження видалення іспиту"
            :disclaimer="deleteConfirmMessage"
            fst-button="Видалити"
            snd-button="Скасувати"
            fst-button-variant="red"
            @fstAction="confirmDeleteExam"
            @sndAction="cancelDeleteExam"
        />
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import CTooltip from '../components/global/CTooltip.vue'
import CPopup from '../components/global/CPopup.vue'
import { getCourseExams } from '../api/courses.js'
import { publishExam as publishExamAPI, deleteExam as deleteExamAPI } from '../api/exams.js'

const route = useRoute()
const router = useRouter()
const courseId = route.params.courseId

const exams = ref([])
const courseName = ref('')
const loading = ref(true)
const error = ref(null)
const publishingExamId = ref(null)
const showDeleteDialog = ref(false)
const examToDelete = ref(null)
const showPublishDialog = ref(false)
const examToPublish = ref(null)

function statusLabel(exam) {
    if (!exam || !exam.status) return 'Не вказано'

    switch (exam.status) {
        case 'draft':
            return 'Чернетка'
        case 'published':
            return 'Опубліковано'
        case 'open':
            return 'Відкрито'
        case 'closed':
            return 'Закрито'
        default:
            return 'Не вказано'
    }
}

function formatAverageGrade(grade) {
    if (!grade) return '--'
    return Math.ceil(grade)
}

onMounted(async () => {
    await loadExams()
})

function goToExamJournal(examId) {
    router.push(`/exams/${examId}/journal`)
}

function createNewExam() {
    router.push(`/courses/${courseId}/exams/create`)
}

function editExam(examId) {
    router.push(`/courses/${courseId}/exams/${examId}/edit`)
}

function showPublishConfirm(examId) {
    examToPublish.value = examId
    showPublishDialog.value = true
}

function cancelPublishExam() {
    showPublishDialog.value = false
    examToPublish.value = null
}

async function confirmPublishExam() {
    if (!examToPublish.value) return
    if (publishingExamId.value === examToPublish.value) return
    
    const examId = examToPublish.value
    showPublishDialog.value = false
    examToPublish.value = null
    
    try {
        publishingExamId.value = examId
        await publishExamAPI(examId)
        // Оновлюємо статус іспиту в списку
        const exam = exams.value.find(e => e.id === examId)
        if (exam) {
            exam.status = 'published'
        }
    } catch (err) {
        console.error('Помилка публікації іспиту:', err)
        error.value = err.message || 'Не вдалося опублікувати іспит'
        // Оновлюємо список іспитів для відображення актуального стану
        await loadExams()
    } finally {
        publishingExamId.value = null
    }
}

async function loadExams() {
    try {
        loading.value = true
        const response = await getCourseExams(courseId)
        exams.value = response.exams
        courseName.value = response.course_name
        document.title = `Іспити курсу ${courseName.value} | Systematics`
    } catch (err) {
        error.value = err.message
    } finally {
        loading.value = false
    }
}

function showDeleteConfirm(examId) {
    examToDelete.value = examId
    showDeleteDialog.value = true
}

function cancelDeleteExam() {
    showDeleteDialog.value = false
    examToDelete.value = null
}

async function confirmDeleteExam() {
    if (!examToDelete.value) return
    
    try {
        await deleteExamAPI(examToDelete.value)
        showDeleteDialog.value = false
        examToDelete.value = null
        // Оновлюємо список іспитів
        await loadExams()
    } catch (err) {
        console.error('Помилка видалення іспиту:', err)
        error.value = err.message || 'Не вдалося видалити іспит'
        showDeleteDialog.value = false
        examToDelete.value = null
    }
}

function getExamTitle(examId) {
    const exam = exams.value.find(e => e.id === examId)
    return exam ? exam.title : 'невідомий іспит'
}

const deleteConfirmMessage = computed(() => {
    if (!examToDelete.value) return ''
    const examTitle = getExamTitle(examToDelete.value)
    return `Ви впевнені, що хочете видалити іспит "${examTitle}"? Цю дію неможливо скасувати.`
})

const publishConfirmMessage = computed(() => {
    if (!examToPublish.value) return ''
    const examTitle = getExamTitle(examToPublish.value)
    return `Ви впевнені, що хочете опублікувати іспит "${examTitle}"? Після публікації іспит стане видимим для студентів курсу.`
})
</script>

<style scoped>
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
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
    vertical-align: middle !important;
}

.actions-wrapper {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
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

.publish-button {
    padding: 8px 16px;
    font-size: 0.9rem;
    white-space: nowrap;
}
</style>