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
                <div class="question">
                    <QuestionDisplay 
                        :question="currentQuestion" 
                        :savedAnswer="allSavedAnswers[currentQuestion.id] || null"
                        @answer-changed="handleAnswerChange"
                    />
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

        <div class="leave-test-popup" v-if="isPopupVisible">
            <CPopup :visible="isPopupVisible" :header="'Завершити тестування?'"
                disclaimer="Ви не зможете повернутися до тестування після завершення." fstButton="Завершити"
                sndButton="Скасувати" @fstAction="confirmLeave" @sndAction="cancelLeave" />
        </div>
    </main>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import QuestionDisplay from '../components/ExamAttemptView/QuestionDisplay.vue'
import CPopup from '../components/global/CPopup.vue'
import { getExamAttemptDetails, saveAnswer } from '../api/attempts.js'

const route = useRoute()
const router = useRouter()

// Отримуємо attemptId з URL
const attemptId = route.params.attemptId
const examTitle = ref('')
const questionsList = ref([])
const allSavedAnswers = ref({})
const dueAt = ref(null)
const status = ref(null)
const currentQuestionIndex = ref(0)
const loading = ref(true)
const error = ref(null)
const isSaving = ref(false)

const currentQuestion = computed(() => questionsList.value[currentQuestionIndex.value])
const totalQuestions = computed(() => questionsList.value.length)
const isLastQuestion = computed(() => currentQuestionIndex.value === totalQuestions.value - 1)

// керуємо поп-апом з підтвердженням готовності завершити іспит
// щоб уникнути випадкового натискання кнопки "назад" у браузері
// або переходу на іншу сторінку сайту
const isPopupVisible = ref(false)
let resolveNavigation = null

function confirmLeave() {
    isPopupVisible.value = false
    if (resolveNavigation) {
        resolveNavigation(true)
    }
}

function cancelLeave() {
    isPopupVisible.value = false
    if (resolveNavigation) {
        resolveNavigation(false)
    }
}

onBeforeRouteLeave(() => {
    if (isPopupVisible.value) {
        return false
    }
    isPopupVisible.value = true
    // Повертаємо проміс, який буде вирішено в confirmLeave або cancelLeave
    return new Promise((resolve) => {
        resolveNavigation = resolve
    })
})


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

function handleAnswerChange(newAnswer) {
    if (currentQuestion.value) {
        allSavedAnswers.value[currentQuestion.value.id] = newAnswer
    }
}

async function saveAndNext() {
    const questionId = currentQuestion.value.id
    const answerToSave = allSavedAnswers.value[questionId]

    // Перевірка, чи є відповідь
    if (answerToSave === null || answerToSave === undefined || (Array.isArray(answerToSave) && answerToSave.length === 0)) {
        alert("Будь ласка, надайте відповідь перед продовженням.")
        return
    }

    isSaving.value = true
    try {
        // Відправляємо відповідь на бекенд
        await saveAnswer(attemptId, questionId, answerToSave)

        if (isLastQuestion.value) {
            alert("Іспит успішно завершено!")
            router.push('/exams')
        } else {
            currentQuestionIndex.value++
            window.scrollTo(0, 0)
        }

    } catch (err) {
        console.error(err)
        alert("Помилка збереження відповіді. Будь ласка, перевірте з'єднання та спробуйте ще раз.")
    } finally {
        isSaving.value = false
    }
}

</script>

<style scoped>
.leave-test-popup {
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
</style>