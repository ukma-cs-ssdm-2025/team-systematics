<template>
    <div>
        <Header />
        <main class="container">
            <Breadcrumbs />
            <div v-if="loading" class="status-message">Завантаження...</div>
            <div v-else-if="error" class="status-message error">{{ error }}</div>

            <div v-else-if="reviewData" class="review-container">
                <h2 class="exam-title">Іспит | {{ reviewData.exam_title }}</h2>
                <h3 class="page-subtitle">Перегляд відповідей</h3>

                <!-- Повідомлення про те, що правильні відповіді приховані -->
                <div v-if="!reviewData.show_correct_answers && !auth.isTeacher.value" class="info-message">
                    <p><strong>Увага!</strong> Правильні відповіді будуть доступні після використання всіх спроб для цього іспиту.</p>
                </div>

                <!-- Фінальна оцінка з можливістю редагування (тільки для викладачів) -->
                <div v-if="auth.isTeacher.value" class="final-score-section">
                    <div class="score-label">Фінальна оцінка:</div>
                    <div 
                        v-if="!isEditingFinalScore" 
                        class="score-display"
                        @click="startEditingFinalScore"
                        :title="'Клік для редагування'"
                    >
                        {{ displayFinalScore }} / 100
                    </div>
                    <div v-else class="score-edit">
                        <input
                            ref="scoreInput"
                            type="text"
                            v-model="editingFinalScore"
                            @blur="saveFinalScore"
                            @keydown.enter="saveFinalScore"
                            @keydown.esc="cancelEditingFinalScore"
                            @input="validateScoreInput"
                            @keypress="preventInvalidInput"
                            class="score-input"
                            maxlength="6"
                        />
                        <span class="score-suffix">/ 100</span>
                    </div>
                    <div v-if="scoreError" class="score-error">{{ scoreError }}</div>
                </div>

                <!-- Ітеруємо по кожному питанню і передаємо його в QuestionDisplay -->
                <div v-for="question in reviewData.questions" :key="question.id" class="question-wrapper">
                    <QuestionDisplay 
                        :question="question" 
                        :position="question.position" 
                        :is-review-mode="true"
                        :is-teacher="auth.isTeacher.value"
                        :attempt-id="attemptId"
                        :show-correct-answers="reviewData.show_correct_answers"
                        @score-updated="handleScoreUpdate"
                    />
                </div>

                <div class="footer-actions">
                    <CButton @click="finishReview">Завершити перегляд</CButton> 
                </div>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import Breadcrumbs from '../components/global/Breadcrumbs.vue'
import CButton from '../components/global/CButton.vue'
import QuestionDisplay from '../components/ExamAttemptView/QuestionDisplay.vue'
import { getExamAttemptReview, getExamAttemptDetails, getExamAttemptResults, updateFinalScore } from '../api/attempts.js'
import { useAuth } from '../store/loginInfo.js'

const route = useRoute()
const router = useRouter()
const attemptId = route.params.attemptId
const auth = useAuth()

const loading = ref(true)
const error = ref(null)
const reviewData = ref(null)
const examId = ref(null)  // Зберігаємо exam_id окремо
const attemptResults = ref(null)  // Зберігаємо результати спроби для отримання фінальної оцінки
const isEditingFinalScore = ref(false)
const editingFinalScore = ref('')
const scoreInput = ref(null)
const scoreError = ref(null)

const displayFinalScore = computed(() => {
    if (!attemptResults.value || typeof attemptResults.value.score !== 'number') {
        return 0
    }
    return Math.round(attemptResults.value.score * 10) / 10  // Округлюємо до 1 знака після коми
})

