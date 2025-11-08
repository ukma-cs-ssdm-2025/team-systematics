<template>
    <div class="question-editor-card">
        <div class="card-header">
            <span class="question-position">Питання {{ index + 1 }}</span>
            <button @click="$emit('delete')" class="delete-btn" title="Видалити питання">🗑️</button>
        </div>
        <div class="form-group">
            <label>Текст питання</label>
            <CInput type="text" v-model.trim="question.title" @blur="capitalize(question, 'title')"
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

        <!-- РЕДАКТОР ДЛЯ MATCHING (ДОПОВНЕНО) -->
        <div v-else-if="question.question_type === 'matching'">
            <div class="matching-editor-grid">
                <!-- Ліва колонка: Терміни + вибір відповідності -->
                <div class="matching-column">
                    <h4>Терміни (ліва колонка)</h4>
                    <div v-for="(prompt, promptIndex) in question.matching_data.prompts" :key="prompt.temp_id"
                        class="matching-row">
                        <CInput type="text" v-model.trim="prompt.text" placeholder="Термін..." />
                        <CSelect v-model="prompt.correct_match_id" :options="matchOptions"
                            placeholder="Виберіть відповідність..." />
                        <button @click="removePrompt(promptIndex)" class="remove-option-btn"
                            title="Видалити термін">✖</button>
                    </div>
                    <CButton type="button" @click="addPrompt" class="add-option-btn">+ Додати термін</CButton>
                </div>

                <!-- Права колонка: Визначення -->
                <div class="matching-column">
                    <h4>Визначення (права колонка)</h4>
                    <div v-for="(match, matchIndex) in question.matching_data.matches" :key="match.temp_id"
                        class="matching-row-right">
                        <CInput type="text" v-model.trim="match.text" placeholder="Визначення..." />
                        <button @click="removeMatch(matchIndex)" class="remove-option-btn"
                            title="Видалити визначення">✖</button>
                    </div>
                    <CButton @click="addMatch" class="add-option-btn">+ Додати визначення</CButton>
                </div>
            </div>
        </div>

        <!-- Для Short & Long Answer додаткових полів не потрібно -->
        <div v-else>
            <p class="placeholder-text">Для цього типу питання додаткові налаштування не потрібні.</p>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import CButton from '../global/CButton.vue'
import CInput from '../global/CInput.vue'
import CSelect from '../global/CSelect.vue'
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
    question.value.options.push({ text: '', is_correct: false })
}

function removeOption(index) {
    question.value.options.splice(index, 1)
}

function setCorrectOptionSingle(selectedId) {
    question.value.options.forEach(opt => {
        opt.is_correct = (opt.temp_id === selectedId)
    });
}
function getCorrectOptionId() {
    const correctOption = question.value.options.find(opt => opt.is_correct)
    return correctOption ? correctOption.temp_id : null
}

// --- Логіка для Matching ---
function addPrompt() {
    question.value.matching_data.prompts.push({ temp_id: getUniqueTempId(), text: '', correct_match_id: '' })
}

function removePrompt(index) {
    question.value.matching_data.prompts.splice(index, 1)
}

function addMatch() {
    question.value.matching_data.matches.push({ temp_id: getUniqueTempId(), text: '' })
}

function removeMatch(index) {
    const matchToRemove = question.value.matching_data.matches[index]
    // Перед видаленням, розірвемо зв'язок з усіма prompt, які на нього посилались
    question.value.matching_data.prompts.forEach(p => {
        if (p.correct_match_id === matchToRemove.temp_id) {
            p.correct_match_id = ''
        }
    })
    question.value.matching_data.matches.splice(index, 1)
}

// Computed-властивість для перетворення `matches` у формат для CSelect
const matchOptions = computed(() => {
    return question.value.matching_data.matches.map(match => ({
        value: match.temp_id,
        text: match.text || '...'
    }))
})

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

.matching-editor-grid {
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: 32px;
}

.matching-column h4 {
    margin-top: 0;
    margin-bottom: 16px;
}

.matching-row {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    gap: 8px;
    margin-bottom: 12px;
    align-items: center;
}

.matching-row-right {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 8px;
    margin-bottom: 12px;
    align-items: center;
}

.placeholder-text {
    font-style: italic;
    color: var(--color-dark-gray);
}

.editor-options-theme {
    /* --- Зелена тема для CRadio --- */
    --cr-selected-border: var(--color-green);
    --cr-selected-bg: var(--color-white); /* Залишаємо фон білим */
    --cr-badge-bg: var(--color-green);    /* Робимо сам бейдж зеленим */
    --cr-badge-text: var(--color-white);

    /* --- Зелена тема для CCheckbox --- */
    --cc-selected-border: var(--color-green);
    --cc-selected-bg: var(--color-green-half-opacity); /* Напівпрозорий зелений фон */
    --cc-icon-fill: var(--color-white); /* Біла галочка */
}
</style>