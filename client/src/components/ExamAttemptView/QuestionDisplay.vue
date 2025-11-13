<template>
    <div class="question-display-container">
        <!-- Заголовок питання (спільний для всіх типів) -->
        <div class="header">
            <div v-if="isReviewMode" class="question-meta">
                <span class="review-question-label">Питання {{ question.position }}</span>
                
                <!-- Флажок для перевірки на плагіат (тільки для long_answer та вчителя) -->
                <button 
                    v-if="isReviewMode && isTeacher && question.question_type === 'long_answer'"
                    type="button"
                    class="plagiarism-flag-button"
                    :class="{ 'flagged': isFlagged, 'no-answer': !question.answer_id && !answerId }"
                    @click.stop="handleFlagClick"
                    :disabled="isFlagging"
                    :title="isFlagged ? 'Зняти позначення для перевірки на плагіат' : 'Позначити для перевірки на плагіат'"
                    :aria-label="isFlagged ? 'Зняти позначення для перевірки на плагіат' : 'Позначити для перевірки на плагіат'"
                >
                    <svg 
                        class="flag-icon"
                        xmlns="http://www.w3.org/2000/svg" 
                        width="20" 
                        height="20" 
                        viewBox="0 0 24 24" 
                        fill="none"
                        aria-hidden="true"
                    >
                        <path d="M5 2V22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M5 2L19 2L13 8L19 14L5 14V2Z" fill="currentColor" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
                
                <Tooltip v-if="isReviewMode && question.earned_points === null">
                    <template #trigger>
                        <span class="info-icon">!</span>
                    </template>
                    <template #content>
                        <strong>Увага!</strong> Деякі типи завдань (з розгорнутою відповіддю) потребують
                        перевірки викладачем. Оцінка за такі завдання буде відображена лише після їхньої
                        перевірки. Загальна оцінка не враховує оцінку таких завдань до моменту їхньої перевірки.
                    </template>
                </Tooltip>
            </div>

            <div class="title">{{ question.title }}</div>
        </div>

        <div class="body">
            <!-- 1. Single Choice (Радіокнопки) -->
            <div v-if="question.question_type === 'single_choice'">
                <SingleChoice
                    :options="question.options" v-model="localAnswer"
                    :is-review-mode="isReviewMode"
                    :earned-points="question.earned_points" 
                />
            </div>

            <!-- 2. Multi Choice (Чекбокси) -->
            <div v-else-if="question.question_type === 'multi_choice'">
                <MultipleChoice
                    :options="question.options"
                    v-model="localAnswer"
                    :is-review-mode="isReviewMode"
                    :earned-points="question.earned_points"
                />
            </div>

            <!-- 3. Short Answer (Коротка відповідь) -->
            <div v-else-if="question.question_type === 'short_answer'">
                <ShortAnswer v-model="localAnswer" :inputType="question.answer_format"
                    :placeholder="question.answer_format === 'text' ? 'Введіть вашу відповідь...' : 'Введіть число...'"
                    :is-review-mode="isReviewMode"
                    :question-data="question"
                />
            </div>

            <!-- 4. Long Answer (Розгорнута відповідь) -->
            <div v-else-if="question.question_type === 'long_answer'">
                <LongAnswer
                    v-model="localAnswer"
                    placeholder="Введіть відповідь..."
                    :is-review-mode="isReviewMode"
                    :question-data="question"
                    :is-teacher="isTeacher"
                    :attempt-id="attemptId"
                    @score-updated="(newScore) => emit('score-updated', question.id, newScore)"
                />
            </div>

            <!-- 5. Matching (Відповідність) -->
            <div v-else-if="question.question_type === 'matching'">
                <Matching
                    :prompts="question.matching_data.prompts"
                    :matches="question.matching_data.matches"
                    :modelValue="localAnswer"
                    :is-review-mode="isReviewMode"
                    @update:modelValue="localAnswer = $event" />
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import SingleChoice from './SingleChoice.vue'
import MultipleChoice from './MultipleChoice.vue'
import ShortAnswer from './ShortAnswer.vue'
import LongAnswer from './LongAnswer.vue'
import Matching from './Matching.vue'
import Tooltip from '../global/CTooltip.vue'
import { flagAnswerForPlagiarism, unflagAnswer, getFlaggedAnswers, getAnswerId } from '../../api/attempts.js'

const props = defineProps({
    question: {
        type: Object,
        required: true
    },
    savedAnswer: {
        type: [String, Number, Array, Object],
        default: null
    },
    isReviewMode: {
        type: Boolean,
        default: false
    },
    position: {
        type: Number,
        default: null
    },
    points: {
        type: Number,
        default: 0
    },
    isTeacher: {
        type: Boolean,
        default: false
    },
    attemptId: {
        type: String,
        default: null
    }
})

