<template>
    <div>
        <Header />
        <main class="container">
            <div class="content-div">
                <div class="page-header">
                    <h2>Створення нового іспиту</h2>
                </div>

                <form @submit.prevent="handleSaveExam" class="form-wrapper">
                    <!-- Секція 1: Налаштування іспиту -->
                    <div class="exam-settings-card">
                        <h3>Основні налаштування</h3>

                        <div class="form-group">
                            <label for="exam-title">Назва іспиту</label>
                            <CInput id="exam-title" v-model.trim="exam.title" @blur="capitalize(exam, 'title')" required
                                :disabled="loading" placeholder="Наприклад, 'Модульний контроль №1'" />
                        </div>

                        <div class="form-grid">
                            <div class="form-group">
                                <label for="exam-start">Дата та час початку</label>
                                <CInput id="exam-start" type="datetime-local" v-model="exam.start_at" required
                                    :disabled="loading" />
                            </div>
                            <div class="form-group">
                                <label for="exam-end">Дата та час завершення</label>
                                <CInput id="exam-end" type="datetime-local" v-model="exam.end_at" required
                                    :disabled="loading" />
                            </div>
                            <div class="form-group">
                                <label for="exam-duration">Тривалість (у хвилинах)</label>
                                <CInput id="exam-duration" type="number" v-model.number="exam.duration_minutes" min="1"
                                    required :disabled="loading" />
                            </div>
                            <div class="form-group">
                                <label for="exam-attempts">Кількість спроб</label>
                                <CInput id="exam-attempts" type="number" v-model.number="exam.max_attempts" min="1"
                                    required :disabled="loading" />
                            </div>
                            <div class="form-group">
                                <label for="exam-threshold">Прохідний бал</label>
                                <CInput id="exam-threshold" type="number" v-model.number="exam.pass_threshold" min="0"
                                    max="100" required :disabled="loading" />
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="exam-instructions">Інструкції (опціонально)</label>
                            <CTextarea id="exam-instructions" v-model.trim="exam.instructions"
                                @blur="capitalize(exam, 'instructions')"
                                placeholder="Опишіть правила або надайте рекомендації для студентів..."
                                :disabled="loading" />
                        </div>
                    </div>

                    <!-- Секція 2: Питання -->
                    <div class="questions-section">
                        <h3>Питання іспиту</h3>

                        <QuestionEditor v-for="(question, index) in exam.questions" :key="question.temp_id"
                            v-model="exam.questions[index]" :index="index" @delete="removeQuestion(index)" />

                        <QuestionTypeSelector @add-question="addQuestion" />
                    </div>

                    <!-- Секція 3: Дії та повідомлення -->
                    <div class="actions">
                        <CButton type="submit" :disabled="loading" class="submit-button">
                            {{ loading ? 'Збереження...' : 'Зберегти іспит' }}
                        </CButton>
                        <div v-if="success" class="status-message success">Іспит успішно створено!</div>
                        <div v-if="error" class="status-message error">{{ error }}</div>
                    </div>
                </form>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import CInput from '../components/global/CInput.vue'
import CTextarea from '../components/global/CTextarea.vue'
import QuestionEditor from '../components/CreateExamView/QuestionEditor.vue'
import QuestionTypeSelector from '../components/CreateExamView/QuestionTypeSelector.vue'
import { createExam } from '../api/exams.js'

const router = useRouter()
const courseId = useRoute().params.courseId

const loading = ref(false)
const error = ref(null)
const success = ref(false)

// Функція для форматування дати для поля datetime-local
const formatDateTimeForInput = (date) => date.toISOString().slice(0, 16)

const exam = ref({
    title: '',
    instructions: '',
    start_at: formatDateTimeForInput(new Date()),
    end_at: formatDateTimeForInput(new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)),
    duration_minutes: 60,
    max_attempts: 1,
    pass_threshold: 60,
    course_id: courseId,
    questions: []
})

let tempIdCounter = 0

function getUniqueTempId() {
    // Створюємо надійний тимчасовий ID
    return `temp-id-${Date.now()}-${tempIdCounter++}`
}

function addQuestion(type) {
    const newQuestion = {
        temp_id: getUniqueTempId(),
        title: '',
        question_type: type,
        points: 1,
        options: [],
        matching_data: { prompts: [], matches: [] }
    };
    
    if (type === 'single_choice' || type === 'multi_choice') {
        for (let i = 0; i < 4; i++) {
            newQuestion.options.push({ 
                temp_id: getUniqueTempId(), 
                text: '', 
                is_correct: false 
            });
        }
    }
    exam.value.questions.push(newQuestion);
}

function removeQuestion(index) {
    exam.value.questions.splice(index, 1)
}

function capitalize(obj, key) {
    if (obj[key] && typeof obj[key] === 'string') {
        obj[key] = obj[key].charAt(0).toUpperCase() + obj[key].slice(1)
    }
}

async function handleSaveExam() {
    loading.value = true
    error.value = null
    success.value = false

    try {
        await createExam(exam.value)
        success.value = true

        // З невеликою затримкою перенаправляємо на сторінку іспитів курсу
        setTimeout(() => {
            router.push(`/courses/${courseId}/exams`)
        }, 1500)

    } catch (err) {
        if (err.response?.data?.detail) {
            error.value = err.response.data.detail
        } else {
            error.value = 'Не вдалося створити іспит. Будь ласка, спробуйте ще раз.'
        }
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
.form-wrapper {
    max-width: 800px;
}

.questions-section, .exam-settings-card {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.form-group,
.submit-button {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 12px;
    font-weight: bold;
    color: var(--color-dark-gray);
}

.form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.status-message {
    padding: 12px;
    border-radius: 8px;
    text-align: center;
    margin-top: 20px;
}

.error {
    color: var(--color-red);
}

.success {
    color: var(--color-green);
}
</style>