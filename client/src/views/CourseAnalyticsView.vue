<template>
    <div>
        <Header />
        <main class="container">
            <Breadcrumbs />
            
            <div v-if="loading" class="status-message">Завантаження аналітики...</div>
            <div v-else-if="error" class="status-message error">{{ error }}</div>
            
            <div v-else class="analytics-content">
                <div class="page-header">
                    <h1>Аналітика курсу: {{ courseName }}</h1>
                </div>

                <!-- Загальна статистика групи -->
                <section class="analytics-section">
                    <h2>Загальна статистика групи</h2>
                    <div v-if="groupAnalytics" class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Всього студентів</div>
                            <div class="stat-value">{{ groupAnalytics.total_students }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Студентів завершило</div>
                            <div class="stat-value">{{ groupAnalytics.students_completed }}</div>
                        </div>
                        <div v-if="groupAnalytics.total_attempts && groupAnalytics.total_attempts > groupAnalytics.students_completed" class="stat-card">
                            <div class="stat-label">Всього спроб</div>
                            <div class="stat-value">{{ groupAnalytics.total_attempts }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Середній бал</div>
                            <div class="stat-value">{{ formatScore(groupAnalytics.average_score) }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Мінімальний бал</div>
                            <div class="stat-value">{{ formatScore(groupAnalytics.min_score) }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Максимальний бал</div>
                            <div class="stat-value">{{ formatScore(groupAnalytics.max_score) }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Медіана</div>
                            <div class="stat-value">{{ formatScore(groupAnalytics.median_score) }}</div>
                        </div>
                    </div>
                </section>

                <!-- Розподіл балів -->
                <section v-if="groupAnalytics?.scores && groupAnalytics.scores.length > 0" class="analytics-section">
                    <h2>Розподіл балів</h2>
                    <div v-if="groupAnalytics.total_attempts && groupAnalytics.total_attempts > groupAnalytics.students_completed" class="info-note">
                        <strong>Примітка:</strong> Гістограма відображає найкращу спробу кожного студента. 
                        Загальна кількість спроб: <strong>{{ groupAnalytics.total_attempts }}</strong> 
                        ({{ groupAnalytics.students_completed }} унікальних студентів).
                    </div>
                    <div class="chart-container">
                        <canvas ref="scoreDistributionChartRef"></canvas>
                    </div>
                </section>

                <!-- Статистика по іспитах -->
                <section v-if="courseAnalytics?.group_stats && courseAnalytics.group_stats.length > 0" class="analytics-section">
                    <h2>Статистика по іспитах</h2>
                    <div class="chart-container">
                        <canvas ref="examsComparisonChartRef"></canvas>
                    </div>
                    
                    <div class="exams-stats-table">
                        <table class="exams-table">
                            <thead>
                                <tr>
                                    <th class="left"><span class="pill">Назва іспиту</span></th>
                                    <th class="right"><span class="pill">Середній бал</span></th>
                                    <th class="right"><span class="pill">Мін. бал</span></th>
                                    <th class="right"><span class="pill">Макс. бал</span></th>
                                    <th class="right"><span class="pill">Медіана</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="exam in courseAnalytics.group_stats" :key="exam.exam_id">
                                    <td class="left">{{ exam.exam_name }}</td>
                                    <td class="right">{{ formatScore(exam.average_score) }}</td>
                                    <td class="right">{{ formatScore(exam.min_score) }}</td>
                                    <td class="right">{{ formatScore(exam.max_score) }}</td>
                                    <td class="right">{{ formatScore(exam.median_score) }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </section>

                <!-- Динаміка результатів -->
                <section v-if="availableExams.length > 0" class="analytics-section">
                    <h2>Динаміка результатів</h2>
                    <div class="exam-selector">
                        <label for="exam-select">Оберіть іспит:</label>
                        <select id="exam-select" v-model="selectedExamId" @change="loadExamProgress">
                            <option value="">Оберіть іспит...</option>
                            <option v-for="exam in availableExams" :key="exam.id" :value="exam.id">
                                {{ exam.title }}
                            </option>
                        </select>
                    </div>
                    <div v-if="examProgress.length > 0" class="chart-container">
                        <canvas ref="progressChartRef"></canvas>
                    </div>
                    <div v-else-if="selectedExamId" class="no-data-message">
                        Немає даних для відображення динаміки результатів
                    </div>
                </section>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { Chart, registerables } from 'chart.js'
import Header from '../components/global/Header.vue'
import Breadcrumbs from '../components/global/Breadcrumbs.vue'
import { getCourseAnalytics, getGroupAnalytics, getExamProgress } from '../api/analytics.js'
import { getCourseExams } from '../api/courses.js'

Chart.register(...registerables)

const route = useRoute()
const courseId = route.params.courseId
const courseName = ref('Курс')

const loading = ref(true)
const error = ref(null)

const groupAnalytics = ref(null)
const courseAnalytics = ref(null)
const examProgress = ref([])
const availableExams = ref([])
const selectedExamId = ref('')

// Chart refs
const scoreDistributionChartRef = ref(null)
const examsComparisonChartRef = ref(null)
const progressChartRef = ref(null)

// Chart instances
let scoreDistributionChart = null
let examsComparisonChart = null
let progressChart = null

onMounted(async () => {
    await loadAnalytics()
})

onBeforeUnmount(() => {
    destroyCharts()
})

async function loadAnalytics() {
    try {
        loading.value = true
        error.value = null

        // Завантажуємо дані паралельно
        const [groupData, courseData, examsData] = await Promise.all([
            getGroupAnalytics(courseId),
            getCourseAnalytics(courseId),
            getCourseExams(courseId)
        ])

        groupAnalytics.value = groupData
        courseAnalytics.value = courseData
        
        // getCourseExams повертає CourseExamsPage з полем exams
        if (examsData?.exams && examsData.exams.length > 0) {
            availableExams.value = examsData.exams
            // Автоматично завантажуємо прогрес для першого іспиту
            selectedExamId.value = examsData.exams[0].id
            // Завантажуємо прогрес асинхронно після рендерингу інших графіків
            setTimeout(async () => {
                await loadExamProgress()
            }, 300)
        }

        // Отримуємо назву курсу (якщо є в даних)
        if (examsData?.course_name) {
            courseName.value = examsData.course_name
        } else if (courseData?.course_name) {
            courseName.value = courseData.course_name
        }

        await nextTick()
        // Затримка для рендерингу графіків, щоб DOM був готовий
        setTimeout(() => {
            renderCharts()
        }, 200)
    } catch (err) {
        console.error('Error loading analytics:', err)
        error.value = err.message || 'Не вдалося завантажити аналітику'
    } finally {
        loading.value = false
    }
}

async function loadExamProgress() {
    if (!selectedExamId.value) {
        examProgress.value = []
        if (progressChart) {
            progressChart.destroy()
            progressChart = null
        }
        return
    }

    try {
        examProgress.value = []
        if (progressChart) {
            progressChart.destroy()
            progressChart = null
        }
        
        const progress = await getExamProgress(courseId, selectedExamId.value)
        examProgress.value = progress || []
        
        await nextTick()
        
        if (examProgress.value.length > 0) {
            setTimeout(() => {
                renderProgressChart()
            }, 200)
        }
    } catch (err) {
        console.error('Error loading exam progress:', err)
        examProgress.value = []
    }
}

function renderCharts() {
    destroyCharts()
    
    // Рендеримо графік розподілу балів, якщо є дані
    if (groupAnalytics.value?.scores && groupAnalytics.value.scores.length > 0) {
        setTimeout(() => renderScoreDistributionChart(), 100)
    }
    
    // Рендеримо графік порівняння іспитів
    if (courseAnalytics.value?.group_stats && courseAnalytics.value.group_stats.length > 0 && 
        courseAnalytics.value?.exam_statistics && courseAnalytics.value.exam_statistics.length > 0) {
        setTimeout(() => renderExamsComparisonChart(), 100)
    }
}

function renderScoreDistributionChart() {
    if (!scoreDistributionChartRef.value) return
    const canvas = scoreDistributionChartRef.value

    const scores = groupAnalytics.value.scores
    const bins = createBins(scores, 10) // 10 інтервалів

    scoreDistributionChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: bins.labels,
            datasets: [{
                label: 'Кількість студентів',
                data: bins.counts,
                backgroundColor: 'rgba(74, 144, 226, 0.7)', // синій колір
                borderColor: '#4A90E2', // синій колір
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Розподіл балів студентів'
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Діапазон балів'
                    }
                }
            }
        }
    })
}

function renderExamsComparisonChart() {
    if (!examsComparisonChartRef.value) return
    const canvas = examsComparisonChartRef.value

    const groupStats = courseAnalytics.value.group_stats
    if (!groupStats || groupStats.length === 0) return

    examsComparisonChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: groupStats.map(e => e.exam_name),
            datasets: [
                {
                    label: 'Середній бал',
                    data: groupStats.map(e => e.average_score || 0),
                    backgroundColor: 'rgba(74, 144, 226, 0.7)', // синій колір
                    borderColor: '#4A90E2', // синій колір
                    borderWidth: 1
                },
                {
                    label: 'Мінімальний бал',
                    data: groupStats.map(e => e.min_score || 0),
                    backgroundColor: 'rgba(255, 107, 109, 0.6)', // --color-red
                    borderColor: '#ff6b6d', // --color-red
                    borderWidth: 1
                },
                {
                    label: 'Максимальний бал',
                    data: groupStats.map(e => e.max_score || 0),
                    backgroundColor: 'rgba(159, 229, 167, 0.6)', // --color-green
                    borderColor: '#9FE5A7', // --color-green
                    borderWidth: 1
                },
                {
                    label: 'Медіана',
                    data: groupStats.map(e => e.median_score || 0),
                    backgroundColor: 'rgba(223, 122, 5, 0.6)', // --color-orange
                    borderColor: '#df7a05', // --color-orange
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Порівняння результатів по іспитах'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Бал'
                    }
                }
            }
        }
    })
}