onMounted(async () => {
    try {
        // Спочатку отримуємо exam_id з attempt details (якщо exam_id не повертається в review)
        try {
            const attemptDetails = await getExamAttemptDetails(attemptId)
            examId.value = attemptDetails.exam_id
        } catch (err) {
            // Логування помилки і перенаправлення на значення за замовчуванням
            console.warn('Failed to get exam_id from attempt details:', err)
        }
        
        // Отримуємо дані для перегляду та результати спроби
        const [data, results] = await Promise.all([
            getExamAttemptReview(attemptId),
            auth.isTeacher.value ? getExamAttemptResults(attemptId).catch(() => null) : Promise.resolve(null)
        ])
        
        reviewData.value = data
        attemptResults.value = results
        
        // Якщо exam_id є в reviewData, використовуємо його
        if (data.exam_id) {
            examId.value = data.exam_id
        }
    } catch (err) {
        // Обробка основної помилки
        console.error('Error loading exam attempt review:', err)
        error.value = "Не вдалося завантажити дані для перегляду."
    } finally {
        loading.value = false
    }
})

function finishReview() {
    // Перенаправляємо вчителів на журнал іспиту, а студентів - на список іспитів
    if (auth.isTeacher.value) {
        // Використовуємо exam_id з reviewData або з окремо збереженого значення
        const finalExamId = reviewData.value?.exam_id || examId.value
        if (finalExamId) {
            router.push(`/exams/${finalExamId}/journal`)
        } else {
            router.push('/courses/my')
        }
    } else {
        router.push('/exams')
    }
}

async function handleScoreUpdate(questionId, newScore) {
    try {
        // Оновлюємо локальні дані одразу для швидкого відображення
        const question = reviewData.value.questions.find(q => q.id === questionId)
        if (question) {
            // Важливо: 0 - це валідне значення, тому явно встановлюємо його
            // Переконуємося, що newScore є числом (включаючи 0)
            question.earned_points = typeof newScore === 'number' ? newScore : null
        }
        
        // Не перезавантажуємо дані з сервера одразу, оскільки оцінка вже збережена
        // Дані будуть оновлені при наступному завантаженні сторінки
    } catch (err) {
        error.value = "Не вдалося оновити оцінку."
        // Відновлюємо попереднє значення при помилці
        const question = reviewData.value.questions.find(q => q.id === questionId)
        if (question) {
            // Можна зберегти попереднє значення або залишити як є
        }
        throw err
    }
}

function startEditingFinalScore() {
    if (!auth.isTeacher.value) return
    
    isEditingFinalScore.value = true
    editingFinalScore.value = displayFinalScore.value.toString()
    scoreError.value = null
    
    nextTick(() => {
        if (scoreInput.value) {
            scoreInput.value.focus()
            scoreInput.value.select()
        }
    })
}

function validateScoreInput(event) {
    let value = event.target.value
    
    // Видаляємо всі символи, крім цифр та крапки
    value = value.replaceAll(/[^\d.]/g, '')
    
    // Перевіряємо, що крапка тільки одна
    const parts = value.split('.')
    if (parts.length > 2) {
        // Якщо більше однієї крапки, залишаємо тільки першу
        value = parts[0] + '.' + parts.slice(1).join('')
    }
    
    // Перевіряємо діапазон та обмежуємо значення
    const numValue = Number.parseFloat(value)
    if (value && !Number.isNaN(numValue)) {
        if (numValue < 0) {
            // Якщо менше 0, встановлюємо 0
            value = '0'
        } else if (numValue > 100) {
            // Якщо більше 100, обмежуємо до 100
            value = '100'
        }
    }
    
    // Додаткова перевірка: якщо вже є "100" без крапки, не дозволяємо додавати цифри
    if (value.startsWith('100') && value.length > 3 && !value.includes('.')) {
        // Якщо намагаються додати цифри після "100", обрізаємо
        value = '100'
    }
    
    // Очищаємо помилку валідації
    scoreError.value = null
    
    // Оновлюємо значення в інпуті (видаляємо некоректні символи)
    editingFinalScore.value = value
    
    // Якщо значення змінилося, оновлюємо позицію курсора
    if (event.target.value !== value) {
        event.target.value = value
        // Встановлюємо курсор на кінці, якщо текст був змінений
        nextTick(() => {
            event.target.setSelectionRange(value.length, value.length)
        })
    }
}

