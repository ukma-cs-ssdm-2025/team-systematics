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
                    <HighlightedText 
                        :text="questionData.student_answer_text || ''"
                        :ranges="questionData.plagiarism_ranges || []"
                    />
                </p>
                
                <div v-if="isTeacher" class="teacher-actions">
                    <button 
                        type="button"
                        class="points-display editable"
                        @click="startEditing"
                        @keyup.enter="startEditing"
                        @keyup.space.prevent="startEditing"
                        :title="'Клік або Enter для редагування оцінки'"
                        :aria-label="`Оцінка: ${formattedEarnedPoints} з ${questionData.points} балів. Натисніть для редагування`"
                    >
                        <span v-if="!isEditing">
                            ({{ formattedEarnedPoints }} / {{ questionData.points }} б)
                        </span>
                        <div v-else class="score-edit" @click.stop>
                            <input 
                                type="text" 
                                v-model="editScore" 
                                @blur="saveScore"
                                @keyup.enter="saveScore"
                                @keyup.esc="cancelEditing"
                                @input="validateInput"
                                @keydown="preventInvalidInput"
                                inputmode="decimal"
                                pattern="\d*\.?\d*"
                                class="score-input"
                                ref="scoreInputRef"
                                :aria-label="`Введіть оцінку від 0 до ${questionData.points}`"
                            />
                            <span> / {{ questionData.points }} б</span>
                        </div>
                    </button>
                </div>
                <div v-else class="points-display">
                    ({{ formattedEarnedPoints }} / {{ questionData.points }} б)
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed, ref, nextTick, watch } from 'vue'
import { updateAnswerScore } from '../../api/attempts.js'
import HighlightedText from './HighlightedText.vue'

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
    isTeacher: {
        type: Boolean,
        default: false
    },
    attemptId: {
        type: String,
        default: null
    }
});

const emit = defineEmits(['update:modelValue', 'score-updated'])

const isEditing = ref(false)
const editScore = ref('0')  // Зберігаємо як рядок для text input
const scoreInputRef = ref(null)
const isSaving = ref(false)

const formattedEarnedPoints = computed(() => {
    // Перевіряємо, чи earned_points є числом (включаючи 0)
    // Важливо: 0 - це валідне значення, тому перевіряємо typeof, а не truthiness
    if (typeof props.questionData.earned_points === 'number') {
        return props.questionData.earned_points.toFixed(1);
    }
    // Повертаємо плейсхолдер тільки якщо earned_points є null або undefined
    return '--'
})

function startEditing(event) {
    if (!props.isTeacher || isSaving.value || isEditing.value) return
    
    // Запобігаємо подвійному спрацюванню
    if (event) {
        event.stopPropagation()
    }
    
    // Встановлюємо поточне значення або 0 (конвертуємо в рядок для text input)
    const currentScore = props.questionData.earned_points ?? 0
    editScore.value = currentScore.toString()
    isEditing.value = true
    
    // Фокусуємося на input після наступного рендеру
    nextTick(() => {
        if (scoreInputRef.value) {
            scoreInputRef.value.focus()
            // select() працює тільки для text input
            if (scoreInputRef.value.type === 'text' || scoreInputRef.value.type === '') {
                try {
                    scoreInputRef.value.select()
                } catch (selectionError) {
                    // Якщо select() не підтримується, просто встановлюємо курсор в кінець
                    console.warn('Failed to select input text, falling back to cursor positioning:', selectionError)
                    const length = scoreInputRef.value.value.length
                    if (scoreInputRef.value.setSelectionRange) {
                        scoreInputRef.value.setSelectionRange(length, length)
                    }
                }
            }
        }
    })
}

function cancelEditing() {
    isEditing.value = false
    const currentScore = props.questionData.earned_points ?? 0
    editScore.value = currentScore.toString()
}

function validateInput(event) {
    const input = event.target
    const inputValue = input.value.trim()
    
    // Якщо поле порожнє, дозволяємо (буде валідуватися при blur)
    if (inputValue === '' || inputValue === '.') {
        editScore.value = ''
        return
    }
    
    // Парсимо значення
    let value = Number.parseFloat(inputValue)
    
    // Якщо не число (наприклад, тільки крапка), не робимо нічого
    if (Number.isNaN(value)) {
        // Якщо це не просто порожня строка або крапка, очищаємо
        if (inputValue !== '.' && inputValue !== '') {
            input.value = ''
            editScore.value = '0'
        }
        return
    }
    
    // Обмежуємо значення між 0 і максимумом
    const maxPoints = props.questionData.points
    if (value < 0) {
        value = 0
    } else if (value > maxPoints) {
        value = maxPoints
    }
    
    // Форматуємо для відображення (зберігаємо десяткові, якщо вони є)
    // Використовуємо безпечний підхід: toFixed(1) завжди повертає один десятковий знак
    const fixedValue = value.toFixed(1)
    const formattedValue = fixedValue.endsWith('.0') ? fixedValue.slice(0, -2) : fixedValue
    // Оновлюємо значення (конвертуємо в рядок для text input)
    editScore.value = formattedValue
    input.value = formattedValue
}

