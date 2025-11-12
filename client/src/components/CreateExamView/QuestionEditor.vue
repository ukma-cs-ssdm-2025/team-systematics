<template>
    <div class="question-editor-card">
        <div class="card-header">
            <span class="question-position">Питання {{ index + 1 }}</span>
            <button @click="$emit('delete')" class="delete-btn" title="Видалити питання">🗑️</button>
        </div>
        <div class="form-group">
            <label :for="`question-title-${question.temp_id}`">Текст питання</label>
            <CInput :id="`question-title-${question.temp_id}`" type="text" v-model.trim="question.title" @blur="capitalize(question, 'title')"
                placeholder="Наприклад, 'Встановіть відповідність між країною та її столицею'" />
        </div>

        <!-- Редактор для Single & Multi Choice -->
        <div v-if="question.question_type === 'single_choice' || question.question_type === 'multi_choice'">
            <h4 class="question-options">Варіанти відповіді</h4>

            <div class="editor-options-theme">
                <div v-for="(option, optIndex) in question.options" :key="option.temp_id" class="option-row">

                    <CRadio v-if="question.question_type === 'single_choice'" :modelValue="getCorrectOptionId()"
                        @update:modelValue="setCorrectOptionSingle" :value="option.temp_id"
                        :name="'correct-opt-' + question.temp_id" title="Позначити як правильну відповідь" />

                    <CCheckbox v-if="question.question_type === 'multi_choice'" v-model="option.is_correct"
                        title="Додати до списку правильних відповідей" />

                    <CInput type="text" v-model.trim="option.text" class="option-input"
                        placeholder="Введіть текст варіанту" />
                    <button @click="removeOption(optIndex)" class="remove-option-btn"
                        title="Видалити варіант">✖</button>
                </div>
                <CButton type="button" @click="addOption" class="add-option-btn">+ Додати варіант</CButton>
            </div>
        </div>

        <!-- РЕДАКТОР ДЛЯ MATCHING -->
        <div v-else-if="question.question_type === 'matching'">
            <h4 class="question-options">Пари термін-визначення</h4>
            <div v-for="(prompt, promptIndex) in question.matching_data.prompts" :key="prompt.temp_id"
                class="matching-pair-row">
                <CInput type="text" v-model.trim="prompt.text" placeholder="Термін..." class="matching-pair-input" />
                <span class="matching-arrow">→</span>
                <CInput type="text" :modelValue="getMatchText(prompt.correct_match_id)" 
                    @update:modelValue="updateMatchText(prompt, $event)"
                    placeholder="Визначення..." class="matching-pair-input" />
                <button @click="removeMatchingPair(promptIndex)" class="remove-option-btn"
                    title="Видалити пару">✖</button>
            </div>
            <CButton type="button" @click="addMatchingPair" class="add-option-btn">+ Додати пару</CButton>
        </div>

        <!-- Редактор для Short Answer -->
        <div v-else-if="question.question_type === 'short_answer'">
            <div class="form-group">
                <label :for="`correct-answer-${question.temp_id}`">Правильна відповідь</label>
                <input 
                    :id="`correct-answer-${question.temp_id}`"
                    type="text"
                    class="correct-answer-input"
                    :value="getCorrectAnswerText()"
                    @input="updateCorrectAnswer($event.target.value)"
                    placeholder="Введіть правильну відповідь..."
                />
            </div>
        </div>

        <!-- Для Long Answer додаткових полів не потрібно -->
        <div v-else-if="question.question_type === 'long_answer'">
            <p class="placeholder-text">Для цього типу питання додаткові налаштування не потрібні.</p>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import CButton from '../global/CButton.vue'
import CInput from '../global/CInput.vue'
import CRadio from '../global/CRadio.vue'
import CCheckbox from '../global/CCheckbox.vue'

const props = defineProps({
    modelValue: { type: Object, required: true },
    index: { type: Number, required: true }
})
const emit = defineEmits(['update:modelValue', 'delete'])

const question = computed({
    get: () => props.modelValue,
    set: (value) => emit('update:modelValue', value)
})

function capitalize(obj, key) {
    if (obj[key]) {
        obj[key] = obj[key].charAt(0).toUpperCase() + obj[key].slice(1)
    }
}

// --- Логіка для Single & Multi Choice ---
function addOption() {
    question.value.options.push({ 
        temp_id: getUniqueTempId(), 
        text: '', 
        is_correct: false 
    })
}

function removeOption(index) {
    question.value.options.splice(index, 1)
}

function setCorrectOptionSingle(selectedId) {
    for (const opt of question.value.options) {
        opt.is_correct = (opt.temp_id === selectedId)
    }
}
function getCorrectOptionId() {
    const correctOption = question.value.options.find(opt => opt.is_correct)
    return correctOption ? correctOption.temp_id : null
}

