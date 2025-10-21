<template>
    <div>
        <Header />
        <main class="container">
            <!-- 1. Стан завантаження -->
            <div v-if="loading" class="status-message">
                Завантаження результатів...
            </div>

            <!-- 2. Стан помилки -->
            <div v-else-if="error" class="status-message error">
                {{ error }}
            </div>

            <!-- 3. Основний контент -->
            <div v-else-if="results" class="results-container">
                <h2 class="exam-title">Іспит | {{ results.exam_title }}</h2>

                <h3 class="status-text">Тестування завершено</h3>

                <div class="score-block">
                    <span class="score-label">Оцінка:</span>
                    <span class="score-value">{{ results.score_percent }} / 100</span>
                </div>

                <ul class="statistics-list">
                    <li>Витрачено часу: <strong>{{ formattedTimeSpent }}</strong></li>
                    <li>Надано відповідей: <strong>{{ results.answers_given }} / {{ results.total_questions }}</strong>
                    </li>
                    <li>Надано правильних відповідей: <strong>{{ results.correct_answers }} / {{ results.total_questions
                    }}</strong></li>
                    <li>Надано неправильних відповідей: <strong>{{ results.incorrect_answers }} / {{
                        results.total_questions }}</strong></li>
                    <li v-if="results.pending_review_count > 0" class="pending">
                        Питань, що очікують перевірки: <strong>{{ results.pending_review_count }}</strong>
                        <div class="tooltip-container">

                            <span class="info-icon">!</span>

                            <div class="tooltip-text">
                                <strong>Увага!</strong> Деякі типи завдань (з розгорнутою відповіддю) потребують
                                перевірки викладачем. Оцінка за такі завдання буде відображена лише після їхньої
                                перевірки. Загальна оцінка не враховує оцінку таких завдань до моменту їхньої перевірки.
                            </div>
                        </div>
                    </li>
                </ul>

                <CButton class="review-button" @click="viewAnswers">
                    Переглянути відповіді
                </CButton>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import { getExamAttemptResults } from '../api/attempts.js'

const route = useRoute()
const router = useRouter()
const attemptId = route.params.attemptId

const loading = ref(true)
const error = ref(null)
const results = ref(null)

onMounted(async () => {
    if (!attemptId) {
        error.value = "Не знайдено ID спроби."
        loading.value = false
        return
    }
    try {
        const data = await getExamAttemptResults(attemptId)
        results.value = data
        document.title = `Результати ${data.exam_title} | Systematics`
    } catch (err) {
        error.value = "Не вдалося завантажити результати."
        console.error(err)
    } finally {
        loading.value = false
    }
})

// Обчислювана властивість для форматування витраченого часу
const formattedTimeSpent = computed(() => {
    if (!results.value || !results.value.time_spent_seconds) return '00 хв 00 сек'

    const totalSeconds = results.value.time_spent_seconds
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60

    return `${String(minutes).padStart(2, '0')} хв ${String(seconds).padStart(2, '0')} сек`
})

function viewAnswers() {
    router.push(`/exam/${attemptId}/review`)
}
</script>

<style scoped>
.score-block {
    display: flex;
    flex-direction: column;
}

.score-value {
    font-weight: bold;
    font-size: 2.5rem;
}

.statistics-list {
    margin: 20px 0;
}

.tooltip-container {
    position: relative;
    display: inline-block;
    vertical-align: middle;
    margin-left: 8px;
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
    margin-bottom: 2px;
}

.tooltip-text {
    visibility: hidden;
    opacity: 0;
    width: 500px;
    background-color: #f0f0f0;
    text-align: left;
    padding: 15px;
    border-radius: 10px;
    border: 2px solid var(--color-orange);
    position: absolute;
    z-index: 1;
    bottom: 150%;
    left: 50%;
    transform: translateX(-50%);
    transition: opacity 0.3s, visibility 0.3s;
}

.tooltip-text::after {
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border-width: 8px;
    border-style: solid;
    border-color: var(--color-orange) transparent transparent transparent;
}

.tooltip-container:hover .tooltip-text {
    visibility: visible;
    opacity: 1;
}
</style>