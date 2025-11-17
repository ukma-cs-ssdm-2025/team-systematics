<template>
    <div>
        <Header />
        <main class="container" v-if="!loading">
            <Breadcrumbs />
            <!-- 1. Стан завантаження -->
            <div v-if="loading" class="status-message">
                Завантаження списку іспитів...
            </div>

            <!-- 2. Стан помилки -->
            <div v-if="error" class="status-message error">
                Помилка завантаження: {{ error }}
            </div>

            <!-- 3. Основний контент, коли дані завантажено -->
            <div v-if="!loading && !error">
                <!-- Секція для відкритих іспитів -->
                <div v-if="openExams.length" class="exams-section">
                    <h2>Відкриті іспити</h2>
                    <table class="exams-table">
                        <thead>
                            <tr>
                                <th class="left"><span class="pill">Назва іспиту</span></th>
                                <th class="left"><span class="pill">Час початку</span></th>
                                <th class="left"><span class="pill">Час закінчення</span></th>
                                <th class="right"><span class="pill">Тривалість</span></th>
                                <th class="right"><span class="pill">К-сть спроб</span></th>
                                <th class="right"><span class="pill">Прохідний бал</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="exam in openExams" :key="exam.id">
                                <td 
                                    class="exam-title left"
                                    @click="openStartExamPopup(exam)">
                                    {{ exam.title }}
                                </td>
                                <td class="left">{{ formatDateTime(exam.start_at) }}</td>
                                <td class="left">{{ formatDateTime(exam.end_at) }}</td>
                                <td class="right">{{ exam.duration_minutes }} хв</td>
                                <td class="right">{{ exam.max_attempts }}</td>
                                <td class="right">{{ exam.pass_threshold }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Секція для майбутніх іспитів -->
                <div class="exams-section">
                    <h2>Майбутні іспити</h2>
                    <table v-if="futureExamsFiltered.length" class="exams-table">
                        <thead>
                            <tr>
                                <th class="left"><span class="pill">Назва іспиту</span></th>
                                <th class="left"><span class="pill">Час початку</span></th>
                                <th class="left"><span class="pill">Час закінчення</span></th>
                                <th class="right"><span class="pill">Тривалість</span></th>
                                <th class="right"><span class="pill">К-сть спроб</span></th>
                                <th class="right"><span class="pill">Прохідний бал</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="exam in futureExamsFiltered" :key="exam.id">
                                <td 
                                    class="exam-title left"
                                    @click="openStartExamPopup(exam)">
                                    {{ exam.title }}
                                </td>
                                <td class="left">{{ formatDateTime(exam.start_at) }}</td>
                                <td class="left">{{ formatDateTime(exam.end_at) }}</td>
                                <td class="right">{{ exam.duration_minutes }} хв</td>
                                <td class="right">{{ exam.max_attempts }}</td>
                                <td class="right">{{ exam.pass_threshold }}</td>
                            </tr>
                        </tbody>
                    </table>
                    <p v-else class="empty-list-message">Немає запланованих іспитів.</p>
                </div>

                <!-- Секція для виконаних іспитів -->
                <div class="exams-section">
                    <h2>Вже виконано</h2>
                    <table v-if="completedExams.length" class="exams-table">
                        <thead>
                            <tr>
                                <th class="left"><span class="pill">Назва іспиту</span></th>
                                <th class="left"><span class="pill">Час початку</span></th>
                                <th class="left"><span class="pill">Час закінчення</span></th>
                                <th class="right"><span class="pill">Тривалість</span></th>
                                <th class="right"><span class="pill">К-сть спроб</span></th>
                                <th class="right"><span class="pill">Прохідний бал</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="exam in completedExams" :key="exam.id">
                                <td 
                                    class="exam-title left"
                                    :class="{ 'inactive': !hasRemainingAttempts(exam) }"
                                    @click="handleCompletedExamClick(exam)">
                                    {{ exam.title }}
                                </td>
                                <td class="left" :class="{ 'inactive': !hasRemainingAttempts(exam) }">{{ formatDateTime(exam.start_at) }}</td>
                                <td class="left" :class="{ 'inactive': !hasRemainingAttempts(exam) }">{{ formatDateTime(exam.end_at) }}</td>
                                <td class="right" :class="{ 'inactive': !hasRemainingAttempts(exam) }">{{ exam.duration_minutes }} хв</td>
                                <td class="right" :class="{ 'inactive': !hasRemainingAttempts(exam) }">{{ exam.max_attempts }}</td>
                                <td class="right" :class="{ 'inactive': !hasRemainingAttempts(exam) }">{{ exam.pass_threshold }}</td>
                            </tr>
                        </tbody>
                    </table>
                    <p v-else class="empty-list-message">Ще немає виконаних іспитів.</p>
                </div>

                <div class="page-end-deco">
                    <img src="../assets/icons/graduate-hat.svg" alt="Decorative graduate hat">
                    <div class="page-end-text">Наразі це все!</div>
                </div>
            </div>
        </main>
        <div class="start-test-popup" v-if="isPopupVisible">
            <CPopup 
                :visible="isPopupVisible" 
                :header="popupHeader"
                :disclaimer="popupDisclaimer"
                :fstButton="getPopupFirstButton()"
                :sndButton="getPopupSecondButton()"
                @fstAction="handlePopupFirstAction()"
                @sndAction="handlePopupSecondAction()" />
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import Header from '../components/global/Header.vue'
import Breadcrumbs from '../components/global/Breadcrumbs.vue'
import CPopup from '../components/global/CPopup.vue'
import { getExams } from '../api/exams.js'
import { startExamAttempt } from '../api/attempts.js'
import { useRouter } from 'vue-router'

const router = useRouter()

// Створюємо окремі ref для кожного списку - відкритих, майбутніх і виконаних іспитів
const openExams = ref([])
const futureExams = ref([])
const completedExams = ref([])

// Computed property для майбутніх іспитів (для сумісності з існуючим кодом)
const futureExamsFiltered = computed(() => {
    return futureExams.value
})

const loading = ref(true)
const error = ref(null)

// керуємо поп-апом з підтвердженням готовності почати іспит
const isPopupVisible = ref(false)
const selectedExam = ref(null)
const isWarningPopup = ref(false) // Попап з попередженням про час початку
const isErrorPopup = ref(false) // Попап з помилкою
const isChoicePopup = ref(false) // Попап з вибором між переглядом спроби та початком нової
const errorMessage = ref('') // Повідомлення про помилку

const popupHeader = computed(() => {
    if (!selectedExam.value) return ''
    
    if (isErrorPopup.value) {
        return 'Неможливо розпочати іспит'
    }
    
    if (isWarningPopup.value) {
        return "Іспит ще не розпочався"
    }
    
    if (isChoicePopup.value) {
        return `Іспит: ${selectedExam.value.title}`
    }
    
    return `Розпочати іспит: ${selectedExam.value.title}?`
})

const popupDisclaimer = computed(() => {
    if (!selectedExam.value) return ''
    
    if (isErrorPopup.value) {
        return errorMessage.value || 'Сталася невідома помилка.'
    }
    
    if (isWarningPopup.value) {
        const formattedTime = formatDateTime(selectedExam.value.start_at)
        return `Іспит "${selectedExam.value.title}" можна розпочати тільки після ${formattedTime}.`
    }
    
    if (isChoicePopup.value) {
        const attemptsUsed = selectedExam.value.user_attempts_count || 0
        const maxAttempts = selectedExam.value.max_attempts || 0
        const remainingAttempts = maxAttempts - attemptsUsed
        return `Ви вже виконали ${attemptsUsed} з ${maxAttempts} спроб. Залишилося ${remainingAttempts} спроб. Що ви хочете зробити?`
    }
    
    return 'Як тільки екзамен розпочнеться, його не можна буде зупинити.'
})

// Перевіряє, чи можна почати іспит (чи час початку вже настав)
function canStartExam(exam) {
    if (!exam || !exam.start_at) {
        return false
    }
    const startTime = new Date(exam.start_at)
    const now = new Date()
    return now >= startTime
}

function openStartExamPopup(exam) {
    selectedExam.value = exam
    
    // Для відкритих іспитів (статус "open") завжди дозволяємо почати без попередження
    // Для інших іспитів перевіряємо, чи час початку вже настав
    const isOpen = exam.status === 'open'
    const canStart = isOpen || canStartExam(exam)
    
    if (canStart) {
        // Показуємо звичайний попап з підтвердженням
        isWarningPopup.value = false
        isPopupVisible.value = true
    } else {
        // Показуємо попап з попередженням (тільки з кнопкою "Закрити")
        isWarningPopup.value = true
        isPopupVisible.value = true
    }
}

function closePopup() {
    selectedExam.value = null
    isPopupVisible.value = false
    isWarningPopup.value = false
    isErrorPopup.value = false
    isChoicePopup.value = false
    errorMessage.value = ''
}

// Перевіряє, чи є ще дозволені спроби для іспиту
function hasRemainingAttempts(exam) {
    if (!exam) return false
    const attemptsUsed = exam.user_attempts_count || 0
    const maxAttempts = exam.max_attempts || 0
    return attemptsUsed < maxAttempts
}

// Обробляє клік на іспит у секції "виконані"
function handleCompletedExamClick(exam) {
    if (!exam) return
    
    // Якщо немає спроб або досягнуто max_attempts, просто переходимо до результатів
    if (!exam.last_attempt_id || !hasRemainingAttempts(exam)) {
        if (exam.last_attempt_id) {
            goToExamResults(exam.last_attempt_id)
        }
        return
    }
    
    // Якщо є спроби і ще є дозволені спроби, показуємо діалог вибору
    selectedExam.value = exam
    isChoicePopup.value = true
    isWarningPopup.value = false
    isErrorPopup.value = false
    isPopupVisible.value = true
}

// Отримує текст першої кнопки попапу
function getPopupFirstButton() {
    if (isErrorPopup.value || isWarningPopup.value) {
        return 'Закрити'
    }
    if (isChoicePopup.value) {
        return 'Розпочати нову спробу'
    }
    return 'Розпочати'
}

// Отримує текст другої кнопки попапу
function getPopupSecondButton() {
    if (isErrorPopup.value || isWarningPopup.value) {
        return null
    }
    if (isChoicePopup.value) {
        return 'Переглянути спробу'
    }
    return 'Скасувати'
}

// Обробляє натискання першої кнопки попапу
function handlePopupFirstAction() {
    if (isErrorPopup.value || isWarningPopup.value) {
        closePopup()
        return
    }
    if (isChoicePopup.value) {
        // Розпочати нову спробу
        handleStartExam()
        return
    }
    handleStartExam()
}

// Обробляє натискання другої кнопки попапу
function handlePopupSecondAction() {
    if (isChoicePopup.value) {
        // Переглянути спробу
        if (selectedExam.value?.last_attempt_id) {
            goToExamResults(selectedExam.value.last_attempt_id)
        }
        closePopup()
        return
    }
    closePopup()
}

// розпочинаємо спробу іспиту, натиснувши на кнопку в поп-апі
async function handleStartExam() {
    if (!selectedExam.value) return;

    try {
        const attemptData = await startExamAttempt(selectedExam.value.id)
        const attemptId = attemptData.id
        router.push(`/exam/${attemptId}`)
        closePopup()
    } catch (err) {
        console.error("Помилка при спробі розпочати іспит:", err)
        
        // Перевіряємо, чи це помилка про те, що студент не зареєстрований
        const errorDetail = err.response?.data?.detail || err.message || ''
        const isNotRegistered = errorDetail.includes('не зареєстрований') || 
                                errorDetail.includes('зареєстрований як учасник') ||
                                err.response?.status === 409
        
        if (isNotRegistered) {
            // Показуємо попап з повідомленням про необхідність звернутися до наглядача
            errorMessage.value = 'Ви не зареєстровані на цей іспит. Будь ласка, зверніться до наглядача для реєстрації.'
            isErrorPopup.value = true
            isWarningPopup.value = false
            // Не закриваємо попап, щоб користувач міг прочитати повідомлення
        } else {
            // Для інших помилок також показуємо попап
            errorMessage.value = errorDetail || 'Не вдалося розпочати іспит. Спробуйте ще раз.'
            isErrorPopup.value = true
            isWarningPopup.value = false
        }
    }
}

onMounted(async () => {
    try {
        const data = await getExams()
        // Отримуємо окремі списки від бекенду
        openExams.value = data.open || []
        futureExams.value = data.future || []
        completedExams.value = data.completed || []

    } catch (err) {
        error.value = err.message
    } finally {
        loading.value = false
    }
})

// браузер бере часовий пояс з налаштувань браузера користувача
function formatDateTime(dateString) {
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }
    return new Date(dateString).toLocaleString('uk-UA', options)
}

function goToExamResults(attemptId) {
    router.push(`/exams-results/${attemptId}`)
}
</script>

<style scoped>
.start-test-popup {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: var(--color-black-half-opacity);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.inactive {
    opacity: 0.5;
}

.page-end-deco {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.page-end-text {
    font-style: italic;
}

.exam-title {
    cursor: pointer;
}
</style>