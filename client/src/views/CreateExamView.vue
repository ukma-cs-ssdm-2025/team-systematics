<template>
    <div>
        <Header />
        <main class="container">
            <div class="content-div">
                <div class="page-header">
                    <h2>{{ isEditMode ? 'Редагування іспиту' : 'Створення нового іспиту' }}</h2>
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
                        <CButton type="button" @click="showConfirmDialog = true" :disabled="loading" class="submit-button">
                            {{ loading ? 'Збереження...' : (isEditMode ? 'Оновити іспит' : 'Зберегти іспит') }}
                        </CButton>
                        <div v-if="success" class="status-message success">{{ isEditMode ? 'Іспит успішно оновлено!' : 'Іспит успішно створено!' }}</div>
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
        
        <!-- Попап підтвердження збереження -->
        <CPopup
            :visible="showConfirmDialog"
            :header="isEditMode ? 'Підтвердження оновлення іспиту' : 'Підтвердження створення іспиту'"
            :disclaimer="isEditMode ? 'Ви впевнені, що хочете оновити цей іспит? Зміни будуть застосовані до всіх майбутніх спроб.' : 'Ви впевнені, що хочете створити цей іспит? Перевірте всі дані перед збереженням.'"
            fst-button="Підтвердити"
            snd-button="Скасувати"
            @fstAction="confirmSaveExam"
            @sndAction="showConfirmDialog = false"
        />
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import CInput from '../components/global/CInput.vue'
import CTextarea from '../components/global/CTextarea.vue'
import QuestionEditor from '../components/CreateExamView/QuestionEditor.vue'
import QuestionTypeSelector from '../components/CreateExamView/QuestionTypeSelector.vue'
import CPopup from '../components/global/CPopup.vue'
import { createExam, getExamForEdit, updateExam } from '../api/exams.js'

const router = useRouter()
const route = useRoute()
const courseId = route.params.courseId
const examId = route.params.examId
const isEditMode = ref(!!examId)

const loading = ref(false)
const error = ref(null)
const success = ref(false)
const showConfirmDialog = ref(false)

// Ключ для localStorage
const STORAGE_KEY = isEditMode.value ? `exam-draft-${examId}` : `exam-draft-${courseId}`

// Функція для форматування дати для поля datetime-local
const formatDateTimeForInput = (date) => date.toISOString().slice(0, 16)

// Функція для збереження в localStorage
function saveToLocalStorage() {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(exam.value))
    } catch (err) {
        console.warn('Не вдалося зберегти в localStorage:', err)
    }
}

// Функція для відновлення з localStorage
function loadFromLocalStorage() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY)
        if (saved) {
            const savedData = JSON.parse(saved)
            // Перевіряємо, чи course_id відповідає
            if (savedData.course_id === courseId) {
                exam.value = savedData
                return true
            }
        }
    } catch (err) {
        console.warn('Не вдалося завантажити з localStorage:', err)
    }
    return false
}

// Функція для очищення localStorage
function clearLocalStorage() {
    try {
        localStorage.removeItem(STORAGE_KEY)
    } catch (err) {
        console.warn('Не вдалося очистити localStorage:', err)
    }
}

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

// Ініціалізація exam - спробуємо завантажити з localStorage, інакше використовуємо значення за замовчуванням
const defaultExam = {
    title: '',
    instructions: '',
    start_at: formatDateTimeForInput(new Date()),
    end_at: formatDateTimeForInput(new Date(Date.now() + 60 * 60 * 1000)), // +1 година за замовчуванням
    duration_minutes: 60,
    max_attempts: 1,
    pass_threshold: 60,
    course_id: courseId,
    questions: []
}

const exam = ref(defaultExam)
const isLoadingFromStorage = ref(false)

