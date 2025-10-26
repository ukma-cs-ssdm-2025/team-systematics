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
                    <select
                        :id="`match-select-${prompt.id}`"
                        class="match-select"
                        :value="modelValue[prompt.id] || ''"
                        @change="updateMatch(prompt.id, $event.target.value)"
                    >
                        <option disabled value="">Виберіть відповідь...</option>
                        <option v-for="match in shuffledMatches" :key="match.id" :value="match.id">
                            {{ match.text }}
                        </option>
                    </select>
                </div>

                <div v-else class="review-item" :class="getReviewClasses(prompt)">
                    <span class="review-text">{{ getMatchText(prompt.student_match_id) }}</span>
                    <span class="review-points">({{ prompt.earned_points_per_match }} б)</span>
                </div>
            </div>

        </div>
    </div>
</template>

<script setup>
import { ref, watch } from 'vue'

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

// Тасування масиву (Fisher–Yates)
function shuffleArray(array) {
    let currentIndex = array.length, randomIndex
    while (currentIndex !== 0) {
        randomIndex = Math.floor(Math.random() * currentIndex)
        currentIndex--
        ;[array[currentIndex], array[randomIndex]] = [array[randomIndex], array[currentIndex]]
    }
    return array
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

function getMatchText(matchId) {
    if (!matchId)
        return 'Відповідь не надано'
    const match = props.matches.find(m => m.id === matchId)
    return match ? match.text : 'Невідома відповідь'
}

function getReviewClasses(prompt) {
    if (!props.isReviewMode)
        return {}
    return {
        correct: prompt.student_match_id === prompt.correct_match_id,
        incorrect: prompt.student_match_id !== prompt.correct_match_id
    }
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
    cursor: pointer;
    transition: all 150ms ease;
    appearance: none;
    background-image: url("data:image/svg+xml,%3csvg xmlns='http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c%2Fsvg%3e");
    background-position: right 16px center;
    background-repeat: no-repeat;
    background-size: 24px;
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
