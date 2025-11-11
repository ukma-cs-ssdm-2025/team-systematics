<template>
    <div>
        <Header />
        <main class="container">
            <div v-if="loading" class="status-message">Завантаження...</div>
            <div v-else-if="error" class="status-message error">{{ error }}</div>

            <div v-else-if="reviewData" class="review-container">
                <h2 class="exam-title">Іспит | {{ reviewData.exam_title }}</h2>
                <h3 class="page-subtitle">Перегляд відповідей</h3>

                <!-- Ітеруємо по кожному питанню і передаємо його в QuestionDisplay -->
                <div v-for="question in reviewData.questions" :key="question.id" class="question-wrapper">
                    <QuestionDisplay 
                        :question="question" 
                        :position="question.position" 
                        :is-review-mode="true"
                        :is-teacher="auth.isTeacher.value"
                        :attempt-id="attemptId"
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
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import QuestionDisplay from '../components/ExamAttemptView/QuestionDisplay.vue'
import { getExamAttemptReview } from '../api/attempts.js'
import { getExamAttemptDetails } from '../api/attempts.js'
import { useAuth } from '../store/loginInfo.js'

const route = useRoute()
const router = useRouter()
const attemptId = route.params.attemptId
const auth = useAuth()

const loading = ref(true)
const error = ref(null)
const reviewData = ref(null)
const examId = ref(null)  // Зберігаємо exam_id окремо

onMounted(async () => {
    try {
        // Спочатку отримуємо exam_id з attempt details (якщо exam_id не повертається в review)
        try {
            const attemptDetails = await getExamAttemptDetails(attemptId)
            examId.value = attemptDetails.exam_id
        } catch (err) {
            // Ігноруємо помилку, якщо не вдалося отримати exam_id з attempt details
        }
        
        const data = await getExamAttemptReview(attemptId)
        reviewData.value = data
        
        // Якщо exam_id є в reviewData, використовуємо його
        if (data.exam_id) {
            examId.value = data.exam_id
        }
    } catch (err) {
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
            question.earned_points = newScore
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
</script>

<style scoped>
.question-wrapper {
    width: 60%;
}
</style>