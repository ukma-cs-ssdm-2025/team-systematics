<template>
    <div class="question-block">
        <ol class="multi-choice-list">
            <li v-for="option in options" :key="option.id" class="option-row" :class="[getOptionClasses(option), { 'review-mode': isReviewMode }]"
                @click="!isReviewMode && handleOptionClick(option)">
                <CCheckbox 
                    :modelValue="isChecked(option)" 
                    @update:modelValue="handleCheckboxChange(option.id, $event)"
                    :disabled="isReviewMode" 
                />
                <div class="option-content">
                    <p class="option-text">{{ option.text }}</p>
                    <p
                        v-if="isReviewMode && showCorrectAnswers && (option.is_correct || option.is_selected)"
                        class="option-points">
                            ({{ formattedPointsPerMatch(option) }} б)
                    </p>
                </div>
            </li>
        </ol>
    </div>
</template>

<script setup>
import CCheckbox from '../global/CCheckbox.vue'

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
    },
    showCorrectAnswers: {
        type: Boolean,
        default: true
    }
})

const emit = defineEmits(['update:modelValue'])

// Функція для обробки змін стану чекбоксів
function handleCheckboxChange(optionId, checked) {
    const currentValues = Array.isArray(props.modelValue) ? props.modelValue : []

    let newModelValue = [...currentValues]

    if (checked) {
        // Перевіряємо, чи цього значення ще немає, щоб уникнути дублікатів
        if (!newModelValue.includes(optionId)) {
            newModelValue.push(optionId)
        }
    } else {
        newModelValue = newModelValue.filter(id => id !== optionId)
    }
    
    emit('update:modelValue', newModelValue)
}

// Обробник кліку на option-row для перемикання стану чекбокса
function handleOptionClick(option) {
    if (!props.isReviewMode) {
        const currentChecked = isChecked(option)
        handleCheckboxChange(option.id, !currentChecked)
    }
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
    // В режимі перегляду, ми додаємо класи для правильних/неправильних відповідей
    // Але тільки якщо дозволено показувати правильні відповіді
    return {
        selected: option.is_selected,
        correct: props.showCorrectAnswers && option.is_correct,
        incorrect: props.showCorrectAnswers && option.is_selected && !option.is_correct
    }
}

function formattedPointsPerMatch(option) {
    if (typeof option?.earned_points_per_option === 'number') {
        return option.earned_points_per_option.toFixed(0)
    }
    return '0'
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
    margin-bottom: 12px;
}

.multi-choice-list li:last-child {
    margin-bottom: 0;
}

.option-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border: 3px solid var(--color-gray);
    border-radius: 12px;
    transition: all 150ms ease;
    cursor: pointer;
}

.option-row:hover:not(.review-mode) {
    border-color: var(--color-dark-gray);
}

.option-row.selected {
    border-color: var(--color-purple);
    background-color: var(--color-lavender);
}

.option-content {
    display: flex;
    justify-content: space-between;
    flex-grow: 1;
}

.option-points {
    color: var(--color-black-half-opacity);
}

.option-row.review-mode {
    cursor: not-allowed;
}

.option-row.review-mode:hover {
    border-color: var(--color-gray);
}

.option-row.review-mode.selected:hover {
    border-color: var(--color-purple);
}

.option-row.correct {
    background-color: var(--color-green-half-opacity);
}

.option-row.incorrect {
    background-color: var(--color-red-half-opacity);
}

.option-row:has(:deep(.real-checkbox:focus-visible)) {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}
</style>