<template>
    <div class="question-block">
        <input 
            v-if="!isReviewMode"
            :type="inputType"
            class="text-input"
            :value="modelValue"
            @input="handleInput"
            :placeholder="inputType === 'text' ? 'Введіть вашу відповідь...' : 'Введіть число...'"
        />
        <div v-else class="review-display">
            <div 
                class="student-answer"
                :class="{
                    'correct': showCorrectAnswers && isCorrect,
                    'incorrect': showCorrectAnswers && !isCorrect && questionData.student_answer_text !== null
                }"
            >
                <div class="answer-content">
                    <span class="answer-text">
                        {{ questionData.student_answer_text }}
                    </span>
                    <span v-if="showCorrectAnswers" class="answer-points">
                        ({{ isCorrect ? formattedPoints : 0 }} б)
                    </span>
                </div>
            </div>
        
            <div v-if="showCorrectAnswers && !isCorrect && questionData.correct_answer_text" class="correct-answer">
                <strong>Правильна відповідь:</strong> {{ questionData.correct_answer_text }}
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
    modelValue: { 
        type: String, 
        default: '' 
    },
    inputType: {
        type: String,
        default: 'text', // За замовчуванням - текстове поле
        validator: (value) => ['text', 'number'].includes(value) // Дозволяємо тільки 'text' або 'number'
    },
    isReviewMode: {
        type: Boolean,
        default: false
    },
    questionData: { 
        type: Object, 
        default: () => ({}) 
    },
    showCorrectAnswers: {
        type: Boolean,
        default: true
    }
})

const emit = defineEmits(['update:modelValue'])

function handleInput(event) {
    let value = event.target.value
    if (props.inputType === 'number') {
        const parsedValue = Number.parseFloat(value)
        if (value.trim() !== '' && !Number.isNaN(parsedValue)) {
            value = parsedValue
        }
    }
    emit('update:modelValue', value)
}

const isCorrect = computed(() => {
    return props.isReviewMode && props.questionData?.earned_points > 0
})

const formattedPoints = computed(() => {
    // 1. Використовуємо опціональний ланцюжок (?.) на випадок відсутності questionData
    // 2. Перевіряємо, що earned_points є числом
    if (typeof props.questionData?.earned_points === 'number') {
        return props.questionData.earned_points.toFixed(0)
    }
    // 3. Повертаємо безпечне значення за замовчуванням
    return '0';
})

</script>

<style scoped>
.question-block {
    width: 60%;
    margin-bottom: 20px;
}

.text-input, .student-answer {
    width: 40%;
    padding: 20px;
    background-color: var(--color-gray);
    border: 3px solid var(--color-gray);
    border-radius: 12px;;
    font-family: inherit;
    font-size: inerhit;
    transition: all 150ms ease;
    box-shadow: none;
}

.text-input:hover {
    border-color: var(--color-dark-gray);
}

.text-input:focus-visible {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px; 
}

.review-display {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.answer-content {
    display: flex;
    justify-content: space-between;
    flex-grow: 1;
}

.answer-points {
    color: var(--color-black-half-opacity);
}

.student-answer {
    cursor: not-allowed;
}

.student-answer.correct {
    background-color: var(--color-green-half-opacity);
}

.student-answer.incorrect {
    background-color: var(--color-red-half-opacity);
}

.correct-answer {
    font-size: 0.8em;
}
</style>