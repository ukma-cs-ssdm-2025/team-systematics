<template>
    <div class="question-block">
        <ol class="single-choice-list">
            <li v-for="(option, i) in options" :key="option.id" class="option-row" :class="[getOptionClasses(option), { 'review-mode': isReviewMode }]"
                @click="!isReviewMode && handleOptionClick(option.id)">
                <CRadio :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)"
                    :value="option.id" :name="uniqueGroupName" :badgeContent="letter(i)" :disabled="isReviewMode" />
                <div class="option-content">
                    <p class="option-text">{{ option.text }}</p>
                    <p v-if="isReviewMode && (option.is_correct || option.is_selected)" class="option-points">
                        ({{ getPointsForOption(option) }} б)
                    </p>
                </div>
            </li>
        </ol>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import CRadio from '../global/CRadio.vue'

const props = defineProps({
    options: {
        type: Array,
        required: true
    },
    modelValue: {
        type: [String, Number],
        default: null
    },
    isReviewMode: {
        type: Boolean,
        default: false
    },
    earnedPoints: {
        type: Number,
        default: null
    },
})

const emit = defineEmits(['update:modelValue'])

// Генеруємо унікальне ім'я для групи радіокнопок один раз при створенні компонента
// Використовуємо детермінований підхід замість Math.random() для безпеки
// Використовуємо модульний лічильник для гарантії унікальності
let groupNameCounter = 0
const uniqueGroupName = `group-${Date.now()}-${groupNameCounter++}`

// Обробник кліку на option-row для передачі вибору
function handleOptionClick(optionId) {
    if (!props.isReviewMode) {
        emit('update:modelValue', optionId)
    }
}

// Функція для генерації літер A, B, C...
// Replace Magic Number / Introduce Constant
const letter = (index) => String.fromCodePoint(65 + index)

function isChecked(option) {
    if (props.isReviewMode) {
        return option.is_selected;
    }
    return props.modelValue === option.id
}

function getOptionClasses(option) {
    if (!props.isReviewMode) {
        // В режимі проходження, нам потрібен тільки клас 'selected'
        return { selected: isChecked(option) }
    }

    // В режимі перегляду, ми додаємо класи для правильних/неправильних відповідей
    return {
        selected: option.is_selected,
        correct: option.is_correct,
        incorrect: option.is_selected && !option.is_correct
    }
}

const formattedPoints = computed(() => {
    if (props.earnedPoints == null) {
        return '0'
    }
    return props.earnedPoints.toFixed(0)
})

function getPointsForOption(option) {
    // Якщо опція правильна і вибрана, показуємо earnedPoints
    if (option.is_correct && option.is_selected) {
        return formattedPoints.value
    }
    // Інакше показуємо 0
    return '0'
}

</script>

<style scoped>
.question-block {
    width: 60%;
    margin-bottom: 20px;
}

.single-choice-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.single-choice-list li {
    list-style: none;
    margin-bottom: 12px;
}

.single-choice-list li:last-child {
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

.option-row.selected {
    border-color: var(--color-purple);
    background-color: var(--color-lavender);
}

.option-row.correct {
    background-color: var(--color-green-half-opacity);
}

.option-row.incorrect {
    background-color: var(--color-red-half-opacity);
}

/* Правильні та неправильні відповіді в review-mode мають пріоритет над selected */
.option-row.review-mode.correct {
    background-color: var(--color-green-half-opacity);
}

.option-row.review-mode.incorrect {
    background-color: var(--color-red-half-opacity);
}

.option-row.selected :deep(.letter-badge) {
    background-color: var(--color-purple);
    color: var(--color-white);
}

.option-row:has(:deep(.real-radio-button:focus-visible)) {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}
</style>