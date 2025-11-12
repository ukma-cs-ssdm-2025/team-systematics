<template>
    <div>
        <Header />
        <main class="container">
            <h2 class="page-title">Перевірка плагіату</h2>
            
            <div v-if="loading" class="status-message">Завантаження...</div>
            <div v-else-if="error" class="status-message error">{{ error }}</div>
            
            <div v-else-if="flaggedAnswers.length === 0" class="empty-state">
                <p>Немає позначених робіт для перевірки на плагіат.</p>
                <p class="hint">Позначте роботи студентів під час перевірки іспитів.</p>
            </div>
            
            <div v-else class="flagged-answers-container">
                <div class="selection-info" v-if="selectedAnswers.length > 0">
                    <span>Вибрано: {{ selectedAnswers.length }} робіт</span>
                    <button 
                        v-if="selectedAnswers.length === 2"
                        class="compare-button"
                        @click="goToComparison"
                    >
                        Порівняти вибрані роботи
                    </button>
                    <button 
                        class="clear-button"
                        @click="clearSelection"
                    >
                        Очистити вибір
                    </button>
                </div>
                
                <div class="flagged-answers-list">
                    <div 
                        v-for="answer in flaggedAnswers" 
                        :key="answer.answer_id"
                        class="flagged-answer-item"
                        :class="{ selected: isSelected(answer.answer_id) }"
                        @click="toggleSelection(answer)"
                    >
                        <div class="answer-checkbox">
                            <input 
                                type="checkbox"
                                :checked="isSelected(answer.answer_id)"
                                @click.stop="toggleSelection(answer)"
                            />
                        </div>
                        <div class="answer-content" @click="selectAnswer(answer)">
                            <div class="answer-header">
                                <h3 class="student-name">{{ answer.student_name }}</h3>
                                <span class="exam-title">{{ answer.exam_title }}</span>
                            </div>
                            <div class="answer-preview">
                                {{ answer.answer_text.substring(0, 150) }}{{ answer.answer_text.length > 150 ? '...' : '' }}
                            </div>
                            <div class="answer-meta">
                                <span class="flagged-date">Позначено: {{ formatDate(answer.flagged_at) }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import { getFlaggedAnswers } from '../api/attempts.js'

const router = useRouter()
const loading = ref(true)
const error = ref(null)
const flaggedAnswers = ref([])
const selectedAnswers = ref([])

onMounted(async () => {
    await loadFlaggedAnswers()
})

async function loadFlaggedAnswers() {
    loading.value = true
    error.value = null
    try {
        flaggedAnswers.value = await getFlaggedAnswers()
    } catch (err) {
        error.value = err.message || 'Не вдалося завантажити список позначених відповідей'
    } finally {
        loading.value = false
    }
}

function formatDate(dateString) {
    const date = new Date(dateString)
    return date.toLocaleDateString('uk-UA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    })
}

function selectAnswer(answer) {
    // Переходимо на сторінку перевірки спроби з цим питанням
    router.push(`/exam/${answer.attempt_id}/review`)
}

function toggleSelection(answer) {
    const index = selectedAnswers.value.findIndex(a => a.answer_id === answer.answer_id)
    if (index === -1) {
        if (selectedAnswers.value.length < 2) {
            selectedAnswers.value.push(answer)
        }
    } else {
        selectedAnswers.value.splice(index, 1)
    }
}

function isSelected(answerId) {
    return selectedAnswers.value.some(a => a.answer_id === answerId)
}

function clearSelection() {
    selectedAnswers.value = []
}

function goToComparison() {
    if (selectedAnswers.value.length === 2) {
        router.push(`/plagiarism-check/compare/${selectedAnswers.value[0].answer_id}/${selectedAnswers.value[1].answer_id}`)
    }
}
</script>

<style scoped>
.page-title {
    margin-bottom: 24px;
    font-size: 1.8rem;
}

.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--color-black-half-opacity);
}

.empty-state .hint {
    margin-top: 12px;
    font-size: 0.9rem;
}

.flagged-answers-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.flagged-answers-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.selection-info {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background-color: var(--color-gray);
    border-radius: 8px;
}

.compare-button {
    padding: 8px 16px;
    background-color: var(--color-purple);
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: bold;
}

.compare-button:hover {
    background-color: #6a006a;
}

.clear-button {
    padding: 8px 16px;
    background-color: transparent;
    color: var(--color-purple);
    border: 2px solid var(--color-purple);
    border-radius: 6px;
    cursor: pointer;
}

.clear-button:hover {
    background-color: var(--color-purple);
    color: white;
}

.flagged-answer-item {
    background: var(--color-gray);
    border: 2px solid var(--color-gray);
    border-radius: 12px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    gap: 16px;
}

.flagged-answer-item:hover {
    border-color: var(--color-purple);
    box-shadow: 0 2px 8px rgba(128, 0, 128, 0.1);
}

.flagged-answer-item.selected {
    border-color: var(--color-purple);
    background-color: rgba(128, 0, 128, 0.05);
}

.answer-checkbox {
    display: flex;
    align-items: flex-start;
    padding-top: 4px;
}

.answer-checkbox input[type="checkbox"] {
    width: 20px;
    height: 20px;
    cursor: pointer;
}

.answer-content {
    flex: 1;
}

.answer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.student-name {
    font-size: 1.2rem;
    font-weight: bold;
    margin: 0;
}

.exam-title {
    color: var(--color-black-half-opacity);
    font-size: 0.9rem;
}

.answer-preview {
    margin-bottom: 12px;
    color: var(--color-black-half-opacity);
    line-height: 1.5;
}

.answer-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: var(--color-black-half-opacity);
}

.flagged-date {
    font-style: italic;
}
</style>

