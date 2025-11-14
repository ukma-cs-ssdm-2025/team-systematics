<template>
    <div>
        <Header />
        <main class="container">
            <Breadcrumbs />
            <div v-if="loading" class="status-message">Завантаження...</div>
            <div v-else-if="error" class="status-message error">{{ error }}</div>

            <div v-else>
                <div class="exams-section">
                    <div class="page-header">
                        <h2>Управління сесією іспиту: {{ examName }}</h2>
                    </div>

                    <!-- Інформація про іспит -->
                    <div class="exam-info">
                        <div class="exam-info-row">
                            <p><strong>Курс:</strong> {{ courseName }}</p>
                            <p><strong>Статус іспиту:</strong> {{ examStatusLabel }}</p>
                        </div>
                        <div v-if="examStatus === 'draft'" class="publish-section">
                            <CButton 
                                @click="showPublishConfirm"
                                variant="green"
                                :disabled="publishingExam"
                            >
                                {{ publishingExam ? 'Публікація...' : '📢 Опублікувати' }}
                            </CButton>
                        </div>
                    </div>

                    <!-- Список учасників -->
                    <div class="participants-section">
                        <div class="section-header">
                            <h3>Учасники іспиту ({{ participants.length }})</h3>
                        </div>

                        <table v-if="participants.length > 0" class="exams-table">
                            <colgroup>
                                <col style="width: 30%">
                                <col style="width: 25%">
                                <col style="width: 15%">
                                <col style="width: 20%">
                                <col style="width: 10%">
                            </colgroup>
                            <thead>
                                <tr>
                                    <th class="left"><span class="pill sortable" @click="sortBy('name')">
                                        ПІБ студента
                                        <span v-if="sortState.key === 'name'" class="sort-indicator">
                                            {{ sortState.order === 'asc' ? '↑' : '↓' }}
                                        </span>
                                    </span></th>
                                    <th class="left"><span class="pill sortable" @click="sortBy('email')">
                                        Email
                                        <span v-if="sortState.key === 'email'" class="sort-indicator">
                                            {{ sortState.order === 'asc' ? '↑' : '↓' }}
                                        </span>
                                    </span></th>
                                    <th class="left"><span class="pill sortable" @click="sortBy('attendance')">
                                        Присутність
                                        <span v-if="sortState.key === 'attendance'" class="sort-indicator">
                                            {{ sortState.order === 'asc' ? '↑' : '↓' }}
                                        </span>
                                    </span></th>
                                    <th class="left"><span class="pill sortable" @click="sortBy('joined_at')">
                                        Додано
                                        <span v-if="sortState.key === 'joined_at'" class="sort-indicator">
                                            {{ sortState.order === 'asc' ? '↑' : '↓' }}
                                        </span>
                                    </span></th>
                                    <th class="right"><span class="pill">Дії</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="participant in sortedParticipants" :key="participant.user_id">
                                    <td class="left">{{ getParticipantName(participant.user_id) }}</td>
                                    <td class="left">{{ getParticipantEmail(participant.user_id) }}</td>
                                    <td class="left">
                                        <span :class="['attendance-badge', isParticipantPresent(participant.user_id) ? 'present' : 'absent']">
                                            {{ isParticipantPresent(participant.user_id) ? 'Присутній' : 'Відсутній' }}
                                        </span>
                                    </td>
                                    <td class="left">{{ formatDate(participant.joined_at) }}</td>
                                    <td class="right">
                                        <button 
                                            @click="showRemoveConfirm(participant.user_id)"
                                            class="icon-button remove-button"
                                            :disabled="removingUserId === participant.user_id"
                                            title="Видалити з іспиту"
                                        >
                                            {{ removingUserId === participant.user_id ? '...' : '🗑️' }}
                                        </button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <p v-else class="empty-list-message">Немає учасників іспиту</p>
                    </div>

                    <!-- Моніторинг активних спроб -->
                    <div class="active-attempts-section" v-if="examStatus === 'open'">
                        <div class="section-header">
                            <h3>Активні спроби ({{ activeAttempts.length }})</h3>
                            <CButton @click="loadActiveAttempts" :disabled="loadingActiveAttempts" variant="secondary" size="small">
                                {{ loadingActiveAttempts ? 'Оновлення...' : '🔄 Оновити' }}
                            </CButton>
                        </div>

                        <table v-if="activeAttempts.length > 0" class="exams-table">
                            <colgroup>
                                <col style="width: 35%">
                                <col style="width: 20%">
                                <col style="width: 20%">
                                <col style="width: 15%">
                                <col style="width: 10%">
                            </colgroup>
                            <thead>
                                <tr>
                                    <th class="left"><span class="pill">ПІБ студента</span></th>
                                    <th class="left"><span class="pill">Початок</span></th>
                                    <th class="left"><span class="pill">Залишилось</span></th>
                                    <th class="left"><span class="pill">Додати час</span></th>
                                    <th class="right"></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="attempt in activeAttempts" :key="attempt.attempt_id">
                                    <td class="left">{{ attempt.user_full_name }}</td>
                                    <td class="left">{{ formatTime(attempt.started_at) }}</td>
                                    <td class="left">
                                        <span :class="{ 'warning-time': attempt.remaining_minutes < 5 }">
                                            {{ formatRemainingTime(attempt.remaining_minutes) }}
                                        </span>
                                    </td>
                                    <td class="left">
                                        <select 
                                            v-model="selectedAdditionalTime[attempt.attempt_id]"
                                            class="time-select"
                                            :disabled="addingTimeToAttempt === attempt.attempt_id"
                                        >
                                            <option :value="null">Оберіть...</option>
                                            <option :value="5">+5 хв</option>
                                            <option :value="10">+10 хв</option>
                                            <option :value="15">+15 хв</option>
                                            <option :value="30">+30 хв</option>
                                        </select>
                                    </td>
                                    <td class="right">
                                        <CButton 
                                            @click="addTime(attempt.attempt_id)"
                                            :disabled="!selectedAdditionalTime[attempt.attempt_id] || addingTimeToAttempt === attempt.attempt_id"
                                            size="small"
                                        >
                                            {{ addingTimeToAttempt === attempt.attempt_id ? '...' : 'Додати' }}
                                        </CButton>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <p v-else class="empty-list-message">Немає активних спроб</p>
                    </div>

                    <!-- Додавання нового учасника -->
                    <div class="add-participant-section">
                        <div class="section-header">
                            <h3>Додати студента до іспиту</h3>
                        </div>
                        
                        <div class="add-participant-controls">
                            <CSelect 
                                v-model="selectedStudentId" 
                                :options="studentSelectOptions"
                                placeholder="Оберіть..."
                                :disabled="addingParticipant || !availableStudents.length"
                            />
                            <CButton 
                                @click="addParticipant"
                                :disabled="!selectedStudentId || addingParticipant || examStatus === 'closed'"
                                variant="green"
                            >
                                {{ addingParticipant ? 'Додавання...' : '+ Додати' }}
                            </CButton>
                        </div>
                        <p v-if="examStatus === 'closed'" class="warning-message">
                            Неможливо додавати учасників до закритого іспиту
                        </p>
                    </div>
                </div>
            </div>
        </main>

        <!-- Попап підтвердження публікації -->
        <CPopup
            v-if="showPublishDialog"
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
            v-if="userToRemove"
            :visible="showRemoveDialog"
            header="Підтвердження видалення"
            :disclaimer="removeConfirmMessage"
            fst-button="Видалити"
            snd-button="Скасувати"
            fst-button-variant="red"
            @fstAction="confirmRemoveParticipant"
            @sndAction="cancelRemoveParticipant"
        />
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, reactive } from 'vue'
import { useRoute } from 'vue-router'
import Header from '../components/global/Header.vue'
import Breadcrumbs from '../components/global/Breadcrumbs.vue'
import CButton from '../components/global/CButton.vue'
import CPopup from '../components/global/CPopup.vue'
import CSelect from '../components/global/CSelect.vue'
import { getExamParticipants, addExamParticipant, removeExamParticipant } from '../api/examParticipants.js'
import { getExam, publishExam } from '../api/exams.js'
import { getCourseDetailsForSupervisor } from '../api/courses.js'
import { getActiveAttemptsForExam, getCompletedAttemptsForExam, addTimeToAttempt } from '../api/attempts.js'

