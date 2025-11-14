<template>
    <div>
        <Header />
        <main class="container">
            <Breadcrumbs />
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
                        <CTextarea 
                            :model-value="comparisonData.answer1_text"
                            :disabled="true"
                        />
                    </div>
                    
                    <div class="comparison-controls">
                        <CButton 
                            @click="runComparison"
                            :disabled="isComparing"
                        >
                            {{ isComparing ? 'Перевірка...' : 'Перевірити на плагіат' }}
                        </CButton>
                        
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
                        <CTextarea 
                            :model-value="comparisonData.answer2_text"
                            :disabled="true"
                        />
                    </div>
                </div>
                
                <div class="comparison-actions">
                </div>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Header from '../components/global/Header.vue'
import Breadcrumbs from '../components/global/Breadcrumbs.vue'
import CTextarea from '../components/global/CTextarea.vue'
import CButton from '../components/global/CButton.vue'
import { compareAnswers, getFlaggedAnswers } from '../api/attempts.js'

const route = useRoute()

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

.comparison-content {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 100px;
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

.answer-panel :deep(.custom-textarea) {
    height: 500px;
}

.comparison-controls {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    gap: 16px;
    padding-top: 60px;
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

