<template>
    <div class="question-display-container">
        <!-- Заголовок питання (спільний для всіх типів) -->
        <div class="header">
            <div v-if="isReviewMode" class="question-meta">
                <span class="review-question-label">Питання {{ question.position }}</span>
                
                <div 
                    v-if="question.earned_points === null" 
                    class="tooltip-container"
                >
                    <span class="info-icon">!</span>
                    <div class="tooltip-text">
                        <strong>Увага!</strong> Деякі типи завдань (з розгорнутою відповіддю) потребують
                        перевірки викладачем. Оцінка за такі завдання буде відображена лише після їхньої
                        перевірки. Загальна оцінка не враховує оцінку таких завдань до моменту їхньої перевірки.
                    </div>
                </div>
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
    }
})

const emit = defineEmits(['answer-changed'])

const localAnswer = ref(null)

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

.tooltip-container {
    position: relative;
    display: inline-block;
    vertical-align: middle;
    margin-left: 8px;
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
    margin-bottom: 2px;
}

.tooltip-text {
    visibility: hidden;
    opacity: 0;
    width: 500px;
    background-color: #f0f0f0;
    text-align: left;
    padding: 15px;
    border-radius: 10px;
    border: 2px solid var(--color-orange);
    position: absolute;
    z-index: 1;
    bottom: 150%;
    left: 50%;
    transform: translateX(-50%);
    transition: opacity 0.3s, visibility 0.3s;
}

.tooltip-text::after {
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border-width: 8px;
    border-style: solid;
    border-color: var(--color-orange) transparent transparent transparent;
}

.tooltip-container:hover .tooltip-text {
    visibility: visible;
    opacity: 1;
}
</style>