function preventInvalidInput(event) {
    const key = event.key
    const input = event.target
    const currentValue = input.value
    const cursorPosition = input.selectionStart
    const selectionEnd = input.selectionEnd || cursorPosition
    const maxPoints = props.questionData.points
    
    // Дозволяємо служебні клавіші
    const allowedKeys = [
        'Backspace', 'Delete', 'Tab', 'Enter', 'Escape',
        'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
        'Home', 'End'
    ]
    
    if (allowedKeys.includes(key)) {
        return true
    }
    
    // Дозволяємо Ctrl/Cmd комбінації (copy, paste, select all, etc.)
    if (event.ctrlKey || event.metaKey) {
        return true
    }
    
    // Блокуємо мінус, плюс та експоненційну нотацію (не дозволяємо від'ємні числа)
    if (key === '-' || key === '+' || key === 'e' || key === 'E') {
        event.preventDefault()
        return false
    }
    
    // Дозволяємо тільки цифри та крапку
    if (!/[\d.]/.test(key)) {
        event.preventDefault()
        return false
    }
    
    // Перевірка на крапку (дозволяємо тільки одну)
    if (key === '.' && currentValue.includes('.')) {
        event.preventDefault()
        return false
    }
    
    // Перевірка на максимум при введенні цифри
    if (/\d/.test(key)) {
        // Створюємо нове значення після введення (замінюємо виділений текст, якщо є)
        const newValue = currentValue.slice(0, cursorPosition) + key + currentValue.slice(selectionEnd)
        
        // Перевіряємо, чи не перевищує максимум
        const numValue = Number.parseFloat(newValue)
        
        // Якщо значення перевищує максимум, просто блокуємо введення
        // Не встановлюємо максимум автоматично
        if (!Number.isNaN(numValue) && numValue > maxPoints) {
            event.preventDefault()
            return false
        }
    }
    
    return true
}

async function saveScore() {
    if (isSaving.value) return
    
    // Якщо поле порожнє, встановлюємо 0
    if (editScore.value === '' || editScore.value === null || Number.isNaN(Number.parseFloat(editScore.value))) {
        editScore.value = 0
    }
    
    const newScore = Number.parseFloat(editScore.value)
    
    // Фінальна валідація (на всяк випадок)
    if (Number.isNaN(newScore)) {
        cancelEditing()
        return
    }
    
    // Обмежуємо значення
    const validatedScore = Math.max(0, Math.min(newScore, props.questionData.points))
    
    // Перевірка, чи значення змінилося
    // Важливо: розрізняємо null (не оцінено) та 0 (оцінено в 0 балів)
    const currentScore = props.questionData.earned_points
    // Якщо поточне значення null або undefined, завжди зберігаємо (навіть якщо це 0)
    if (currentScore === null || currentScore === undefined) {
        // Зберігаємо нове значення (може бути 0)
    } else if (Math.abs(validatedScore - currentScore) < 0.01) {
        // Значення не змінилося, скасовуємо редагування
        cancelEditing()
        return
    }
    
    isSaving.value = true
    isEditing.value = false
    
    try {
        await updateAnswerScore(props.attemptId, props.questionData.id, validatedScore)
        emit('score-updated', validatedScore)
    } catch (error) {
        alert(error.message || 'Не вдалося оновити оцінку')
        // Відновлюємо попереднє значення
        cancelEditing()
    } finally {
        isSaving.value = false
    }
}

// Відстежуємо зміни в questionData.earned_points
watch(() => props.questionData.earned_points, (newValue) => {
    if (!isEditing.value) {
        editScore.value = (newValue ?? 0).toString()
    }
})
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

.points-display.editable {
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: background-color 0.2s;
    outline: none;
    border: none;
    background: transparent;
    font-family: inherit;
    font-size: inherit;
    color: inherit;
}

.points-display.editable:hover {
    background-color: rgba(0, 0, 0, 0.05);
}

.points-display.editable:focus {
    background-color: rgba(0, 0, 0, 0.08);
    outline: 2px solid var(--color-purple);
    outline-offset: 2px;
}

.teacher-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 12px;
}

.score-edit {
    display: flex;
    align-items: center;
    gap: 4px;
}

.score-input {
    width: 60px;
    padding: 2px 4px;
    border: 2px solid var(--color-purple);
    border-radius: 4px;
    font-size: inherit;
    font-family: inherit;
}

.score-input:focus {
    outline: none;
    border-color: var(--color-purple);
    box-shadow: 0 0 0 2px rgba(128, 0, 128, 0.2);
}
</style>