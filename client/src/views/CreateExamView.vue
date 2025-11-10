<template>
    <div>
        <Header />
        <main class="container">
            <div class="content-div">
                <div class="page-header">
                    <h2>{{ isEditMode ? 'Редагування іспиту' : 'Створення нового іспиту' }}</h2>
                </div>

                <form @submit="handleSaveExam" class="form-wrapper">
                    <!-- Секція 1: Налаштування іспиту -->
                    <div class="exam-settings-card">
                        <h3>Основні налаштування</h3>

                        <div class="form-group" :class="{ 'has-error': titleError }">
                            <label for="exam-title">Назва іспиту</label>
                            <CInput id="exam-title" v-model.trim="exam.title" @blur="validateTitle" required
                                :disabled="loading" placeholder="Наприклад, 'Модульний контроль №1'" />
                            <div v-if="titleError" class="field-error">{{ titleError }}</div>
                        </div>

                        <div class="form-grid">
                            <div class="form-group" :class="{ 'has-error': startDateError }">
                                <label for="exam-start">Дата та час початку</label>
                                <CInput id="exam-start" type="datetime-local" v-model="exam.start_at" 
                                    :min="minStartDateTime" step="60" required :disabled="loading"
                                    @update:modelValue="validateStartDate"
                                    @blur="validateStartDate(exam.start_at)" />
                                <div v-if="startDateError" class="field-error">{{ startDateError }}</div>
                            </div>
                            <div class="form-group" :class="{ 'has-error': endDateError }">
                                <label for="exam-end">Дата та час завершення</label>
                                <CInput id="exam-end" type="datetime-local" v-model="exam.end_at" 
                                    :min="minEndDateTime" step="60" required :disabled="loading" 
                                    @update:modelValue="validateEndDate"
                                    @blur="validateEndDate(exam.end_at)" />
                                <div v-if="endDateError" class="field-error">{{ endDateError }}</div>
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
const startDateError = ref(null)
const endDateError = ref(null)
const titleError = ref(null)
// Флаг для відстеження автоматичних оновлень, щоб уникнути зациклення
const isUpdatingDuration = ref(false)
const isUpdatingEndDate = ref(false)
// Флаг для відстеження, чи тривалість була змінена вручну (не через оновлення часу завершення)
const isDurationManuallyChanged = ref(false)
// Флаг для відстеження, чи час завершення був змінений вручну (не через оновлення тривалості)
const isEndDateManuallyChanged = ref(false)

// Ключ для localStorage
const STORAGE_KEY = isEditMode.value ? `exam-draft-${examId}` : `exam-draft-${courseId}`