const route = useRoute()
const examId = route.params.examId

const loading = ref(true)
const error = ref(null)
const participants = ref([])
const examName = ref('')
const examStatus = ref('')
const courseId = ref(null)
const courseName = ref('')
const courseStudents = ref([])
const selectedStudentId = ref('')
const addingParticipant = ref(false)
const removingUserId = ref(null)
const showRemoveDialog = ref(false)
const userToRemove = ref(null)
const activeAttempts = ref([])
const loadingActiveAttempts = ref(false)
const selectedAdditionalTime = ref({})
const addingTimeToAttempt = ref(null)
const studentsWithCompletedAttempts = ref(new Set()) // Set з user_id студентів, які мають завершені спроби
const showPublishDialog = ref(false)
const publishingExam = ref(false)

const sortState = reactive({
    key: null, // Поле, за яким сортуємо
    order: 'asc' // Напрямок сортування
})

const examStatusLabel = computed(() => {
    switch (examStatus.value) {
        case 'draft':
            return 'Чернетка'
        case 'published':
            return 'Опубліковано'
        case 'open':
            return 'Відкрито'
        case 'closed':
            return 'Закрито'
        default:
            return examStatus.value || 'Невідомо'
    }
})

const availableStudents = computed(() => {
    // Фільтруємо студентів, які ще не є учасниками
    const participantIds = new Set(participants.value.map(p => p.user_id))
    return courseStudents.value.filter(student => !participantIds.has(student.id))
})