const emit = defineEmits(['answer-changed', 'score-updated'])

const localAnswer = ref(null)
const isFlagged = ref(false)
const isFlagging = ref(false)

// Функція для правильної ініціалізації стану відповіді
function initializeAnswerState() {
    switch (props.question.question_type) {
        case 'multi_choice':
            // Для multi-choice відповідь ЗАВЖДИ має бути масивом
            if (Array.isArray(props.savedAnswer)) {
                localAnswer.value = props.savedAnswer
            } else if (props.savedAnswer) {
                // Якщо з бекенду прийшов рядок, обгортаємо його в масив
                localAnswer.value = [props.savedAnswer]
            } else {
                localAnswer.value = [] // Якщо нічого немає, створюємо порожній масив
            }
            break;
        case 'matching':
            // Для matching відповідь має бути об'єктом
            localAnswer.value = props.savedAnswer || {}
            break;
        default:
            // Для всіх інших (single_choice, short_answer) - рядок або null
            localAnswer.value = props.savedAnswer
    }
}

// Слідкуємо за зміною самого питання. Коли воно змінюється,
// ми заново ініціалізуємо `localAnswer` до правильного типу.
watch(() => props.question, () => {
    initializeAnswerState()
}, {
    // immediate: true гарантує, що функція виконається і при першому завантаженні
    immediate: true
})

onMounted(() => {
    // Встановлюємо початкове значення на основі типу питання та збереженої відповіді
    switch (props.question.question_type) {
        case 'multi_choice':
            // Для multi-choice відповідь має бути масивом
            localAnswer.value = props.savedAnswer || []
            break
        case 'matching':
            // Для matching відповідь має бути об'єктом
            localAnswer.value = props.savedAnswer || {}
            break
        default:
            localAnswer.value = props.savedAnswer
    }
})

// Слідкуємо за змінами в `localAnswer`
watch(localAnswer, (newValue) => {
    emit('answer-changed', newValue)
}, {
    // Відстежуємо зміни всередині масивів (для multi_choice) та об'єктів (для matching)
    deep: true
})

// Зберігаємо answer_id окремо, якщо він не переданий в question
const answerId = ref(null);

const handleFlaggedStatus = async () => {
    // Якщо `is_flagged` визначено, використовуємо його значення
    if (props.question.is_flagged != null) { // Перевірка на `null` і `undefined`
        isFlagged.value = props.question.is_flagged;
    } else {
        // Якщо `is_flagged` не передано, перевіряємо через API
        await checkFlaggedStatus();
    }
};

const fetchAnswerId = async () => {
    if (props.attemptId && props.question.id) {
        try {
            const fetchedAnswerId = await getAnswerId(props.attemptId, props.question.id);
            if (fetchedAnswerId) {
                answerId.value = fetchedAnswerId;
                props.question.answer_id = fetchedAnswerId;
                await handleFlaggedStatus();
            }
        } catch (error) {
            // Логування помилки в консоль або виведення повідомлення
            console.error("Помилка при отриманні ID відповіді:", error);
        }
    }
};

onMounted(async () => {
    if (props.isReviewMode && props.isTeacher && props.question.question_type === 'long_answer') {
        if (props.question.answer_id) {
            answerId.value = props.question.answer_id;
            await handleFlaggedStatus();
        } else {
            await fetchAnswerId();
        }
    }
})

async function checkFlaggedStatus() {
    const currentAnswerId = props.question.answer_id || answerId.value
    if (!currentAnswerId) return
    try {
        const flaggedAnswers = await getFlaggedAnswers()
        isFlagged.value = flaggedAnswers.some(fa => fa.answer_id === currentAnswerId)
    } catch (error) {
        console.error('Failed to check flagged status:', error)
    }
}

function logButtonState() {
    console.log('Button state:', {
        answer_id: props.question.answer_id,
        isFlagging: isFlagging.value,
        isFlagged: isFlagged.value,
        question_id: props.question.id,
        question_type: props.question.question_type
    })
}