function renderProgressChart() {
    if (!progressChartRef.value) {
        return
    }
    if (examProgress.value.length === 0) {
        return
    }
    
    const canvas = progressChartRef.value

    // Сортуємо за датою
    const sortedProgress = [...examProgress.value].sort((a, b) => 
        new Date(a.date) - new Date(b.date)
    )

    progressChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: sortedProgress.map(p => formatDate(p.date)),
            datasets: [{
                label: 'Середній бал',
                data: sortedProgress.map(p => p.average_score),
                borderColor: '#4A90E2', // синій колір
                backgroundColor: 'rgba(74, 144, 226, 0.15)', // синій колір з низькою прозорістю
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Динаміка середнього балу по часу'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Середній бал'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Дата'
                    }
                }
            }
        }
    })
}

function createBins(scores, numBins) {
    const min = Math.min(...scores)
    const max = Math.max(...scores)
    const binSize = (max - min) / numBins
    
    const bins = new Array(numBins).fill(0)
    const labels = []
    
    for (let i = 0; i < numBins; i++) {
        const binStart = min + i * binSize
        const binEnd = binStart + binSize
        labels.push(`${Math.round(binStart)}-${Math.round(binEnd)}`)
    }
    
    for (const score of scores) {
        const binIndex = Math.min(
            Math.floor((score - min) / binSize),
            numBins - 1
        )
        bins[binIndex]++
    }
    
    return { labels, counts: bins }
}

