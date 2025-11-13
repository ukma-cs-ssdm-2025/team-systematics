<template>
    <div class="question-block">
        <div class="matching-container">

            <!-- Заголовки колонок -->
            <div class="header-row">
                <div class="column-header"><h4>Питання</h4></div>
                <div class="column-header"><h4>Відповіді</h4></div>
            </div>

            <!-- Основний список -->
            <div v-for="prompt in prompts" :key="prompt.id" class="row">
                <label :for="`match-select-${prompt.id}`" class="prompt-item">
                    {{ prompt.text }}
                </label>

                <div v-if="!isReviewMode" class="match-item">
                    <CSelect
                        :modelValue="modelValue[prompt.id] || ''"
                        @update:modelValue="newValue => updateMatch(prompt.id, newValue)"
                        :options="selectOptions"
                        placeholder="Виберіть відповідь..."
                    />
                </div>

                <div v-else class="review-item" :class="getReviewClasses(prompt)">
                    <span class="review-text">{{ prompt.text }}</span>
                    <span class="review-points">({{ formattedPointsPerMatch(prompt) }} б)</span>
                </div>
            </div>

        </div>
    </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import CSelect from '../global/CSelect.vue'

const props = defineProps({
    prompts: {
        type: Array,
        required: true
    },
    matches: {
        type: Array,
        required: true
    },
    modelValue: {
        type: Object,
        default: () => ({})
    },
    isReviewMode: {
        type: Boolean,
        default: false
    },
})

const emit = defineEmits(['update:modelValue'])
const shuffledMatches = ref([])

const selectOptions = computed(() => {
    return shuffledMatches.value.map(match => ({
        value: match.id,
        text: match.text
    }));
});

// Тасування масиву (Fisher–Yates)
function shuffleArray(array) {
    let currentIndex = array.length, randomIndex
    while (currentIndex !== 0) {
        randomIndex = secureRandomInt(currentIndex)
        currentIndex--
        ;[array[currentIndex], array[randomIndex]] = [array[randomIndex], array[currentIndex]]
    }
    return array
}

// Return integer in range [0, max) using Web Crypto when available.
// Uses rejection sampling to avoid modulo bias. Falls back to Math.random().
function secureRandomInt(max) {
    if (typeof window !== 'undefined' && window.crypto && window.crypto.getRandomValues && max > 0) {
        const uint32Max = 0xFFFFFFFF
        const range = max
        const threshold = (uint32Max + 1) - ((uint32Max + 1) % range)
        const arr = new Uint32Array(1)
        let r
        do {
            window.crypto.getRandomValues(arr)
            r = arr[0]
        } while (r >= threshold)
        return r % range
    }
    // Fallback: not cryptographically secure, but fine for UI shuffling when crypto is unavailable
    return Math.floor(Math.random() * max)
}

watch(
    () => props.matches, 
    (newMatches) => {
        // Перевіряємо, чи newMatches - це дійсно масив з елементами
        if (Array.isArray(newMatches) && newMatches.length > 0 && !props.isReviewMode) {
            shuffledMatches.value = shuffleArray([...newMatches]);
        }
    },
    { immediate: true }
)

function updateMatch(promptId, selectedMatchId) {
    const newModelValue = { ...props.modelValue }
    newModelValue[promptId] = selectedMatchId
    emit('update:modelValue', newModelValue)
}

function getReviewClasses(prompt) {
    if (!props.isReviewMode)
        return {}
    return {
        correct: prompt.student_match_id === prompt.correct_match_id,
        incorrect: prompt.student_match_id !== prompt.correct_match_id
    }
}

function formattedPointsPerMatch(prompt) {
    return prompt.earned_points_per_match.toFixed(0)
}
</script>

<style scoped>
.question-block {
    width: 80%;
    margin-bottom: 20px;
}

.matching-container {
    display: grid;
    gap: 16px;
}

.header-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    font-weight: bold;
    margin-bottom: 4px;
}

.row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    align-items: stretch;
}

.prompt-item {
    background-color: var(--color-gray);
    padding: 16px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    height: 100%;
}

.match-select, .review-item {
    display: flex;
    align-items: center;
    width: 100%;
    height: 100%;
    padding: 0 16px;
    border: 2px solid var(--color-gray);
    border-radius: 8px;
    background-color: white;
    font-family: inherit;
    transition: all 150ms ease;
}

.match-select {
    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml,%3csvg xmlns='http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c%2Fsvg%3e");
    background-position: right 16px center;
    background-repeat: no-repeat;
    background-size: 24px;
}

.review-item {
    cursor: not-allowed;
}

.match-select:hover {
    border-color: var(--color-dark-gray);
}

.match-select:focus-visible {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.review-item.correct {
    background-color: var(--color-green-half-opacity);
}

.review-item.incorrect {
    background-color: var(--color-red-half-opacity);
}

.review-points {
    color: var(--color-black-half-opacity);
    margin-left: 8px;
}

</style>
