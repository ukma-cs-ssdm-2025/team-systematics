<template>
    <div>
        <Header />
        <main class="container">
            <div v-if="loading" class="status-message">Завантаження журналу...</div>
            <div v-else-if="error" class="status-message error">{{ error }}</div>

            <div v-else>
                <section class="exams-section">
                    <h2>Журнал іспиту {{ examName }}</h2>

                    <table v-if="students.length" class="exams-table">
                        <colgroup>
                            <col style="width: 5%">
                            <col style="width: 40%">
                            <col style="width: 20%">
                            <col style="width: 20%">
                            <col style="width: 15%">
                        </colgroup>

                        <thead>
                            <tr>
                                <th class="toggle-column"></th>
                                <th class="left"><span class="pill">ПІБ студента</span></th>
                                <th class="left"><span class="pill">Статус</span></th>
                                <th class="right"><span class="pill">Макс. оцінка</span></th>
                                <th class="right"><span class="pill">К-сть спроб</span></th>
                            </tr>
                        </thead>

                        <tbody>
                            <template v-for="student in students" :key="student.id">
                                <tr class="main-row" :class="{ 'is-expandable': student.attempts.length > 0 }"
                                    @click="toggleDetails(student)">
                                    <td class="toggle-column">
                                        <button class="toggle-button" v-if="student.attempts.length > 0"
                                            :class="{ 'is-open': isExpanded(student.id) }"
                                            aria-label="Розгорнути деталі">
                                            ▶
                                        </button>
                                    </td>
                                    <td class="left">{{ student.full_name }}</td>
                                    <td class="left">
                                        <span :class="['status-pill', getStatusClass(student.overall_status)]">
                                            {{ statusLabel(student.overall_status) }}
                                        </span>
                                    </td>
                                    <td class="right">{{ formatGrade(student.max_grade) }}</td>
                                    <td class="right">{{ student.attempts_count }} / {{ maxAttempts }}</td>
                                </tr>

                                <transition name="fade">
                                    <tr v-if="isExpanded(student.id)" class="details-row">
                                        <td></td>
                                        <td colspan="4">
                                            <div class="details-content">
                                                <table class="attempts-table">
                                                    <colgroup>
                                                        <col style="width: 40%">
                                                        <col style="width: 20%">
                                                        <col style="width: 20%">
                                                        <col style="width: 15%">
                                                    </colgroup>
                                                    <thead class="visually-hidden">
                                                        <tr>
                                                            <th>Номер спроби</th>
                                                            <th>Статус спроби</th>
                                                            <th>Оцінка за спробу</th>
                                                            <th>Витрачений час</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        <tr v-for="attempt in student.attempts" :key="attempt.id"
                                                            class="attempt-row" @click="reviewAttempt(attempt.id)">
                                                            <td class="left">{{ `Спроба №${attempt.attempt_number}` }}
                                                            </td>
                                                            <td class="left">
                                                                <span
                                                                    :class="['status-pill', getStatusClass(attempt.status)]">
                                                                    {{ statusLabel(attempt.status) }}
                                                                </span>
                                                            </td>
                                                            <td class="right">{{
                                                                formatEarnedPoints(attempt.earned_points) }} / 100
                                                            </td>
                                                            <td class="right">{{ attempt.time_spent_minutes }} хв</td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </div>
                                        </td>
                                    </tr>
                                </transition>
                            </template>
                        </tbody>
                    </table>

                    <p v-else class="empty-list-message">Ще жоден студент не складав цей іспит.</p>
                </section>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import { getExamJournal } from '../api/exams.js'

const router = useRouter()
const examId = useRoute().params.examId
const students = ref([])
const examName = ref('')
const maxAttempts = ref(0)
const loading = ref(true)
const error = ref(null)
const expandedStudentId = ref(null)

function isExpanded(studentId) {
    return expandedStudentId.value === studentId
}

function toggleDetails(student) {
    if (!student.attempts || student.attempts.length === 0) {
        return
    }
    expandedStudentId.value = isExpanded(student.id) ? null : student.id
}

function reviewAttempt(attemptId) {
    router.push(`/exams-results/${attemptId}`)
}

function formatGrade(grade) {
    if (grade === null || grade === undefined) {
        return '–'
    }
    return `${Math.ceil(grade)} / 100`
}

function formatEarnedPoints(earned_points) {
    if (typeof earned_points === 'number') {
        return Math.ceil(earned_points)
    }
    return '--'
}

function getStatusClass(status) {
    switch (status) {
        case 'not_started':
            return 'not-started'
        case 'submitted':
            return 'pending'
        case 'completed':
            return 'evaluated'
        default:
            return 'not-started'
    }
}

function statusLabel(status) {
    if (!status) return 'Не розпочато'

    switch (status) {
        case 'not_started':
            return 'Не розпочато'
        case 'submitted':
            return 'Потребує перевірки'
        case 'completed':
            return 'Оцінено'
        default:
            return 'Не розпочато'
    }
}

onMounted(async () => {
    try {
        const response = await getExamJournal(examId)
        students.value = response.students
        examName.value = response.exam_name
        document.title = `Журнал іспиту ${examName.value} | Systematics`
        maxAttempts.value = response.max_attempts
    } catch (err) {
        error.value = err.message || 'Сталася невідома помилка.'
    } finally {
        loading.value = false
    }
})
</script>

<style scoped>
.toggle-column {
    width: 40px;
    text-align: center;
}

.toggle-button {
    background: none;
    border: none;
    cursor: default;
    font-size: 0.8rem;
    color: var(--color-dark-gray);
    transition: transform 0.2s ease;
}

.toggle-button.is-open {
    transform: rotate(90deg);
}

.main-row.is-expandable,
.toggle-button>.main-row.is-expandable {
    cursor: pointer;
}

.details-row>td {
    padding: 0;
    border: none;
}

.details-content {
    border-left: 3px solid var(--color-gray);
    margin: 20px 0;
}

.details-content tbody tr {
    border-bottom: none;
}

.details-content tbody tr td:first-child {
    border-bottom: none;
    padding-left: 16px;
}


.attempt-row {
    cursor: pointer;
}

.status-pill {
    padding: 4px 12px;
    border-radius: 12px;
    white-space: nowrap;
}

.status-pill.evaluated {
    background-color: var(--color-green-half-opacity);
}

.status-pill.pending {
    background-color: var(--color-red-half-opacity);
}

.status-pill.not-started {
    background-color: var(--color-gray);
}

.fade-enter-active {
    transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

.visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
}
</style>
