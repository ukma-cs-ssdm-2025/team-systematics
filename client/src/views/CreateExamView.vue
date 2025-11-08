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
                                <CInput id="exam-start" type="datetime-local" v-model="exam.start_at" 
                                    :max="maxDateTime" required :disabled="loading"
                                    @update:modelValue="validateStartDate" />
                            </div>
                            <div class="form-group">
                                <label for="exam-end">Дата та час завершення</label>
                                <CInput id="exam-end" type="datetime-local" v-model="exam.end_at" 
                                    :min="minEndDateTime" required :disabled="loading" 
                                    @update:modelValue="validateEndDate" />
                            </div>
                            <div class="form-group">
                                <label for="exam-duration">Тривалість (у хвилинах)</label>
                                <CInput id="exam-duration" type="number" 
                                    :modelValue="exam.duration_minutes"
                                    @update:modelValue="validatePositiveNumber('duration_minutes', $event)" 
                                    min="1" required :disabled="loading" />
                            </div>
                            <div class="form-group">
                                <label for="exam-attempts">Кількість спроб</label>
                                <CInput id="exam-attempts" type="number" 
                                    :modelValue="exam.max_attempts"
                                    @update:modelValue="validatePositiveNumber('max_attempts', $event)" 
                                    min="1" required :disabled="loading" />
                            </div>
                            <div class="form-group">
                                <label for="exam-threshold">Прохідний бал</label>
                                <CInput id="exam-threshold" type="number" 
                                    :modelValue="exam.pass_threshold"
                                    @update:modelValue="validatePositiveNumber('pass_threshold', $event)" 
                                    min="0" max="100" required :disabled="loading" />
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
                        <div v-if="error" class="status-message error">
                            <div v-if="Array.isArray(error)">
                                <div v-for="(err, index) in error" :key="index">{{ err }}</div>
                            </div>
                            <div v-else>{{ error }}</div>
                        </div>
                    </div>
                </form>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
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

// Максимальна дата/час (поточна дата/час) для datetime-local полів
const maxDateTime = computed(() => formatDateTimeForInput(new Date()))

// Мінімальна дата/час для завершення - максимум з поточної дати та дати початку + 1 хвилина
const minEndDateTime = computed(() => {
    const now = new Date()
    const startDate = exam.value.start_at ? new Date(exam.value.start_at) : now
    // Додаємо 1 хвилину до дати початку
    const minEndDate = new Date(startDate.getTime() + 60000) // +1 хвилина
    // Повертаємо більшу з двох дат (поточна або початок + 1 хвилина)
    return formatDateTimeForInput(minEndDate > now ? minEndDate : now)
})

// Валідація дати початку
function validateStartDate(value) {
    if (!value) return
    
    const startDate = new Date(value)
    const endDate = new Date(exam.value.end_at)
    const now = new Date()
    
    // Якщо дата початку змінилася і тепер дата завершення стала раніше або дорівнює початку,
    // встановлюємо дату завершення на початок + 1 хвилина
    if (endDate <= startDate) {
        const minEndDate = new Date(startDate.getTime() + 60000) // +1 хвилина
        exam.value.end_at = formatDateTimeForInput(minEndDate > now ? minEndDate : now)
    }
}

// Валідація дати завершення
function validateEndDate(value) {
    if (!value) return
    
    const endDate = new Date(value)
    const startDate = new Date(exam.value.start_at)
    const now = new Date()
    
    // Якщо дата завершення раніше за поточну дату
    if (endDate < now) {
        exam.value.end_at = formatDateTimeForInput(now)
        return
    }
    
    // Якщо дата завершення раніше або дорівнює даті початку, встановлюємо початок + 1 хвилина
    if (endDate <= startDate) {
        const minEndDate = new Date(startDate.getTime() + 60000) // +1 хвилина
        exam.value.end_at = formatDateTimeForInput(minEndDate > now ? minEndDate : now)
    }
}