const studentSelectOptions = computed(() => {
    return availableStudents.value.map(student => ({
        value: student.id,
        text: `${student.full_name} (${student.email})`
    }))
})

const sortedParticipants = computed(() => {
    if (!sortState.key) {
        return participants.value
    }
    
    const sorted = [...participants.value]
    
    sorted.sort((a, b) => {
        let aValue, bValue
        
        switch (sortState.key) {
            case 'name':
                aValue = getParticipantName(a.user_id).toLowerCase()
                bValue = getParticipantName(b.user_id).toLowerCase()
                break
            case 'email':
                aValue = getParticipantEmail(a.user_id).toLowerCase()
                bValue = getParticipantEmail(b.user_id).toLowerCase()
                break
            case 'attendance':
                aValue = isParticipantPresent(a.user_id) ? 1 : 0
                bValue = isParticipantPresent(b.user_id) ? 1 : 0
                break
            case 'joined_at':
                aValue = a.joined_at ? new Date(a.joined_at).getTime() : 0
                bValue = b.joined_at ? new Date(b.joined_at).getTime() : 0
                break
            default:
                return 0
        }
        
        if (aValue < bValue) {
            return sortState.order === 'asc' ? -1 : 1
        }
        if (aValue > bValue) {
            return sortState.order === 'asc' ? 1 : -1
        }
        return 0
    })
    
    return sorted
})

function getParticipantName(userId) {
    const student = courseStudents.value.find(s => s.id === userId)
    return student ? student.full_name : 'Невідомо'
}

function getParticipantEmail(userId) {
    const student = courseStudents.value.find(s => s.id === userId)
    return student ? student.email : 'Невідомо'
}

function isParticipantPresent(userId) {
    // Перевіряємо, чи є у студента активна спроба АБО завершена спроба
    // Нормалізуємо user_id до рядка для порівняння
    const userIdStr = String(userId).toLowerCase().trim()
    
    const hasActiveAttempt = activeAttempts.value.some(attempt => {
        const attemptUserIdStr = String(attempt.user_id || attempt.userId || '').toLowerCase().trim()
        return attemptUserIdStr === userIdStr
    })
    
    // Перевіряємо всі можливі формати user_id в Set
    let hasCompletedAttempt = false
    for (const completedId of studentsWithCompletedAttempts.value) {
        const completedIdStr = String(completedId).toLowerCase().trim()
        if (completedIdStr === userIdStr) {
            hasCompletedAttempt = true
            break
        }
    }
    
    return hasActiveAttempt || hasCompletedAttempt
}

function sortBy(key) {
    // Якщо клікнули на ту саму колонку, змінюємо напрямок
    if (sortState.key === key) {
        sortState.order = sortState.order === 'asc' ? 'desc' : 'asc'
    } else {
        // Якщо клікнули на нову колонку, встановлюємо її і скидаємо напрямок
        sortState.key = key
        sortState.order = 'asc'
    }
}

function formatDate(dateString) {
    if (!dateString) return '—'
    const date = new Date(dateString)
    return date.toLocaleString('uk-UA', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    })
}

function formatTime(dateString) {
    if (!dateString) return '—'
    const date = new Date(dateString)
    return date.toLocaleTimeString('uk-UA', {
        hour: '2-digit',
        minute: '2-digit'
    })
}

function formatRemainingTime(minutes) {
    if (minutes < 0) return 'Час вийшов'
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours > 0) {
        return `${hours} год ${mins} хв`
    }
    return `${mins} хв`
}

