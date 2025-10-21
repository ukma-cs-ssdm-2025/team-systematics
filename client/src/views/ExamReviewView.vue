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
                    <QuestionDisplay :question="question" :position="question.position" :is-review-mode="true"/>
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

const route = useRoute()
const router = useRouter()
const attemptId = route.params.attemptId

const loading = ref(true)
const error = ref(null)
const reviewData = ref(null)

onMounted(async () => {
    try {
        const data = await getExamAttemptReview(attemptId)
        reviewData.value = data
    } catch (err) {
        error.value = "Не вдалося завантажити дані для перегляду."
    } finally {
        loading.value = false
    }
})

function finishReview() {
    router.push('/exams')
}
</script>

<style scoped>
.question-wrapper {
    width: 60%;
}
</style>