// Валідація для числових полів - видаляє нечислові символи та від'ємні числа
function validatePositiveNumber(field, value) {
    // Якщо значення порожнє, залишаємо як є (не встановлюємо автоматично)
    if (value === null || value === undefined || value === '') {
        return
    }
    
    // Видаляємо всі нечислові символи (крім крапки для десяткових чисел, але ми працюємо з цілими)
    let cleanedValue = String(value).replace(/[^0-9]/g, '')
    
    // Якщо після очищення значення порожнє, встановлюємо мінімальне значення
    if (cleanedValue === '') {
        exam.value[field] = field === 'pass_threshold' ? 0 : 1
        return
    }
    
    // Конвертуємо в число
    let numValue = Number(cleanedValue)
    
    // Якщо не число або NaN, встановлюємо мінімальне значення
    if (isNaN(numValue)) {
        exam.value[field] = field === 'pass_threshold' ? 0 : 1
        return
    }
    
    // Якщо від'ємне число, встановлюємо мінімальне значення
    if (numValue < 0) {
        exam.value[field] = field === 'pass_threshold' ? 0 : 1
        return
    }
    
    // Для прохідного балу перевіряємо максимум
    if (field === 'pass_threshold' && numValue > 100) {
        exam.value[field] = 100
        return
    }
    
    // Округлюємо до цілого числа
    exam.value[field] = Math.floor(numValue)
}

const exam = ref({
    title: '',
    instructions: '',
    start_at: formatDateTimeForInput(new Date()),
    end_at: formatDateTimeForInput(new Date(Date.now() + 60 * 60 * 1000)), // +1 година за замовчуванням
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

// Валідація іспиту перед збереженням
function validateExam() {
    const errors = []
    
    // 1. Перевірка наявності питань
    if (!exam.value.questions || exam.value.questions.length === 0) {
        errors.push('Додайте хоча б одне питання до іспиту.')
        return errors
    }
    
    // 2. Перевірка кожного питання
    exam.value.questions.forEach((question, index) => {
        const questionNum = index + 1
        
        // Перевірка наявності тексту питання
        if (!question.title || question.title.trim() === '') {
            errors.push(`Питання ${questionNum}: введіть текст питання.`)
        }
        
        // Перевірка для single_choice та multi_choice
        if (question.question_type === 'single_choice' || question.question_type === 'multi_choice') {
            // Перевірка наявності опцій з текстом
            const filledOptions = question.options?.filter(opt => opt.text && opt.text.trim() !== '') || []
            if (filledOptions.length === 0) {
                errors.push(`Питання ${questionNum}: додайте хоча б одну опцію з текстом.`)
            }
            
            // Перевірка наявності правильної відповіді
            const hasCorrectOption = question.options?.some(opt => opt.is_correct === true) || false
            if (!hasCorrectOption) {
                errors.push(`Питання ${questionNum}: оберіть правильний варіант відповіді.`)
            }
        }
        
        // Перевірка для matching
        if (question.question_type === 'matching') {
            const prompts = question.matching_data?.prompts || []
            if (prompts.length === 0) {
                errors.push(`Питання ${questionNum}: додайте хоча б одну пару термін-визначення.`)
            } else {
                // Перевірка, чи всі пари заповнені
                prompts.forEach((prompt, promptIndex) => {
                    if (!prompt.text || prompt.text.trim() === '') {
                        errors.push(`Питання ${questionNum}, пара ${promptIndex + 1}: заповніть термін.`)
                    }
                    const match = question.matching_data?.matches?.find(m => m.temp_id === prompt.correct_match_id)
                    if (!match || !match.text || match.text.trim() === '') {
                        errors.push(`Питання ${questionNum}, пара ${promptIndex + 1}: заповніть визначення.`)
                    }
                })
            }
        }
        
        // Перевірка для short_answer
        if (question.question_type === 'short_answer') {
            const correctOption = question.options?.find(opt => opt.is_correct === true)
            if (!correctOption || !correctOption.text || correctOption.text.trim() === '') {
                errors.push(`Питання ${questionNum}: введіть правильну відповідь.`)
            }
        }
        
        // long_answer не потребує валідації (немає правильної відповіді)
    })
    
    return errors
}

async function handleSaveExam() {
    loading.value = true
    error.value = null
    success.value = false

    // Валідація перед збереженням
    const validationErrors = validateExam()
    if (validationErrors.length > 0) {
        error.value = validationErrors
        loading.value = false
        // Прокручуємо до помилок
        setTimeout(() => {
            const errorElement = document.querySelector('.status-message.error')
            if (errorElement) {
                errorElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
            }
        }, 100)
        return
    }

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

.error {
    color: var(--color-red);
}

.success {
    color: var(--color-green);
}
</style>