function formatScore(score) {
    if (score === null || score === undefined) return '—'
    return Math.round(score * 10) / 10
}

function formatDate(dateString) {
    const date = new Date(dateString)
    return date.toLocaleDateString('uk-UA', { 
        day: '2-digit', 
        month: '2-digit',
        year: 'numeric'
    })
}

function destroyCharts() {
    if (scoreDistributionChart) {
        scoreDistributionChart.destroy()
        scoreDistributionChart = null
    }
    if (examsComparisonChart) {
        examsComparisonChart.destroy()
        examsComparisonChart = null
    }
    if (progressChart) {
        progressChart.destroy()
        progressChart = null
    }
}
</script>

<style scoped>

.page-header {
    margin-bottom: 30px;
}

.page-header h1 {
    font-size: 2rem;
    color: var(--color-black, #333);
}

.analytics-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.analytics-section {
    background: var(--color-white, #eeeeee);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border: 1px solid var(--color-gray, #D9D9D9);
}

.analytics-section h2 {
    font-size: 1.5rem;
    margin-bottom: 20px;
    color: var(--color-black, #333);
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
}

.stat-card {
    background: var(--color-lavender, #e1c9e8);
    color: var(--color-black, #000000);
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    border: 1px solid var(--color-dark-lavender, #d1bbd8);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-label {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-bottom: 8px;
}

.stat-value {
    font-size: 2rem;
    font-weight: bold;
    color: var(--color-purple, #361c31);
}

.chart-container {
    position: relative;
    height: 400px;
    margin: 20px 0;
}

.exams-stats-table {
    margin-top: 30px;
    overflow-x: auto;
}

.exams-stats-table .exams-table {
    width: 100%;
    border-collapse: collapse;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    background-color: var(--color-white, #eeeeee);
    border-radius: 8px;
    overflow: hidden;
}

.exam-selector {
    margin-bottom: 20px;
}

.exam-selector label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
    color: var(--color-black, #333);
}

.exam-selector select {
    padding: 10px;
    border: 1px solid var(--color-gray, #D9D9D9);
    border-radius: 6px;
    font-size: 1rem;
    min-width: 300px;
    background: var(--color-white, #eeeeee);
    color: var(--color-black, #000000);
    cursor: pointer;
    transition: border-color 0.2s, outline 0.2s;
}

.exam-selector select:hover {
    border-color: var(--color-dark-lavender, #d1bbd8);
}

.exam-selector select:focus {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.no-data-message {
    text-align: center;
    padding: 40px;
    color: var(--color-dark-gray, #555);
    font-style: italic;
}

.status-message {
    text-align: center;
    padding: 40px;
    font-size: 1.2rem;
    color: var(--color-black, #333);
}

.status-message.error {
    color: var(--color-red, #ff6b6d);
}

.info-note {
    background-color: rgba(74, 144, 226, 0.1);
    border-left: 4px solid var(--color-blue, #4A90E2);
    padding: 12px 16px;
    margin-bottom: 20px;
    border-radius: 4px;
    color: var(--color-black, #333);
    font-size: 0.95rem;
    line-height: 1.5;
}

.info-note strong {
    color: var(--color-blue, #4A90E2);
}
</style>

