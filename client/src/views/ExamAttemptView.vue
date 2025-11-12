    <template>
        <Header />
        <main class="container">
            <Breadcrumbs />
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
                    <div class="exam-question-content">
                        <div class="progress">
                            <h3>Питання {{ currentQuestionIndex + 1 }} з {{ totalQuestions }}</h3>
                        </div>
                        <div class="question">
                            <QuestionDisplay :question="currentQuestion"
                                :savedAnswer="allSavedAnswers[currentQuestion.id] || null"
                                @answer-changed="handleAnswerChange" />
                        </div>
                        <div class="navigation-buttons">
                            <CButton @click="saveAndNext" :disabled="isSaving">
                                {{ isLastQuestion ? 'Завершити іспит' : 'Зберегти і продовжити' }}
                            </CButton>
                        </div>
                        <div class="exam-timer">
                            <CTimer :durationMinutes="durationMinutes" :startedAt="startedAt" :dueAt="dueAt" @time-up="finalizeAndLeave" />
                        </div>
                    </div>
                </div>
            </div>

            <div class="leave-test-popup" v-if="isPopupVisible">
                <CPopup :visible="isPopupVisible" :header="'Завершити тестування?'"
                    disclaimer="Ви не зможете повернутися до тестування після завершення." fstButton="Завершити"
                    sndButton="Скасувати" @fstAction="finalizeAndLeave" @sndAction="cancelLeave" />
            </div>
        </main>
    </template>

    <script setup>
    import { onMounted, onUnmounted, ref, computed } from 'vue'
    import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
    import Header from '../components/global/Header.vue'
    import Breadcrumbs from '../components/global/Breadcrumbs.vue'
    import CButton from '../components/global/CButton.vue'
    import QuestionDisplay from '../components/ExamAttemptView/QuestionDisplay.vue'
    import CPopup from '../components/global/CPopup.vue'
    import CTimer from '../components/ExamAttemptView/CTimer.vue'
    import { getExamAttemptDetails, saveAnswer, submitExamAttempt } from '../api/attempts.js'

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
    const durationMinutes = ref(0)

    const currentQuestion = computed(() => questionsList.value[currentQuestionIndex.value])
    const totalQuestions = computed(() => questionsList.value.length)
    const isLastQuestion = computed(() => currentQuestionIndex.value === totalQuestions.value - 1)

    const localStorageKey = `exam_progress_${attemptId}`
    const startTimeKey = `exam_start_time_${attemptId}`
    const startedAt = ref(null)

    // керуємо поп-апом з підтвердженням готовності завершити іспит
    // щоб уникнути випадкового натискання кнопки "назад" у браузері
    // або переходу на іншу сторінку сайту
    const isPopupVisible = ref(false)
    let resolveNavigation = null

    function cancelLeave() {
        isPopupVisible.value = false
        if (resolveNavigation) {
            resolveNavigation(false)
        }
    }

    onBeforeRouteLeave(() => {
        if (status.value !== 'in_progress') {
            return true
        }
        if (isPopupVisible.value) {
            return false
        }
        isPopupVisible.value = true
        // Повертаємо проміс, який буде вирішено в confirmLeave або cancelLeave
        return new Promise((resolve) => {
            resolveNavigation = resolve
        })
    })


    async function refreshAttemptDetails() {
        try {
            const data = await getExamAttemptDetails(attemptId)
            // Оновлюємо тільки dueAt, щоб таймер реагував на зміни
            if (data.due_at) {
                dueAt.value = data.due_at
            }
            // Оновлюємо статус, якщо він змінився
            if (data.status) {
                status.value = data.status
            }
        } catch (err) {
            console.error('Помилка оновлення даних спроби:', err)
        }
    }

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
            durationMinutes.value = data.duration_minutes || 60 // За замовчуванням 60 хвилин
            document.title = `${data.exam_title} | Systematics`
            startedAt.value = data.started_at

            const savedIndex = localStorage.getItem(localStorageKey)
            if (savedIndex) {
                // Перетворюємо рядок з localStorage назад в число
                const parsedIndex = Number.parseInt(savedIndex, 10)
                // Перевіряємо, чи індекс валідний (на випадок зміни кількості питань)
                if (parsedIndex < questionsList.value.length) {
                    currentQuestionIndex.value = parsedIndex
                }
            }

            // Оновлюємо дані спроби кожні 30 секунд, щоб таймер реагував на зміни часу
            const refreshInterval = setInterval(() => {
                if (status.value === 'in_progress') {
                    refreshAttemptDetails()
                } else {
                    clearInterval(refreshInterval)
                }
            }, 30000) // 30 секунд

            // Очищаємо інтервал при розмонтуванні компонента
            onUnmounted(() => {
                clearInterval(refreshInterval)
            })

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
        const questionType = currentQuestion.value.question_type

        // Перевірка, чи є відповідь
        if (answerToSave === null || answerToSave === undefined || (Array.isArray(answerToSave) && answerToSave.length === 0)) {
            alert("Будь ласка, надайте відповідь перед продовженням.")
            return
        }

        isSaving.value = true
        try {
            // Відправляємо відповідь на бекенд
            await saveAnswer(attemptId, questionId, answerToSave, questionType)

            if (isLastQuestion.value) {
                await finalizeAndLeave()
            } else {
                currentQuestionIndex.value++
                localStorage.setItem(localStorageKey, currentQuestionIndex.value)
                window.scrollTo(0, 0)
            }

        } catch (err) {
            console.error(err)
            alert("Помилка збереження відповіді. Будь ласка, перевірте з'єднання та спробуйте ще раз.")
        } finally {
            isSaving.value = false
        }
    }

    async function finalizeAndLeave() {
        isSaving.value = true
        isPopupVisible.value = false

        try {
            // Перевіряємо, чи є незбережена відповідь на поточному питанні
            const currentAnswer = allSavedAnswers.value[currentQuestion.value.id]
            if (currentAnswer !== null && currentAnswer !== undefined) {
                // Якщо відповідь є, зберігаємо її перед виходом
                const questionType = currentQuestion.value.question_type
                await saveAnswer(attemptId, currentQuestion.value.id, currentAnswer, questionType)
            }

            const updatedAttempt = await submitExamAttempt(attemptId)
            status.value = updatedAttempt.status
            localStorage.removeItem(localStorageKey)
            localStorage.removeItem(startTimeKey)

            router.push(`/exams-results/${attemptId}`)

            if (resolveNavigation) {
                resolveNavigation(true)
                resolveNavigation = null
            }
        } catch (err) {
            console.error("Помилка при завершенні іспиту:", err)
            alert("Не вдалося завершити іспит. Будь ласка, спробуйте ще раз.")

            if (resolveNavigation) {
                resolveNavigation(false)
                resolveNavigation = null
            }
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

    .exam-question-content {
        position: relative;
    }

    .exam-timer {
        position: absolute;
        top: 0;
        right: 0;
    }
    </style>