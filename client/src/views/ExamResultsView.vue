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
                    <span class="score-value">{{ results.score }} / 100</span>
                </div>

                <ul class="statistics-list">
                    <li>Витрачено часу: <strong>{{ formattedTimeSpent }}</strong></li>
                    <li>Надано відповідей: <strong>{{ results.answers_given }} / {{ results.total_questions }}</strong>
                    </li>
                    <li>Надано правильних відповідей: <strong>{{ results.correct_answers }} / {{ results.total_questions
                    }}</strong></li>
                    <li>Надано неправильних відповідей: <strong>{{ results.incorrect_answers }} / {{
                        results.total_questions }}</strong></li>
                    <li v-if="results.pending_count > 0" class="pending">
                        Питань, що очікують перевірки: <strong>{{ results.pending_count }}</strong>

                         <Tooltip>
                            <template #trigger>
                                <span class="info-icon">!</span>
                            </template>
                            <template #content>
                                <strong>Увага!</strong> Деякі типи завдань (з розгорнутою відповіддю) потребують
                                перевірки викладачем. Оцінка за такі завдання буде відображена лише після їхньої
                                перевірки. Загальна оцінка не враховує оцінку таких завдань до моменту їхньої перевірки.
                            </template>
                        </Tooltip>
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
import Tooltip from '../components/global/CTooltip.vue'
import { formatDuration } from '../utils/formatters.js'

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
        console.log(data)
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
    if (!results.value || typeof results.value.time_spent_seconds !== 'number') {
        return '00 хв 00 сек' 
    }
    // Викликаємо нашу нову, протестовану функцію
    return formatDuration(results.value.time_spent_seconds)
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

.pending .tooltip-container {
    display: inline-block;
    vertical-align: middle;
    margin-left: 8px;
    margin-bottom: 2px; 
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
</style>