async function loadActiveAttempts() {
    try {
        loadingActiveAttempts.value = true
        const attempts = await getActiveAttemptsForExam(examId)
        activeAttempts.value = attempts
        // Оновлюємо також список завершених спроб, щоб статуси присутності були актуальними
        await loadCompletedAttempts()
    } catch (err) {
        console.error('Помилка завантаження активних спроб:', err)
        // Не встановлюємо помилку як критичну, оскільки це може бути нормально, якщо немає активних спроб
        if (err.message && !err.message.includes('404')) {
            error.value = err.message || 'Не вдалося завантажити активні спроби'
        }
    } finally {
        loadingActiveAttempts.value = false
    }
}

async function loadCompletedAttempts() {
    if (!examId) {
        return
    }
    
    try {
        // Завантажуємо завершені спроби через новий endpoint для наглядачів
        const completedAttemptsData = await getCompletedAttemptsForExam(examId)
        
        // Створюємо Set з user_id студентів, які мають завершені спроби
        const completedUserIds = new Set()
        
        completedAttemptsData.forEach(attempt => {
            const userId = String(attempt.user_id).toLowerCase().trim()
            completedUserIds.add(userId)
        })
        
        studentsWithCompletedAttempts.value = completedUserIds
    } catch (err) {
        // Не встановлюємо помилку як критичну, оскільки це не критично для роботи
    }
}

async function addTime(attemptId) {
    const additionalMinutes = selectedAdditionalTime.value[attemptId]
    if (!additionalMinutes) return
    
    try {
        addingTimeToAttempt.value = attemptId
        await addTimeToAttempt(attemptId, additionalMinutes)
        // Оновлюємо список активних спроб
        await loadActiveAttempts()
        // Очищаємо вибір
        selectedAdditionalTime.value[attemptId] = null
    } catch (err) {
        console.error('Помилка додавання часу:', err)
        error.value = err.message || 'Не вдалося додати час'
        alert(err.message || 'Не вдалося додати час')
    } finally {
        addingTimeToAttempt.value = null
    }
}

function showRemoveConfirm(userId) {
    userToRemove.value = userId
    showRemoveDialog.value = true
}

function cancelRemoveParticipant() {
    showRemoveDialog.value = false
    userToRemove.value = null
}

async function confirmRemoveParticipant() {
    if (!userToRemove.value) return
    
    const userId = userToRemove.value
    showRemoveDialog.value = false
    userToRemove.value = null
    
    try {
        removingUserId.value = userId
        await removeExamParticipant(examId, userId)
        // Оновлюємо список учасників
        await loadParticipants()
    } catch (err) {
        console.error('Помилка видалення учасника:', err)
        error.value = err.message || 'Не вдалося видалити учасника'
    } finally {
        removingUserId.value = null
    }
}

async function addParticipant() {
    if (!selectedStudentId.value) return
    
    try {
        addingParticipant.value = true
        await addExamParticipant(examId, selectedStudentId.value, courseId.value)
        selectedStudentId.value = ''
        // Оновлюємо список учасників
        await loadParticipants()
    } catch (err) {
        console.error('Помилка додавання учасника:', err)
        error.value = err.message || 'Не вдалося додати студента до іспиту'
        alert(err.message || 'Не вдалося додати студента до іспиту')
    } finally {
        addingParticipant.value = false
    }
}

async function loadParticipants() {
    try {
        const data = await getExamParticipants(examId)
        participants.value = data
    } catch (err) {
        console.error('Помилка завантаження учасників:', err)
        throw err
    }
}

async function loadExamAndCourse() {
    try {
        // Завантажуємо інформацію про іспит
        const exam = await getExam(examId)
        examName.value = exam.title
        examStatus.value = exam.status
        
        // Отримуємо course_id з route параметрів (обов'язковий параметр)
        const courseIdFromRoute = route.params.courseId
        
        if (!courseIdFromRoute) {
            throw new Error('Не вдалося визначити курс для іспиту. Перевірте URL.')
        }
        
        courseId.value = courseIdFromRoute
        const courseDetails = await getCourseDetailsForSupervisor(courseIdFromRoute)
        courseName.value = courseDetails.name || courseDetails.code || 'Невідомий курс'
        courseStudents.value = courseDetails.students || []
    } catch (err) {
        console.error('Помилка завантаження даних іспиту:', err)
        throw err
    }
}

