<template>
    <div>
        <Header />
        <main class="container" v-if="!loading">
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
                <!-- Секція для майбутніх іспитів -->
                <section class="exams-section">
                    <h2>Майбутні іспити</h2>
                    <table v-if="futureExams.length" class="exams-table">
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
                            <tr v-for="exam in futureExams" :key="exam.id">
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
                </section>

                <!-- Секція для виконаних іспитів -->
                <section class="exams-section">
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
                                <td class="exam-title left inactive">{{ exam.title }}</td>
                                <td class="left inactive">{{ formatDateTime(exam.start_at) }}</td>
                                <td class="left inactive">{{ formatDateTime(exam.end_at) }}</td>
                                <td class="right inactive">{{ exam.duration_minutes }} хв</td>
                                <td class="right inactive">{{ exam.max_attempts }}</td>
                                <td class="right inactive">{{ exam.pass_threshold }}</td>
                            </tr>
                        </tbody>
                    </table>
                    <p v-else class="empty-list-message">Ще немає виконаних іспитів.</p>
                </section>

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
                :fstButton="isWarningPopup ? 'Закрити' : 'Розпочати'"
                :sndButton="isWarningPopup ? null : 'Скасувати'"
                @fstAction="isWarningPopup ? closePopup() : handleStartExam()"
                @sndAction="closePopup" />
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import Header from '../components/global/Header.vue'
import CPopup from '../components/global/CPopup.vue'
import { getExams } from '../api/exams.js'
import { startExamAttempt } from '../api/attempts.js'
import { useRouter } from 'vue-router'

const router = useRouter()

// Створюємо два окремих ref для кожного списку - майбутніх і виконаних іспитів
const futureExams = ref([])
const completedExams = ref([])

const loading = ref(true)
const error = ref(null)

// керуємо поп-апом з підтвердженням готовності почати іспит
const isPopupVisible = ref(false)
const selectedExam = ref(null)
const isWarningPopup = ref(false) // Попап з попередженням про час початку

const popupHeader = computed(() => {
    if (!selectedExam.value) return ''
    
    if (isWarningPopup.value) {
        return `Іспит ще не розпочався`
    }
    
    return `Розпочати іспит: ${selectedExam.value.title}?`
})

const popupDisclaimer = computed(() => {
    if (!selectedExam.value) return ''
    
    if (isWarningPopup.value) {
        const formattedTime = formatDateTime(selectedExam.value.start_at)
        return `Іспит "${selectedExam.value.title}" можна розпочати тільки після ${formattedTime}.`
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
    
    // Перевіряємо, чи час початку вже настав
    const canStart = canStartExam(exam)
    if (canStart === false) {
        // Показуємо попап з попередженням (тільки з кнопкою "Закрити")
        isWarningPopup.value = true
        isPopupVisible.value = true
    } else {
        // Показуємо звичайний попап з підтвердженням
        isWarningPopup.value = false
        isPopupVisible.value = true
    }
}

function closePopup() {
    selectedExam.value = null
    isPopupVisible.value = false
    isWarningPopup.value = false
}

// розпочинаємо спробу іспиту, натиснувши на кнопку в поп-апі
async function handleStartExam() {
    if (!selectedExam.value) return;

    try {
        const attemptData = await startExamAttempt(selectedExam.value.id)
        const attemptId = attemptData.id
        router.push(`/exam/${attemptId}`)
    } catch (err) {
        console.error("Помилка при спробі розпочати іспит:", err)
        const errorMsg = err.response?.data?.detail || err.message || 'Не вдалося розпочати іспит. Спробуйте ще раз.'
        alert(errorMsg)
    } finally {
        closePopup()
    }
}

onMounted(async () => {
    try {
        const data = await getExams()
        futureExams.value = data.future
        completedExams.value = data.completed

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