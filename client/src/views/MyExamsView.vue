<template>
    <div>
        <Header />
        <main class="container" v-if="!loading">
            <!-- 1. Стан завантаження -->
            <div v-if="loading" class="status-message">
                Завантаження списку іспитів...
            </div>

            <!-- 2. Стан помилки -->
            <div v-else-if="error" class="status-message error">
                Помилка завантаження: {{ error }}
            </div>

            <!-- 3. Основний контент, коли дані завантажено -->
            <div v-else>
                <!-- Секція для майбутніх іспитів -->
                <section class="exams-section">
                    <h2>Майбутні іспити</h2>
                    <table v-if="futureExams.length" class="exams-table">
                        <thead>
                            <tr>
                                <th class="left"><span class="pill">Назва іспиту</span></th>
                                <th class="left"><span class="pill">Час початку</span></th>
                                <th class="left"><span class="pill">Час закінчення</span></th>
                                <th class="right"><span class="pill">К-сть спроб</span></th>
                                <th class="right"><span class="pill">Прохідний бал</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="exam in futureExams" :key="exam.id">
                                <td class="exam-title left" @click="openStartExamPopup(exam)">{{ exam.title }}</td>
                                <td class="left">{{ formatDateTime(exam.start_at) }}</td>
                                <td class="left">{{ formatDateTime(exam.end_at) }}</td>
                                <td class="right">{{ exam.max_attempts }}</td>
                                <td class="right">{{ exam.pass_threshold }}</td>
                            </tr>
                        </tbody>
                    </table>
                    <p v-else class="empty-list-message">Немає запланованих іспитів.</p>
                </section>

                <!-- Секція для виконаних іспитів -->
                <section class="exams-section">
                    <h2>Вже виконано</h2>
                    <table v-if="completedExams.length" class="exams-table">
                        <thead>
                            <tr>
                                <th class="left"><span class="pill">Назва іспиту</span></th>
                                <th class="left"><span class="pill">Час початку</span></th>
                                <th class="left"><span class="pill">Час закінчення</span></th>
                                <th class="right"><span class="pill">К-сть спроб</span></th>
                                <th class="right"><span class="pill">Прохідний бал</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="exam in completedExams" :key="exam.id">
                                <td class="exam-title left inactive">{{ exam.title }}</td>
                                <td class="left inactive">{{ formatDateTime(exam.start_at) }}</td>
                                <td class="left inactive">{{ formatDateTime(exam.end_at) }}</td>
                                <td class="right inactive">{{ exam.max_attempts }}</td>
                                <td class="right inactive">{{ exam.pass_threshold }}</td>
                            </tr>
                        </tbody>
                    </table>
                    <p v-else class="empty-list-message">Ще немає виконаних іспитів.</p>
                </section>

                <div class="page-end-deco">
                    <img src="../assets/icons/graduate-hat.svg" alt="Decorative image of a graduate hat">
                    <div class="page-end-text">Наразі це все!</div>
                </div>
            </div>
        </main>
        <div class="start-test-popup" v-if="isPopupVisible">
            <CPopup :visible="isPopupVisible" :header="popupHeader"
                disclaimer="Як тільки екзамен розпочнеться, його не можна буде зупинити." fstButton="Розпочати"
                sndButton="Скасувати" @fstAction="handleStartExam" @sndAction="closePopup" />
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import Header from '../components/global/Header.vue'
import CPopup from '../components/global/CPopup.vue'
import { getExams } from '../api/exams.js'

// Створюємо два окремих ref для кожного списку - майбутніх і виконаних іспитів
const futureExams = ref([])
const completedExams = ref([])

const loading = ref(true)
const error = ref(null)

// керуємо поп-апом з підтвердженням готовності почати іспит
const isPopupVisible = ref(false)
const selectedExam = ref(null)

const popupHeader = computed(() => {
    return selectedExam.value
        ? `Розпочати іспит: ${selectedExam.value.title}?`
        : ''
})

function openStartExamPopup(exam) {
    selectedExam.value = exam
    isPopupVisible.value = true
}

function closePopup() {
    selectedExam.value = null
    isPopupVisible.value = false
}

// async function handleStartExam {}

onMounted(async () => {
    try {
        const data = await getExams()
        futureExams.value = data.future
        completedExams.value = data.completed

    } catch (err) {
        error.value = err.message
    } finally {
        loading.value = false
    }
})

// браузер бере часовий пояс з налаштувань браузера користувача
function formatDateTime(dateString) {
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }
    return new Date(dateString).toLocaleString('uk-UA', options)
}
</script>

<style scoped>
.start-test-popup {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: var(--color-black-half-opacity);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.inactive {
    opacity: 0.5;
}

.page-end-deco {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.page-end-text {
    font-style: italic;
}

.exam-title {
    cursor: pointer;
}

.exam-title.inactive {
    cursor: default;
}
</style>