// Завантажуємо дані з localStorage або з бекенду при монтуванні компонента
onMounted(async () => {
    isLoadingFromStorage.value = true
    
    if (isEditMode.value) {
        // Режим редагування: завантажуємо з бекенду
        try {
            loading.value = true
            const examData = await getExamForEdit(examId)
            
            // Конвертуємо дані з бекенду в формат, який очікує фронтенд
            exam.value = {
                title: examData.title || '',
                instructions: examData.instructions || '',
                start_at: formatDateTimeForInput(new Date(examData.start_at)),
                end_at: formatDateTimeForInput(new Date(examData.end_at)),
                duration_minutes: examData.duration_minutes || 60,
                max_attempts: examData.max_attempts || 1,
                pass_threshold: examData.pass_threshold || 60,
                course_id: courseId,
                questions: (examData.questions || []).map(q => {
                    const question = {
                        id: q.id, // Зберігаємо id для редагування
                        temp_id: getUniqueTempId(), // Додаємо temp_id для Vue key
                        title: q.title || '',
                        question_type: q.question_type,
                        points: q.points || 1,
                        options: [],
                        matching_data: { prompts: [], matches: [] }
                    }
                    
                    // Якщо це matching питання, конвертуємо matching_data
                    if (q.question_type === 'matching' && q.matching_data) {
                        question.matching_data = q.matching_data
                    } else if (q.question_type === 'short_answer') {
                        // Для short_answer створюємо опцію з правильною відповіддю
                        const correctOption = q.options?.find(opt => opt.is_correct)
                        if (correctOption) {
                            question.options = [{
                                id: correctOption.id,
                                temp_id: getUniqueTempId(),
                                text: correctOption.text || '',
                                is_correct: true
                            }]
                        }
                    } else {
                        // Для single_choice та multi_choice
                        question.options = (q.options || []).map(opt => ({
                            id: opt.id,
                            temp_id: getUniqueTempId(),
                            text: opt.text || '',
                            is_correct: opt.is_correct || false
                        }))
                    }
                    
                    return question
                })
            }
        } catch (err) {
            console.error('Помилка завантаження іспиту:', err)
            error.value = err.message || 'Не вдалося завантажити іспит для редагування'
        } finally {
            loading.value = false
        }
    } else {
        // Режим створення: завантажуємо з localStorage
        const loaded = loadFromLocalStorage()
        if (loaded) {
            // Оновлюємо дати, якщо вони в минулому
            const now = new Date()
            const startDate = new Date(exam.value.start_at)
            if (startDate > now) {
                exam.value.start_at = formatDateTimeForInput(now)
            }
            const endDate = new Date(exam.value.end_at)
            if (endDate < now) {
                exam.value.end_at = formatDateTimeForInput(new Date(now.getTime() + 60 * 60 * 1000))
            }
        }
    }
    
    isLoadingFromStorage.value = false
})

// Зберігаємо в localStorage при зміні exam (з затримкою для уникнення надмірних записів)
let saveTimeout = null
watch(exam, () => {
    // Не зберігаємо, якщо зараз відбувається завантаження з localStorage
    if (isLoadingFromStorage.value) {
        return
    }
    if (saveTimeout) {
        clearTimeout(saveTimeout)
    }
    saveTimeout = setTimeout(() => {
        saveToLocalStorage()
    }, 500) // Зберігаємо через 500мс після останньої зміни
}, { deep: true })

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

function handleSaveExam() {
    // Валідація перед показом діалогу підтвердження
    const validationErrors = validateExam()
    if (validationErrors.length > 0) {
        error.value = validationErrors
        // Прокручуємо до помилок
        setTimeout(() => {
            const errorElement = document.querySelector('.status-message.error')
            if (errorElement) {
                errorElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
            }
        }, 100)
        return
    }
    
    // Показуємо діалог підтвердження
    showConfirmDialog.value = true
}

async function confirmSaveExam() {
    showConfirmDialog.value = false
    loading.value = true
    error.value = null
    success.value = false

    try {
        // Підготовка даних для відправки
        const examData = {
            title: exam.value.title,
            instructions: exam.value.instructions || null,
            start_at: new Date(exam.value.start_at).toISOString(),
            end_at: new Date(exam.value.end_at).toISOString(),
            duration_minutes: exam.value.duration_minutes,
            max_attempts: exam.value.max_attempts,
            pass_threshold: exam.value.pass_threshold,
            course_id: courseId,
            questions: exam.value.questions.map(q => {
                const questionData = {
                    title: q.title,
                    question_type: q.question_type,
                    points: q.points || 1,
                    options: []
                }
                
                // Для single_choice, multi_choice, short_answer
                if (q.question_type === 'single_choice' || q.question_type === 'multi_choice' || q.question_type === 'short_answer') {
                    questionData.options = (q.options || [])
                        .filter(opt => opt.text && opt.text.trim() !== '')
                        .map(opt => ({
                            text: opt.text,
                            is_correct: opt.is_correct || false
                        }))
                }
                
                // Для matching
                if (q.question_type === 'matching') {
                    questionData.matching_data = {
                        prompts: (q.matching_data?.prompts || [])
                            .filter(p => p.text && p.text.trim() !== '')
                            .map(p => {
                                const match = q.matching_data?.matches?.find(m => m.temp_id === p.correct_match_id)
                                return {
                                    text: p.text,
                                    correct_match: match?.text || ''
                                }
                            })
                    }
                }
                
                return questionData
            })
        }
        
        if (isEditMode.value) {
            await updateExam(examId, examData)
            success.value = true
            clearLocalStorage()
            router.push(`/courses/${courseId}/exams`)
        } else {
            await createExam(examData)
            success.value = true
            clearLocalStorage()
            router.push(`/courses/${courseId}/exams`)
        }

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