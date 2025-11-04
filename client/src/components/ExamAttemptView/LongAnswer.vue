<template>
    <div class="question-block">
        <textarea
            v-if="!isReviewMode"
            class="textarea-input"
            :value="modelValue"
            @input="$emit('update:modelValue', $event.target.value)"
            placeholder="Введіть розгорнуту відповідь..."
        ></textarea>

        <div v-else class="review-display">
            <div class="student-answer">
                <p class="answer-text">
                    {{ questionData.student_answer_text }}
                </p>
                
                <div class="points-display">
                    ({{ formattedEarnedPoints }} / {{ questionData.points }} б)
                </div>
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
    isReviewMode: {
        type: Boolean,
        default: false
    },
    questionData: {
        type: Object,
        default: () => ({})
    },
});

const formattedEarnedPoints = computed(() => {
    if (typeof props.questionData.earned_points === 'number') {
        return props.questionData.earned_points.toFixed(0);
    }
    return '--' // Повертаємо плейсхолдер, якщо балів немає
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.question-block {
    width: 60%;
    height: 400px;
    margin-bottom: 20px;
}

.textarea-input, .review-display {
    height: 100%;
    width: 100%;
    padding: 20px;
    background-color: var(--color-gray);
    border: 3px solid var(--color-gray);
    border-radius: 12px;
    font-family: inherit;
    font-size: inherit;
    transition: all 150ms ease;
    box-shadow: none;
    resize: none;
    line-height: 1.5;
}

.review-display {
    position: relative;
    cursor: not-allowed;
}

.textarea-input:hover {
    border-color: var(--color-dark-gray);
}

.textarea-input:focus-visible {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.points-display {
    position: absolute;
    left: 20px;
    bottom: 20px;
    color: var(--color-black-half-opacity);
}
</style>