const removeConfirmMessage = computed(() => {
    if (!userToRemove.value) return ''
    const studentName = getParticipantName(userToRemove.value)
    return `Ви впевнені, що хочете видалити студента "${studentName}" зі списку учасників іспиту? Якщо студент проходить іспит зараз, його сесія буде автоматично завершена.`
})

const publishConfirmMessage = computed(() => {
    return `Ви впевнені, що хочете опублікувати іспит "${examName.value}"? Після публікації іспит стане видимим для студентів курсу.`
})

function showPublishConfirm() {
    showPublishDialog.value = true
}

function cancelPublishExam() {
    showPublishDialog.value = false
}

async function confirmPublishExam() {
    if (publishingExam.value) return
    
    showPublishDialog.value = false
    
    try {
        publishingExam.value = true
        await publishExam(examId)
        // Оновлюємо статус іспиту
        examStatus.value = 'published'
        // Оновлюємо дані іспиту
        await loadExamAndCourse()
    } catch (err) {
        console.error('Помилка публікації іспиту:', err)
        error.value = err.message || 'Не вдалося опублікувати іспит'
        alert(err.message || 'Не вдалося опублікувати іспит')
    } finally {
        publishingExam.value = false
    }
}

// Зберігаємо інтервал для автоматичного оновлення
let refreshInterval = null

onMounted(async () => {
    try {
        loading.value = true
        await loadExamAndCourse()
        await loadParticipants()
        // Завантажуємо завершені спроби для відображення присутності
        await loadCompletedAttempts()
        
        // Завантажуємо активні спроби, якщо іспит відкритий
        if (examStatus.value === 'open') {
            await loadActiveAttempts()
            
            // Автоматично оновлюємо список активних спроб кожні 10 секунд
            // Також оновлюємо завершені спроби, щоб статуси присутності були актуальними
            refreshInterval = setInterval(() => {
                if (examStatus.value === 'open' && !loadingActiveAttempts.value) {
                    loadActiveAttempts()
                } else if (!loadingActiveAttempts.value) {
                    // Навіть якщо іспит не відкритий, оновлюємо завершені спроби для коректного відображення статусів
                    loadCompletedAttempts()
                }
            }, 10000) // 10 секунд
        } else {
            // Якщо іспит не відкритий, все одно завантажуємо активні спроби для відображення присутності
            // (на випадок, якщо є спроби, які ще не завершені)
            await loadActiveAttempts()
        }
    } catch (err) {
        error.value = err.message || 'Сталася невідома помилка.'
    } finally {
        loading.value = false
    }
})

onUnmounted(() => {
    // Очищаємо інтервал при розмонтуванні компонента
    if (refreshInterval) {
        clearInterval(refreshInterval)
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

.exam-info {
    background-color: #f9f9f9;
    border: 1px solid var(--color-gray);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 24px;
}

.exam-info-row {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.exam-info p {
    margin: 0;
}

.publish-section {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--color-gray);
    display: flex;
    justify-content: flex-start;
}

.participants-section,
.add-participant-section {
    margin-bottom: 32px;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.section-header h3 {
    margin: 0;
    font-size: 1.2rem;
}

.active-attempts-section {
    margin-bottom: 32px;
}

.time-select {
    padding: 6px 12px;
    border: 1px solid var(--color-light-gray);
    border-radius: 8px;
    font-size: 14px;
    background-color: white;
}

.time-select:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.warning-time {
    color: var(--color-red);
    font-weight: bold;
}

.add-participant-controls {
    display: flex;
    gap: 12px;
    align-items: center;
}

.add-participant-controls .custom-select {
    flex: 1;
}


.warning-message {
    color: var(--color-red);
    font-size: 0.9rem;
    margin-top: 8px;
}

.icon-button {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
    padding: 4px;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.icon-button:hover:not(:disabled) {
    background-color: #f0f0f0;
}

.icon-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.remove-button {
    color: var(--color-red);
}

.empty-list-message {
    text-align: center;
    padding: 24px;
    color: var(--color-dark-gray);
    font-style: italic;
}

.attendance-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.9rem;
    font-weight: 500;
    white-space: nowrap;
}

.attendance-badge.present {
    background-color: var(--color-green);
    /* Колір тексту залишається дефолтним */
}

.attendance-badge.absent {
    background-color: var(--color-red);
}

.sortable {
    cursor: pointer;
    user-select: none;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.sortable:hover {
    opacity: 0.8;
}

.sort-indicator {
    font-size: 0.8rem;
    color: var(--color-violet);
    font-weight: bold;
}
</style>

