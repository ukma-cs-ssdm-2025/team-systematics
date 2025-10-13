<template>
    <Header />
    <main class="container">
        <!-- 1. Стан завантаження -->
        <div v-if="loading" class="status-message">
            Завантаження іспиту...
        </div>

        <!-- 2. Стан помилки -->
        <div v-else-if="error" class="status-message error">
            {{ error }}
        </div>

        <!-- 3. Основний інтерфейс іспиту -->
        <div v-else-if="currentQuestion" class="exam-content">
            <div class="exam-header">
                <h2>{{ examTitle }}</h2>
                <div class="progress">
                    <h3>Питання {{ currentQuestionIndex + 1 }} з {{ totalQuestions }}</h3>
                </div>
                <div class="navigation-buttons">
                    <CButton 
                        @click="saveAndNext"
                        :disabled="isSaving" 
                    >
                        {{ isLastQuestion ? 'Завершити іспит' : 'Зберегти і продовжити' }}
                    </CButton>
                </div>
            </div>
        </div>
    </main>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import { getExamAttemptDetails } from '../api/attempts.js'

const route = useRoute()

// Отримуємо attemptId з URL
const attemptId = route.params.attemptId
const examTitle = ref('')
const questionsList = ref([])
const allSavedAnswers = ref({})
const dueAt = ref(null)
const status = ref(null)
const currentQuestionIndex = ref(0)
const currentTempAnswer = ref(null)
const loading = ref(true)
const error = ref(null)
const isSaving = ref(false)

const currentQuestion = computed(() => questionsList.value[currentQuestionIndex.value])
const totalQuestions = computed(() => questionsList.value.length)
const isLastQuestion = computed(() => currentQuestionIndex.value === totalQuestions.value - 1)

onMounted(async () => {
    if (!attemptId) {
        error.value = "Помилка: Відсутній ID спроби."
        loading.value = false
        return
    }

    try {
        const data = await getExamAttemptDetails(attemptId)
        examTitle.value = data.exam_title
        questionsList.value = data.questions
        allSavedAnswers.value = data.saved_answers || {}
        dueAt.value = data.due_at
        status.value = data.status

        document.title = `${data.exam_title} | Systematics`

    } catch (err) {
        console.error(err)
        error.value = "Не вдалося завантажити дані іспиту. Спробуйте пізніше."
    } finally {
        loading.value = false
    }
})

// async function saveAndNext() {}
</script>