// Функція для форматування дати для поля datetime-local
// Використовуємо локальний час, а не UTC, щоб уникнути проблем з часовими поясами
const formatDateTimeForInput = (date) => {
    const d = new Date(date)
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hours = String(d.getHours()).padStart(2, '0')
    const minutes = String(d.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}`
}

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

// Реактивна змінна для поточного часу (оновлюється при натиску кнопки "Створити іспит")
const currentTime = ref(new Date())

// Функція для оновлення поточного часу
function updateCurrentTime() {
    currentTime.value = new Date()
}

// Мінімальна дата/час (поточна дата/час) для поля дати початку
// Використовуємо currentTime.value для реактивності
const minStartDateTime = computed(() => {
    const now = currentTime.value
    // Округлюємо до найближчої хвилини в майбутньому
    const rounded = new Date(Math.ceil(now.getTime() / 60000) * 60000)
    return formatDateTimeForInput(rounded)
})

// Мінімальна дата/час для завершення - максимум з поточної дати та дати початку + 1 хвилина
const minEndDateTime = computed(() => {
    const now = currentTime.value
    const startDate = exam.value.start_at ? new Date(exam.value.start_at) : now
    // Додаємо 1 хвилину до дати початку
    const minEndDate = new Date(startDate.getTime() + 60000) // +1 хвилина
    // Округлюємо до найближчої хвилини
    const roundedNow = new Date(Math.ceil(now.getTime() / 60000) * 60000)
    const roundedMinEnd = new Date(Math.ceil(minEndDate.getTime() / 60000) * 60000)
    // Повертаємо більшу з двох дат (поточна або початок + 1 хвилина)
    return formatDateTimeForInput(roundedMinEnd > roundedNow ? roundedMinEnd : roundedNow)
})

// Валідація дати початку
function validateStartDate(value) {
    if (!value) {
        startDateError.value = null
        return
    }
    
    const startDate = new Date(value)
    const endDate = exam.value.end_at ? new Date(exam.value.end_at) : null
    // Використовуємо currentTime для перевірки
    const now = currentTime.value
    
    // Перевіряємо, чи дата/час початку не в минулому
    if (startDate < now) {
        // Показуємо помилку замість автоматичного виправлення
        startDateError.value = 'Дата та час початку не можуть бути в минулому'
        // Не оновлюємо значення автоматично - залишаємо як є, щоб користувач міг бачити помилку
        return
    } else {
        // Очищаємо помилку, якщо дата коректна
        startDateError.value = null
    }
    
    // Якщо дата початку змінилася і тепер дата завершення стала раніше або дорівнює початку,
    // встановлюємо дату завершення на основі тривалості, або мінімум початок + 1 хвилина
    // watch для end_at автоматично викличе validateEndDate
    if (endDate && endDate <= startDate) {
        // Спробуємо використати тривалість, якщо вона встановлена
        if (exam.value.duration_minutes && exam.value.duration_minutes > 0) {
            updateEndDateFromDuration()
        } else {
            // Інакше встановлюємо мінімум: початок + 1 хвилина
            const minEndDate = new Date(startDate.getTime() + 60000) // +1 хвилина
            const roundedNow = new Date(Math.ceil(now.getTime() / 60000) * 60000)
            const newEndDate = minEndDate > roundedNow ? minEndDate : roundedNow
            exam.value.end_at = formatDateTimeForInput(newEndDate)
            // watch для end_at автоматично викличе validateEndDate
        }
    } else if (endDate && exam.value.duration_minutes) {
        // Якщо дата початку змінилася, але дата завершення все ще коректна,
        // оновлюємо час завершення на основі нової дати початку та тривалості
        updateEndDateFromDuration()
    }
}

// Оновлення часу завершення на основі тривалості
// forceUpdate - чи примусово оновити, навіть якщо час завершення був змінений вручну (для виправлення некоректних значень)
function updateEndDateFromDuration(forceUpdate = false) {
    if (isUpdatingEndDate.value || !exam.value.start_at || !exam.value.duration_minutes) {
        return
    }
    
    // Перевіряємо, чи час завершення некоректний (раніше за час початку)
    const startDate = new Date(exam.value.start_at)
    const currentEndDate = exam.value.end_at ? new Date(exam.value.end_at) : null
    const isInvalid = currentEndDate && currentEndDate <= startDate
    
    // Не оновлюємо час завершення, якщо він був змінений вручну І час завершення коректний
    // Але завжди оновлюємо, якщо час завершення некоректний або це примусове оновлення
    if (!forceUpdate && !isInvalid && isEndDateManuallyChanged.value) {
        return
    }
    
    // Якщо час завершення некоректний, скидаємо флаг ручної зміни
    if (isInvalid) {
        isEndDateManuallyChanged.value = false
    }
    
    isUpdatingEndDate.value = true
    try {
        const durationMs = exam.value.duration_minutes * 60 * 1000
        const newEndDate = new Date(startDate.getTime() + durationMs)
        const newEndDateFormatted = formatDateTimeForInput(newEndDate)
        
        exam.value.end_at = newEndDateFormatted
        // Викликаємо валідацію дати завершення без оновлення тривалості (щоб уникнути зациклення)
        validateEndDate(exam.value.end_at, false)
    } finally {
        // Використовуємо nextTick, щоб watch для end_at не спрацював одразу
        setTimeout(() => {
            isUpdatingEndDate.value = false
        }, 10)
    }
}

// Оновлення тривалості на основі часу завершення
function updateDurationFromEndDate() {
    if (isUpdatingDuration.value || !exam.value.start_at || !exam.value.end_at) {
        return
    }
    
    // Не оновлюємо тривалість, якщо вона була змінена вручну
    // Але якщо час завершення був змінений вручну, оновлюємо тривалість (це нормально)
    if (isDurationManuallyChanged.value && !isEndDateManuallyChanged.value) {
        return
    }
    
    isUpdatingDuration.value = true
    try {
        const startDate = new Date(exam.value.start_at)
        const endDate = new Date(exam.value.end_at)
        const durationMs = endDate.getTime() - startDate.getTime()
        const durationMinutes = Math.floor(durationMs / (60 * 1000))
        
        // Якщо час завершення раніше за час початку, це некоректно
        // У такому випадку не оновлюємо тривалість, а залишаємо як є
        // (валідація покаже помилку)
        if (durationMinutes <= 0) {
            return
        }
        
        // Оновлюємо тривалість, якщо вона відрізняється від поточної
        const currentDuration = exam.value.duration_minutes || 0
        if (durationMinutes !== currentDuration) {
            exam.value.duration_minutes = durationMinutes
        }
    } finally {
        // Використовуємо nextTick, щоб watch для duration_minutes не спрацював одразу
        setTimeout(() => {
            isUpdatingDuration.value = false
        }, 10)
    }
}

// Валідація дати завершення
// updateDuration - чи потрібно оновлювати тривалість на основі часу завершення (за замовчуванням true)
function validateEndDate(value, updateDuration = true) {
    if (!value) {
        endDateError.value = null
        return
    }
    
    const endDate = new Date(value)
    const startDate = exam.value.start_at ? new Date(exam.value.start_at) : null
    // Використовуємо currentTime для перевірки
    const now = currentTime.value
    
    // Перевіряємо, чи дата/час завершення не в минулому
    if (endDate < now) {
        // Показуємо помилку замість автоматичного виправлення
        endDateError.value = 'Дата та час завершення не можуть бути в минулому'
        return
    }
    
    // Перевіряємо, чи дата завершення не раніше дати початку
    if (startDate && endDate <= startDate) {
        // Якщо час завершення раніше за час початку, але тривалість встановлена,
        // автоматично виправляємо час завершення на основі тривалості
        // (навіть якщо час завершення був введений вручну, бо це некоректне значення)
        if (exam.value.duration_minutes && exam.value.duration_minutes > 0) {
            // Виправляємо час завершення на основі тривалості (примусово)
            updateEndDateFromDuration(true)
            return
        }
        // Показуємо помилку, якщо автоматичне виправлення неможливе
        endDateError.value = 'Дата та час завершення не можуть бути раніше або дорівнювати часу початку'
        return
    }
    
    // Очищаємо помилку, якщо дата коректна
    endDateError.value = null
    
    // Оновлюємо тривалість на основі нового часу завершення (тільки якщо помилок немає і дозволено оновлення)
    if (updateDuration && !endDateError.value && !isUpdatingDuration.value) {
        updateDurationFromEndDate()
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
        // watch для duration_minutes автоматично викличе updateEndDateFromDuration
        return
    }
    
    // Конвертуємо в число
    let numValue = Number(cleanedValue)
    
    // Якщо не число або NaN, встановлюємо мінімальне значення
    if (isNaN(numValue)) {
        exam.value[field] = field === 'pass_threshold' ? 0 : 1
        // watch для duration_minutes автоматично викличе updateEndDateFromDuration
        return
    }
    
    // Якщо від'ємне число, встановлюємо мінімальне значення
    if (numValue < 0) {
        exam.value[field] = field === 'pass_threshold' ? 0 : 1
        // watch для duration_minutes автоматично викличе updateEndDateFromDuration
        return
    }
    
    // Для прохідного балу перевіряємо максимум
    if (field === 'pass_threshold' && numValue > 100) {
        exam.value[field] = 100
        return
    }
    
    // Округлюємо до цілого числа
    exam.value[field] = Math.floor(numValue)
    // watch для duration_minutes автоматично викличе updateEndDateFromDuration
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
    // Оновлюємо поточний час при монтуванні
    updateCurrentTime()
    
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
            
            // Валідуємо дати після завантаження з бекенду
            validateStartDate(exam.value.start_at)
            validateEndDate(exam.value.end_at)
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
            // Валідуємо дати, якщо вони в минулому
            validateStartDate(exam.value.start_at)
            validateEndDate(exam.value.end_at)
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

// Валідуємо дату початку при зміні (тільки якщо не завантажуємо зі сховища)
watch(() => exam.value.start_at, (newValue) => {
    if (newValue && !isLoadingFromStorage.value) {
        validateStartDate(newValue)
        // Також перевіряємо дату завершення, якщо вона існує
        // (навіть якщо validateStartDate оновлює end_at, watch для end_at викличе validateEndDate)
        if (exam.value.end_at) {
            // Викликаємо validateEndDate тільки якщо end_at не було оновлено в validateStartDate
            // (якщо end_at <= start_at, validateStartDate оновить end_at, і watch викличе validateEndDate)
            // Але для перевірки, чи end_at не в минулому, викликаємо validateEndDate вручну
            validateEndDate(exam.value.end_at)
        }
    }
})

// Валідуємо дату завершення при зміні (тільки якщо не завантажуємо зі сховища)
watch(() => exam.value.end_at, (newValue, oldValue) => {
    if (newValue && !isLoadingFromStorage.value && !isUpdatingEndDate.value) {
        // Якщо час завершення змінився не через автоматичне оновлення (isUpdatingEndDate = false),
        // то це ручна зміна користувача
        if (oldValue && newValue !== oldValue) {
            isEndDateManuallyChanged.value = true
            // Скидаємо флаг ручної зміни тривалості, бо тепер користувач змінює час завершення
            isDurationManuallyChanged.value = false
        }
        validateEndDate(newValue)
    }
})

// Оновлюємо час завершення при зміні тривалості (тільки якщо не завантажуємо зі сховища)
watch(() => exam.value.duration_minutes, (newValue, oldValue) => {
    if (newValue && !isLoadingFromStorage.value && !isUpdatingDuration.value) {
        // Якщо тривалість змінилася не через автоматичне оновлення (isUpdatingDuration = false),
        // то це ручна зміна користувача
        if (oldValue && newValue !== oldValue) {
            isDurationManuallyChanged.value = true
            // Скидаємо флаг ручної зміни часу завершення, бо тепер користувач змінює тривалість
            isEndDateManuallyChanged.value = false
        }
        updateEndDateFromDuration()
    }
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

// Валідація назви іспиту
function validateTitle() {
    if (!exam.value.title || exam.value.title.trim() === '') {
        titleError.value = 'Назва іспиту обов\'язкова'
        return
    }
    
    if (exam.value.title.trim().length < 3) {
        titleError.value = 'Назва іспиту повинна містити мінімум 3 символи'
        return
    }
    
    // Капіталізуємо першу букву після валідації
    capitalize(exam.value, 'title')
    titleError.value = null
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
            // Перевірка наявності опцій
            if (!question.options || question.options.length === 0) {
                errors.push(`Питання ${questionNum}: додайте хоча б одну опцію відповіді.`)
            } else {
                // Перевірка, що всі опції або заповнені, або видалені (не має порожніх опцій)
                const emptyOptions = question.options.filter(opt => !opt.text || opt.text.trim() === '')
                if (emptyOptions.length > 0) {
                    errors.push(`Питання ${questionNum}: всі опції відповіді мають бути заповнені або видалені. Заповніть або видаліть порожні опції.`)
                }
                
                // Перевірка наявності опцій з текстом (після фільтрації порожніх)
                const filledOptions = question.options.filter(opt => opt.text && opt.text.trim() !== '')
                if (filledOptions.length === 0) {
                    errors.push(`Питання ${questionNum}: додайте хоча б одну опцію з текстом.`)
                } else if (filledOptions.length < 2) {
                    // Для single_choice та multi_choice потрібно мінімум 2 опції
                    errors.push(`Питання ${questionNum}: додайте хоча б дві опції відповіді.`)
                }
                
                // Перевірка наявності правильної відповіді
                const hasCorrectOption = filledOptions.some(opt => opt.is_correct === true)
                if (!hasCorrectOption) {
                    errors.push(`Питання ${questionNum}: оберіть правильний варіант відповіді.`)
                }
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

function handleSaveExam(event) {
    // Запобігаємо стандартній відправці форми
    if (event) {
        event.preventDefault()
    }
    
    // Перевіряємо стандартну HTML5 валідацію
    const form = event?.target || document.querySelector('.form-wrapper')
    if (form && !form.checkValidity()) {
        // Якщо стандартна валідація не пройдена, показуємо стандартні повідомлення браузера
        form.reportValidity()
        return
    }
    
    // Очищаємо попередні помилки
    error.value = null
    success.value = false
    
    // Оновлюємо поточний час при натиску кнопки "Створити іспит"
    updateCurrentTime()
    
    const allErrors = []
    
    // Валідація назви іспиту
    validateTitle()
    if (titleError.value) {
        allErrors.push(titleError.value)
    }
    
    // Перевіряємо дату початку з оновленим часом
    if (exam.value.start_at) {
        validateStartDate(exam.value.start_at)
        if (startDateError.value) {
            allErrors.push(startDateError.value)
        }
    }
    
    // Перевіряємо дату завершення з оновленим часом
    if (exam.value.end_at) {
        validateEndDate(exam.value.end_at)
        if (endDateError.value) {
            allErrors.push(endDateError.value)
        }
    }
    
    // Валідація питань
    const validationErrors = validateExam()
    allErrors.push(...validationErrors)
    
    // Якщо є помилки, показуємо їх
    if (allErrors.length > 0) {
        error.value = allErrors.length === 1 ? allErrors[0] : allErrors
        // Прокручуємо до помилок
        setTimeout(() => {
            // Спочатку намагаємося прокрутити до поля з помилкою (пріоритет: назва, дата початку, дата завершення)
            if (titleError.value) {
                const errorElement = document.querySelector('#exam-title')?.closest('.form-group')
                if (errorElement) {
                    errorElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
                    return
                }
            }
            if (startDateError.value) {
                const errorElement = document.querySelector('#exam-start')?.closest('.form-group')
                if (errorElement) {
                    errorElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
                    return
                }
            }
            if (endDateError.value) {
                const errorElement = document.querySelector('#exam-end')?.closest('.form-group')
                if (errorElement) {
                    errorElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
                    return
                }
            }
            // Інакше прокручуємо до повідомлення про помилки
            const errorElement = document.querySelector('.status-message.error')
            if (errorElement) {
                errorElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
            }
        }, 100)
        return
    }
    
    // Показуємо діалог підтвердження тільки якщо немає помилок
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
                    // Фільтруємо порожні опції перед відправкою на бекенд
                    questionData.options = (q.options || [])
                        .filter(opt => opt.text && opt.text.trim() !== '')
                        .map(opt => ({
                            text: opt.text.trim(),
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

.field-error {
    color: var(--color-red);
    font-size: 0.9em;
    margin-top: 5px;
}

.form-group.has-error :deep(.custom-input) {
    border-color: var(--color-red) !important;
}

.form-group.has-error :deep(.custom-input:hover) {
    border-color: var(--color-red) !important;
}

.form-group.has-error :deep(.custom-input:focus-visible) {
    outline-color: var(--color-red) !important;
    border-color: var(--color-red) !important;
}
</style>