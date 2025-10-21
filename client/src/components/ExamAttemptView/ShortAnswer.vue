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
                    'correct': questionData.student_answer_text === questionData.correct_answer_text,
                    'incorrect': questionData.student_answer_text !== questionData.correct_answer_text
                }"
            >
                <p class="answer-text">{{ questionData.student_answer_text }}</p>
                <p class="answer-points">{{ questionData.earnedPoints }}</p>
            </div>

            <div 
                v-if="questionData.student_answer_text !== questionData.correct_answer_text"
                class="correct-answer"
            >
                Правильна відповідь: {{ questionData.correct_answer_text }}
            </div>
        </div>
    </div>
</template>

<script setup>
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
    }
});

const emit = defineEmits(['update:modelValue'])

function handleInput(event) {
    let value = event.target.value
    if (props.inputType === 'number') {
        const parsedValue = parseFloat(value)
        if (value.trim() !== '' && !isNaN(parsedValue)) {
            value = parsedValue
        }
    }
    emit('update:modelValue', value)
}
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