async function handleFlagClick(event) {
    event.stopPropagation()
    
    // Отримуємо answer_id з різних джерел
    let currentAnswerId = props.question.answer_id || answerId.value
    
    console.log('Flag button clicked! Initial state:', {
        question_answer_id: props.question.answer_id,
        answerId_value: answerId.value,
        currentAnswerId: currentAnswerId,
        attemptId: props.attemptId,
        question_id: props.question.id,
        question_type: props.question.question_type
    })
    
    // Якщо answer_id все ще немає, спробуємо отримати його через API
    if (!currentAnswerId && props.attemptId && props.question.id) {
        console.log('Fetching answer_id from API...', {
            attemptId: props.attemptId,
            questionId: props.question.id
        })
        try {
            currentAnswerId = await getAnswerId(props.attemptId, props.question.id)
            console.log('Received answer_id from API:', currentAnswerId)
            if (currentAnswerId) {
                answerId.value = currentAnswerId
                // Не змінюємо props напряму, це може викликати проблеми
            }
        } catch (error) {
            console.error('Failed to fetch answer_id:', error)
            if (error.response?.status === 404) {
                alert('Відповідь не знайдена. Можливо, студент ще не відповів на це питання.')
                return
            }
        }
    }
    
    if (!currentAnswerId) {
        console.error('No answer_id found for question:', {
            question_id: props.question.id,
            question_type: props.question.question_type,
            attemptId: props.attemptId
        })
        alert('Неможливо позначити: відсутній ID відповіді. Можливо, студент ще не відповів на це питання.')
        return
    }
    
    // Перевіряємо формат UUID
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    if (!uuidRegex.test(currentAnswerId)) {
        console.error('Invalid UUID format:', currentAnswerId)
        alert('Невірний формат ID відповіді. Спробуйте оновити сторінку.')
        return
    }
    
    if (isFlagging.value) {
        console.log('Already flagging, ignoring click')
        return // Вже виконується запит
    }
    
    isFlagging.value = true
    try {
        if (isFlagged.value) {
            console.log('Unflagging answer:', currentAnswerId)
            await unflagAnswer(currentAnswerId)
            isFlagged.value = false
        } else {
            console.log('Flagging answer:', currentAnswerId)
            const result = await flagAnswerForPlagiarism(currentAnswerId)
            console.log('Flagging successful:', result)
            isFlagged.value = true
        }
    } catch (error) {
        console.error('Error flagging/unflagging:', error)
        console.error('Error details:', {
            message: error.message,
            response: error.response?.data,
            status: error.response?.status
        })
        // Відновлюємо попереднє значення при помилці
        const errorMessage = error.response?.data?.error?.message || error.message || 'Не вдалося змінити статус позначення'
        alert(errorMessage)
    } finally {
        isFlagging.value = false
    }
}
</script>

<style scoped>
.header {
    display: flex;
    flex-direction: column;
    align-items: baseline; 
    gap: 16px;
    margin-bottom: 20px;
}

.review-question-label {
    font-weight: bold;
    margin: 20px 0;
}

.question-meta {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}

.info-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background-color: var(--color-orange);
    color: var(--color-white);
    font-weight: bold;
    font-size: 0.8rem;
    cursor: help;
    user-select: none;
    margin-left: 8px;
    margin-bottom: 2px;
}

.plagiarism-flag-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    margin-left: 12px;
    padding: 4px;
    background: transparent;
    border: 2px solid transparent;
    border-radius: 6px;
    cursor: pointer !important;
    transition: all 0.2s ease;
    user-select: none;
    position: relative;
    z-index: 10;
    pointer-events: auto !important;
}

.plagiarism-flag-button:not(:disabled):hover {
    background-color: rgba(128, 0, 128, 0.1);
    border-color: var(--color-purple);
}

.plagiarism-flag-button:focus-visible {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.plagiarism-flag-button.flagged {
    background-color: rgba(220, 53, 69, 0.1);
    border-color: #dc3545;
}

.plagiarism-flag-button.flagged:not(:disabled):hover {
    background-color: rgba(220, 53, 69, 0.2);
}

.plagiarism-flag-button:disabled {
    opacity: 0.4;
    cursor: not-allowed !important;
    pointer-events: none !important;
}

.plagiarism-flag-button:not(:disabled) {
    cursor: pointer !important;
    pointer-events: auto !important;
}

/* Переконаємося, що кнопка завжди клікабельна, якщо не disabled */
.plagiarism-flag-button:not(:disabled):active {
    transform: scale(0.95);
}

.plagiarism-flag-button.no-answer {
    opacity: 0.5;
}

.plagiarism-flag-button.no-answer:hover {
    opacity: 0.7;
}

.flag-icon {
    width: 20px;
    height: 20px;
    display: block;
    transition: all 0.2s ease;
    color: #6c757d; /* Сірий колір за замовчуванням */
}

.plagiarism-flag-button.flagged .flag-icon {
    color: #dc3545; /* Червоний колір коли позначено */
}

.plagiarism-flag-button:not(.flagged) .flag-icon {
    color: #6c757d; /* Сірий колір коли не позначено */
}

.plagiarism-flag-button:not(:disabled):hover:not(.flagged) .flag-icon {
    color: #dc3545; /* Червоний колір при наведенні */
}
</style>