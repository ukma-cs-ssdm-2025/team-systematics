<template>
    <div class="question-block">
        <ol class="multi-choice-list">
            <li v-for="option in options" :key="option.id">
                <label 
                    class="option-item" 
                    :class="[getOptionClasses(option), { 'review-mode': isReviewMode }]"
                >
                    <!-- 1. Справжній чекбокс, який ми приховаємо -->
                    <input 
                        type="checkbox"
                        class="real-checkbox"
                        :value="option.id"
                        :checked="isChecked(option)"
                        :disabled="isReviewMode"
                        @change="!isReviewMode && handleChange($event)"
                    />

                    <!-- 2. Наш кастомний чекбокс, який змінює вигляд -->
                    <div class="custom-checkbox" aria-hidden="true">
                        <!-- Іконка галочки (SVG), яка з'являється при виборі -->
                        <svg xmlns="http://www.w3.org/2000/svg" width="17" height="13" viewBox="0 0 17 13" fill="none"
                            v-if="isChecked(option)">
                            <path d="M5.7 12.025L0 6.325L1.425 4.9L5.7 9.175L14.875 0L16.3 1.425L5.7 12.025Z"
                                fill="black" />
                        </svg>
                    </div>

                    <!-- 3. Текст варіанту відповіді -->
                    <div class="option-content">
                        <p class="option-text">{{ option.text }}</p>
                        <p
                            v-if="isReviewMode && (option.is_correct || option.is_selected)"
                            class="option-points">
                                ({{ option.earned_points_per_option }} б)
                        </p>
                    </div>
                </label>
            </li>
        </ol>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    options: {
        type: Array,
        required: true
    },
    modelValue: {
        type: Array,
        default: () => []
    },
    isReviewMode: {
        type: Boolean,
        default: false
    },
    earnedPoints: {
        type: Number,
        default: null
    }
})

const emit = defineEmits(['update:modelValue'])

// Функція для обробки змін стану чекбоксів
function handleChange(event) {
    const { value, checked } = event.target
    const currentValues = Array.isArray(props.modelValue) ? props.modelValue : []

    let newModelValue = [...currentValues]

    if (checked) {
        // Перевіряємо, чи цього значення ще немає, щоб уникнути дублікатів
        if (!newModelValue.includes(value)) {
            newModelValue.push(value)
        }
    } else {
        newModelValue = newModelValue.filter(id => id !== value)
    }
    
    emit('update:modelValue', newModelValue)
}

function isChecked(option) {
    if (props.isReviewMode) {
        return option.is_selected
    }
    return Array.isArray(props.modelValue) && props.modelValue.includes(option.id)
}

function getOptionClasses(option) {
    if (!props.isReviewMode) {
        return { selected: isChecked(option) }
    }
    return {
        selected: option.is_selected,
        correct: option.is_correct,
        incorrect: option.is_selected && !option.is_correct
    }
}

</script>

<style scoped>
.question-block {
    width: 60%;
    margin-bottom: 20px;
}

.multi-choice-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.multi-choice-list li {
    list-style: none;
}

.option-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border: 3px solid var(--color-gray);
    border-radius: 12px;
    cursor: pointer;
    transition: all 150ms ease;
}

.option-item:hover {
    border-color: var(--color-dark-gray);
}

.option-item.selected {
    border-color: var(--color-purple);
    background-color: var(--color-lavender);
}

.real-checkbox {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
    cursor: pointer;
}

.custom-checkbox {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 4px;
    background-color: var(--color-gray);
    transition: all 150ms ease;
}

.check-icon {
    width: 24px;
    height: 24px;
    stroke: var(--color-dark-purple);
    opacity: 0;
    transform: scale(0.5);
    transition: all 150ms ease;
}

.option-item.selected .check-icon {
    opacity: 1;
    transform: scale(1);
}

.option-item:has(.real-checkbox:focus-visible) {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.option-content {
    display: flex;
    justify-content: space-between;
    flex-grow: 1;
}

.option-points {
    color: var(--color-black-half-opacity);
}

.option-item.review-mode {
    cursor: not-allowed;
}
.option-item.review-mode:hover {
    border-color: var(--color-gray);
}

.option-item.review-mode.selected:hover {
    border-color: var(--color-purple);
}

.option-item.correct {
    background-color: var(--color-green-half-opacity);
}

.option-item.incorrect {
    background-color: var(--color-red-half-opacity);
}
</style>