async function saveFinalScore() {
    if (!isEditingFinalScore.value) return
    
    const numValue = Number.parseFloat(editingFinalScore.value)
    
    // Валідація
    if (editingFinalScore.value === '' || Number.isNaN(numValue)) {
        scoreError.value = 'Введіть коректне число'
        return
    }
    
    if (numValue < 0 || numValue > 100) {
        scoreError.value = 'Оцінка повинна бути від 0 до 100'
        return
    }
    
    try {
        await updateFinalScore(attemptId, numValue)
        
        // Оновлюємо локальні дані
        if (attemptResults.value) {
            attemptResults.value.score = numValue
        }
        
        isEditingFinalScore.value = false
        scoreError.value = null
    } catch (err) {
        scoreError.value = err.message || 'Не вдалося оновити оцінку'
        console.error('Failed to update final score:', err)
    }
}

function preventInvalidInput(event) {
    const char = event.key
    const currentValue = editingFinalScore.value
    
    // Дозволяємо клавіші управління завжди
    if (['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter', 'Escape'].includes(char)) {
        return true
    }
    
    // Блокуємо всі інші символи, крім цифр та крапки
    if (!/[\d.]/.test(char)) {
        event.preventDefault()
        return false
    }
    
    // Перевіряємо, чи вже є крапка
    if (char === '.' && currentValue.includes('.')) {
        event.preventDefault()
        return false
    }
    
    // Якщо вже введено 100, блокуємо подальше введення цифр
    if (/\d/.test(char)) {
        const numValue = Number.parseFloat(currentValue + char)
        if (!Number.isNaN(numValue) && numValue > 100) {
            event.preventDefault()
            return false
        }
        
        // Якщо вже є "100" без крапки, блокуємо додавання цифр
        if (currentValue === '100' && !currentValue.includes('.')) {
            event.preventDefault()
            return false
        }
    }
    
    return true
}

function cancelEditingFinalScore() {
    isEditingFinalScore.value = false
    editingFinalScore.value = ''
    scoreError.value = null
}
</script>

<style scoped>
.question-wrapper {
    width: 60%;
}

.info-message {
    background-color: var(--color-lavender);
    border: 2px solid var(--color-purple);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 24px;
    width: 60%;
}

.info-message p {
    margin: 0;
    color: var(--color-dark-gray);
}

.final-score-section {
    margin-bottom: 24px;
    padding: 16px;
    background-color: var(--color-lavender);
    border: 2px solid var(--color-purple);
    border-radius: 8px;
    width: 60%;
}

.score-label {
    font-weight: bold;
    margin-bottom: 8px;
    color: var(--color-dark-gray);
}

.score-display {
    font-size: 2rem;
    font-weight: bold;
    color: var(--color-purple);
    cursor: pointer;
    user-select: none;
    padding: 8px;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.score-display:hover {
    background-color: rgba(128, 0, 128, 0.1);
}

.score-edit {
    display: flex;
    align-items: center;
    gap: 8px;
}

.score-input {
    font-size: 2rem;
    font-weight: bold;
    padding: 8px;
    border: 2px solid var(--color-purple);
    border-radius: 4px;
    width: 120px;
    text-align: center;
    color: var(--color-purple);
}

.score-input:focus {
    outline: none;
    border-color: var(--color-dark-purple);
    box-shadow: 0 0 0 3px rgba(128, 0, 128, 0.1);
}

.score-suffix {
    font-size: 2rem;
    font-weight: bold;
    color: var(--color-dark-gray);
}

.score-error {
    color: var(--color-red, #d32f2f);
    font-size: 0.9rem;
    margin-top: 8px;
}
</style>