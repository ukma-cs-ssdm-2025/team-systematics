<template>
    <div>
        <Header />
        <main class="container">
            <!-- 1. Стан завантаження -->
            <div v-if="loading" class="status-message">
                Завантаження атестату...
            </div>

            <!-- 2. Стан помилки -->
            <div v-else-if="error" class="status-message error">
                Помилка завантаження: {{ error }}
            </div>

            <!-- 3. Основний контент, коли дані завантажено -->
            <div v-else-if="transcriptData">
                <div class="student-info-header">
                    <h2>Атестат студента</h2>
                    <p class="student-info">
                        {{ fullName }} | {{ major }}
                    </p>
                </div>

                <section class="transcript-table">
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th class="left"><span class="pill" @click="sortBy('course_name')">Назва
                                        дисципліни</span></th>
                                <th class="right"><span class="pill" @click="sortBy('rating')">Рейтинг</span></th>
                                <th class="left"><span class="pill" @click="sortBy('ects_grade')">Оцінка ECTS</span>
                                </th>
                                <th class="left"><span class="pill" @click="sortBy('national_grade')">Національна
                                        шкала</span></th>
                                <th class="left"><span class="pill" @click="sortBy('pass_status')">Поріг виконано</span>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="course in transcriptData.courses" :key="course.id">
                                <td class="left">{{ course.course_name }}</td>
                                <td class="right">{{ course.rating !== null && course.rating !== undefined ?
                                    course.rating : '--' }}</td>
                                <td class="left">{{ course.ects_grade || '--' }}</td>
                                <td class="left">{{ course.national_grade || '--' }}</td>
                                <td class="left">{{ course.pass_status || '--' }}</td>
                            </tr>
                        </tbody>
                    </table>
                </section>

                <section>
                    <h2>Статистика</h2>
                    <ul class="statistics-list">
                        <li>Складено іспитів: {{ transcriptData.statistics.completed_courses }} / {{
                            transcriptData.statistics.total_courses }}</li>
                        <li>З них складено на A: {{ transcriptData.statistics.a_grades_count }}</li>
                        <li>Середньозважений рейтинг: {{ transcriptData.statistics.average_rating }}</li>
                    </ul>
                </section>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import Header from '../components/global/Header.vue'
import { useAuth } from '../store/loginInfo.js'
import { getTranscript } from '../api/transcript.js'

const transcriptData = ref(null)
const loading = ref(true)
const error = ref(null)

const { fullName, major } = useAuth()

const sortState = reactive({
    key: null, // Поле, за яким сортуємо
    order: 'asc' // Напрямок сортування
})

async function fetchTranscriptData() {
    loading.value = true
    try {
        const data = await getTranscript(sortState.key, sortState.order)
        transcriptData.value = data
    } catch (err) {
        error.value = err.message || "Не вдалося завантажити дані."
    } finally {
        loading.value = false
    }
}

function sortBy(key) {
    // Якщо клікнули на ту саму колонку, змінюємо напрямок
    if (sortState.key === key) {
        sortState.order = sortState.order === 'asc' ? 'desc' : 'asc'
    } else {
        // Якщо клікнули на нову колонку, встановлюємо її і скидаємо напрямок
        sortState.key = key
        sortState.order = 'asc'
    }
    fetchTranscriptData()
}

onMounted(fetchTranscriptData)

</script>