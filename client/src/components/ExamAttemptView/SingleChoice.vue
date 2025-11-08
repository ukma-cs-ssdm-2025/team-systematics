<template>
    <div class="question-block">
        <ol class="single-choice-list">
            <li v-for="(option, i) in options" :key="option.id">
                <CRadio :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)"
                    :value="option.id" :name="uniqueGroupName" :badgeContent="letter(i)" :disabled="isReviewMode"
                    :class="getOptionClasses(option)">
                    <p class="option-text">{{ option.text }}</p>
                    <p v-if="isReviewMode && (option.is_correct || option.is_selected)" class="option-points">
                        ({{ option.is_correct && option.is_selected ? formattedPoints : 0 }} б)
                    </p>
                </CRadio>
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

defineEmits(['update:modelValue'])

// Генеруємо унікальне ім'я для групи радіокнопок, щоб вони працювали коректно
const uniqueGroupName = computed(() => `group-${Math.random()}`)

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
    return props.earnedPoints.toFixed(0)
})

</script>

<style scoped>
.question-block {
    width: 60%;
    margin-bottom: 20px;
}

.single-choice-list li {
    list-style: none;
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