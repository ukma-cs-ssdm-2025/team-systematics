<template>
    <div>
        <Header />
        <main class="container">
            <div v-if="loading" class="status-message">Завантаження...</div>
            <div v-else-if="error" class="status-message error">{{ error }}</div>
            
            <div v-else-if="comparisonData" class="comparison-container">
                <div class="comparison-header">
                    <h2 class="page-title">Порівняння робіт на плагіат</h2>
                    <div class="exam-info">{{ comparisonData.exam_title }}</div>
                </div>
                
                <div class="comparison-content">
                    <div class="answer-panel left">
                        <div class="answer-header">
                            <h3>{{ comparisonData.student1_name }}</h3>
                        </div>
                        <textarea 
                            class="answer-textarea"
                            :value="comparisonData.answer1_text"
                            readonly
                        ></textarea>
                    </div>
                    
                    <div class="comparison-controls">
                        <button 
                            class="compare-button"
                            @click="runComparison"
                            :disabled="isComparing"
                        >
                            {{ isComparing ? 'Перевірка...' : 'Перевірити на плагіат' }}
                        </button>
                        
                        <div v-if="comparisonResult" class="comparison-result">
                            <div class="similarity-score">
                                Схожість: {{ (comparisonResult.similarity_score * 100).toFixed(1) }}%
                            </div>
                            <div 
                                class="similarity-status"
                                :class="getSimilarityClass(comparisonResult.similarity_score)"
                            >
                                {{ getSimilarityStatus(comparisonResult.similarity_score) }}
                            </div>
                        </div>
                    </div>
                    
                    <div class="answer-panel right">
                        <div class="answer-header">
                            <h3>{{ comparisonData.student2_name }}</h3>
                        </div>
                        <textarea 
                            class="answer-textarea"
                            :value="comparisonData.answer2_text"
                            readonly
                        ></textarea>
                    </div>
                </div>
                
                <div class="comparison-actions">
                    <button class="back-button" @click="goBack">Назад до списку</button>
                </div>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import { compareAnswers, getFlaggedAnswers } from '../api/attempts.js'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref(null)
const comparisonData = ref(null)
const comparisonResult = ref(null)
const isComparing = ref(false)

const answer1Id = route.params.answer1Id
const answer2Id = route.params.answer2Id

onMounted(async () => {
    await loadComparisonData()
})

async function loadComparisonData() {
    loading.value = true
    error.value = null
    
    try {
        // Отримуємо дані про обидві відповіді зі списку позначених
        const flaggedAnswers = await getFlaggedAnswers()
        const answer1 = flaggedAnswers.find(a => a.answer_id === answer1Id)
        const answer2 = flaggedAnswers.find(a => a.answer_id === answer2Id)
        
        if (!answer1 || !answer2) {
            error.value = 'Не вдалося знайти одну або обидві відповіді'
            return
        }
        
        comparisonData.value = {
            answer1_id: answer1.answer_id,
            answer2_id: answer2.answer_id,
            answer1_text: answer1.answer_text,
            answer2_text: answer2.answer_text,
            student1_name: answer1.student_name,
            student2_name: answer2.student_name,
            exam_title: answer1.exam_title
        }
    } catch (err) {
        error.value = err.message || 'Не вдалося завантажити дані для порівняння'
    } finally {
        loading.value = false
    }
}

async function runComparison() {
    if (!comparisonData.value) return
    
    isComparing.value = true
    try {
        comparisonResult.value = await compareAnswers(
            comparisonData.value.answer1_id,
            comparisonData.value.answer2_id
        )
    } catch (err) {
        alert(err.message || 'Не вдалося виконати перевірку на плагіат')
    } finally {
        isComparing.value = false
    }
}

function getSimilarityClass(score) {
    if (score >= 0.9) return 'high-risk'
    if (score >= 0.7) return 'suspicious'
    return 'ok'
}

function getSimilarityStatus(score) {
    if (score >= 0.9) return 'Високий ризик плагіату'
    if (score >= 0.7) return 'Підозріла схожість'
    return 'Нормальна схожість'
}

function goBack() {
    router.push('/plagiarism-check')
}
</script>

<style scoped>
.page-title {
    margin-bottom: 12px;
    font-size: 1.8rem;
}

.comparison-header {
    margin-bottom: 24px;
}

.exam-info {
    color: var(--color-black-half-opacity);
    font-size: 0.9rem;
}

.comparison-container {
    max-width: 1400px;
    margin: 0 auto;
}

.comparison-content {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 24px;
    margin-bottom: 24px;
}

.answer-panel {
    display: flex;
    flex-direction: column;
}

.answer-header {
    margin-bottom: 12px;
}

.answer-header h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: bold;
}

.answer-textarea {
    width: 100%;
    height: 500px;
    padding: 16px;
    background-color: var(--color-gray);
    border: 3px solid var(--color-gray);
    border-radius: 12px;
    font-family: inherit;
    font-size: inherit;
    resize: none;
    line-height: 1.6;
}

.answer-textarea:focus {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.comparison-controls {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    gap: 16px;
    padding-top: 60px;
}

.compare-button {
    padding: 12px 24px;
    background-color: var(--color-purple);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.2s;
}

.compare-button:hover:not(:disabled) {
    background-color: #6a006a;
}

.compare-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.comparison-result {
    text-align: center;
    padding: 16px;
    background-color: var(--color-gray);
    border-radius: 8px;
    min-width: 200px;
}

.similarity-score {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 8px;
}

.similarity-status {
    font-size: 0.9rem;
    padding: 4px 8px;
    border-radius: 4px;
}

.similarity-status.high-risk {
    background-color: #ffebee;
    color: #c62828;
}

.similarity-status.suspicious {
    background-color: #fff3e0;
    color: #e65100;
}

.similarity-status.ok {
    background-color: #e8f5e9;
    color: #2e7d32;
}

.comparison-actions {
    display: flex;
    justify-content: center;
    margin-top: 24px;
}

.back-button {
    padding: 10px 20px;
    background-color: transparent;
    color: var(--color-purple);
    border: 2px solid var(--color-purple);
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s;
}

.back-button:hover {
    background-color: var(--color-purple);
    color: white;
}

@media (max-width: 1200px) {
    .comparison-content {
        grid-template-columns: 1fr;
        gap: 16px;
    }
    
    .comparison-controls {
        padding-top: 0;
        order: 2;
    }
    
    .answer-panel.left {
        order: 1;
    }
    
    .answer-panel.right {
        order: 3;
    }
}
</style>