// --- Логіка для Matching ---
function addMatchingPair() {
    const matchId = getUniqueTempId()
    question.value.matching_data.prompts.push({ 
        temp_id: getUniqueTempId(), 
        text: '', 
        correct_match_id: matchId 
    })
    // Створюємо відповідний match
    if (!question.value.matching_data.matches) {
        question.value.matching_data.matches = []
    }
    question.value.matching_data.matches.push({ 
        temp_id: matchId, 
        text: '' 
    })
}

function removeMatchingPair(index) {
    const promptToRemove = question.value.matching_data.prompts[index]
    // Видаляємо відповідний match
    if (promptToRemove.correct_match_id) {
        const matchIndex = question.value.matching_data.matches.findIndex(
            m => m.temp_id === promptToRemove.correct_match_id
        )
        if (matchIndex !== -1) {
            question.value.matching_data.matches.splice(matchIndex, 1)
        }
    }
    // Видаляємо prompt
    question.value.matching_data.prompts.splice(index, 1)
}

function getMatchText(matchId) {
    if (!matchId || !question.value.matching_data.matches) {
        return ''
    }
    const match = question.value.matching_data.matches.find(m => m.temp_id === matchId)
    return match ? match.text : ''
}

function updateMatchText(prompt, text) {
    if (prompt.correct_match_id) {
        // Оновлюємо існуючий match
        const match = question.value.matching_data.matches.find(m => m.temp_id === prompt.correct_match_id)
        if (match) {
            match.text = text
        }
    } else {
        // Якщо match ще не створено, створюємо його
        const matchId = getUniqueTempId()
        prompt.correct_match_id = matchId
        if (!question.value.matching_data.matches) {
            question.value.matching_data.matches = []
        }
        question.value.matching_data.matches.push({
            temp_id: matchId,
            text: text
        })
    }
}

// Функція для генерації унікальних тимчасових ID
let tempIdCounter = 0
function getUniqueTempId() {
    return `temp-id-${Date.now()}-${tempIdCounter++}`
}

// --- Логіка для Short Answer ---
function getCorrectAnswerText() {
    if (!question.value.options || question.value.options.length === 0) {
        return ''
    }
    const correctOption = question.value.options.find(opt => opt.is_correct)
    return correctOption ? correctOption.text : ''
}

function updateCorrectAnswer(value) {
    // Якщо options не існує або порожній, створюємо перший option
    if (!question.value.options || question.value.options.length === 0) {
        question.value.options = [{
            temp_id: getUniqueTempId(),
            text: value,
            is_correct: true
        }]
    } else {
        // Знаходимо правильний option або створюємо новий
        let correctOption = question.value.options.find(opt => opt.is_correct)
        if (correctOption) {
            correctOption.text = value
        } else {
            // Якщо немає правильного option, робимо перший правильним
            question.value.options[0].text = value
            question.value.options[0].is_correct = true
        }
    }
}

</script>

<style scoped>
.question-editor-card {
    background: #ffffff;
    border: 1px solid var(--color-gray);
    border-radius: 12px;
    padding: 24px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--color-gray);
}

.question-position {
    font-weight: bold;
    font-size: 1.1rem;
    color: var(--color-black);
}

.question-options {
    margin-bottom: 8px;
}

.delete-btn {
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    color: var(--color-dark-gray);
}

.delete-btn:hover {
    color: var(--color-red);
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
}

.option-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
}

.correct-marker {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    cursor: pointer;
}

.option-input {
    flex-grow: 1;
}

.remove-option-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--color-red);
    font-size: 1rem;
}

.add-option-btn {
    margin-top: 8px;
}

.matching-pair-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
}

.matching-pair-input {
    flex: 1;
}

.matching-arrow {
    font-size: 1.2rem;
    color: var(--color-dark-gray);
    font-weight: bold;
}

.placeholder-text {
    font-style: italic;
    color: var(--color-dark-gray);
}

.editor-options-theme {
    --cr-selected-bg: var(--color-green);
    --cr-selected-text: var(--color-white);
    --cc-selected-border: var(--color-green);
    --cc-selected-bg: var(--color-green);
    --cc-icon-fill: var(--color-white);
}

.editor-options-theme :deep(.option-item.selected .letter-badge) {
    background-color: var(--color-green);
    color: var(--color-white);
}

.editor-options-theme :deep(.option-item.selected .custom-checkbox) {
    background-color: var(--color-green);
}

.editor-options-theme :deep(.option-item.selected .custom-checkbox svg path) {
    fill: var(--color-white);
}

/* Стилі для поля правильної відповіді (Short Answer) */
.correct-answer-input {
    width: 40%;
    padding: 20px;
    background-color: var(--color-gray);
    border: 3px solid var(--color-gray);
    border-radius: 12px;
    font-family: inherit;
    font-size: inherit;
    transition: all 150ms ease;
    box-shadow: none;
}

.correct-answer-input:hover {
    border-color: var(--color-dark-gray);
}

.correct-answer-input:focus-visible {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}
</style>