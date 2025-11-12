<template>
    <div>
        <Header />
        <main class="container">
            <section class="content-section">
                <div class="page-header">
                    <h2> {{ header }}</h2>
                    <CButton v-if="auth.isTeacher.value" @click="createNewCourse">+ Створити новий курс</CButton>
                </div>

                <!-- Фільтри -->
                <div class="filters-section">
                    <input
                        v-model="filters.name"
                        type="text"
                        placeholder="Назва або код курсу"
                        class="filter-input"
                        @input="applyFilters"
                    />
                    <input
                        v-if="auth.isStudent.value || auth.isSupervisor.value"
                        v-model="filters.teacher_name"
                        type="text"
                        placeholder="Викладач (ПІБ або email)"
                        class="filter-input"
                        @input="applyFilters"
                    />
                    <input
                        v-if="auth.isStudent.value"
                        v-model.number="filters.min_students"
                        type="number"
                        min="0"
                        step="1"
                        placeholder="Мін. студентів"
                        class="filter-input"
                        @input="applyFilters"
                    />
                    <input
                        v-if="auth.isStudent.value"
                        v-model.number="filters.max_students"
                        type="number"
                        min="0"
                        step="1"
                        placeholder="Макс. студентів"
                        class="filter-input"
                        @input="applyFilters"
                    />
                    <input
                        v-if="auth.isStudent.value"
                        v-model.number="filters.min_exams"
                        type="number"
                        min="0"
                        step="1"
                        placeholder="Мін. іспитів"
                        class="filter-input"
                        @input="applyFilters"
                    />
                    <input
                        v-if="auth.isStudent.value"
                        v-model.number="filters.max_exams"
                        type="number"
                        min="0"
                        step="1"
                        placeholder="Макс. іспитів"
                        class="filter-input"
                        @input="applyFilters"
                    />
                    <input
                        v-if="auth.isTeacher.value || auth.isSupervisor.value"
                        v-model.number="filters.min_students"
                        type="number"
                        min="0"
                        step="1"
                        placeholder="Мін. студентів"
                        class="filter-input"
                        @input="applyFilters"
                    />
                    <input
                        v-if="auth.isTeacher.value || auth.isSupervisor.value"
                        v-model.number="filters.max_students"
                        type="number"
                        min="0"
                        step="1"
                        placeholder="Макс. студентів"
                        class="filter-input"
                        @input="applyFilters"
                    />
                    <input
                        v-if="auth.isTeacher.value"
                        v-model.number="filters.min_exams"
                        type="number"
                        min="0"
                        step="1"
                        placeholder="Мін. іспитів"
                        class="filter-input"
                        @input="applyFilters"
                    />
                    <input
                        v-if="auth.isTeacher.value"
                        v-model.number="filters.max_exams"
                        type="number"
                        min="0"
                        step="1"
                        placeholder="Макс. іспитів"
                        class="filter-input"
                        @input="applyFilters"
                    />
                    <button 
                        v-if="hasActiveFilters"
                        @click="clearFilters"
                        class="clear-filters-btn"
                        title="Очистити фільтри"
                    >
                        <span class="clear-icon">×</span>
                    </button>
                </div>

                <div v-if="loading" class="status-message">Завантаження...</div>
                <div v-else-if="error" class="status-message error">{{ error }}</div>

                <div v-else-if="courses.length > 0" class="courses-grid">
                    <div v-for="course in displayCourses" :key="course.id" class="course-card">
                        <span class="course-code">{{ course.code }}</span>
                        <h3 class="course-name">{{ course.name }}</h3>
                        <div v-if="course.description" class="card-description">
                            <p>{{ course.description }}</p>
                        </div>
                        <div class="card-stats">
                            <span>👩‍🎓 {{ course.student_count || course.students_count || 0 }} студентів</span>
                            <span v-if="course.teachers && course.teachers.length > 0">
                                👨‍🏫 {{ course.teachers.length }} {{ course.teachers.length === 1 ? 'викладач' : 'викладачів' }}
                            </span>
                            <span v-if="!auth.isSupervisor.value">📝 {{ course.exam_count || 0 }} іспитів</span>
                        </div>
                        <div v-if="course.teachers && course.teachers.length > 0" class="card-teachers">
                            <span class="teachers-label">Викладачі:</span>
                            <span class="teachers-list">{{ course.teachers.join(', ') }}</span>
                        </div>
                        <div class="card-actions">
                            <CButton v-if="auth.isTeacher.value" @click="goToExams(course.id)">Керувати</CButton>
                            <CButton 
                                v-if="auth.isStudent.value" 
                                @click="handleEnroll(course)" 
                                :disabled="course.is_enrolled || isEnrolling[course.id]"
                            >
                                <span v-if="isEnrolling[course.id]">Запис...</span>
                                <span v-else-if="course.is_enrolled">✔ Ви записані</span>
                                <span v-else>Записатися</span>
                            </CButton>
                            <CButton v-if="auth.isSupervisor.value" @click.stop="viewCourseDetails(course.id)">Переглянути деталі</CButton>
                        </div>
                    </div>
                </div>

                <div v-else class="empty-state">
                    <h2 v-if="auth.isTeacher.value">У вас ще немає створених курсів</h2>
                    <h2 v-else>Курси не знайдено</h2>
                    <p v-if="(auth.isStudent.value || auth.isSupervisor.value) && hasActiveFilters">Спробуйте змінити фільтри пошуку</p>
                    <CButton v-if="auth.isTeacher.value" @click="createNewCourse">+ Створити свій перший курс</CButton>
                </div>
            </section>
        </main>

        <!-- Модальне вікно з деталями курсу (тільки для наглядача) -->
        <div v-if="auth.isSupervisor.value && selectedCourse" class="modal-overlay" @click="closeModal">
            <div class="modal-content" @click.stop>
                <div class="modal-header">
                    <h3>{{ selectedCourse.name }} ({{ selectedCourse.code }})</h3>
                    <button class="close-button" @click="closeModal">×</button>
                </div>
                <div class="modal-body">
                    <div v-if="selectedCourse.description" class="course-description">
                        <p>{{ selectedCourse.description }}</p>
                    </div>

                    <!-- Студенти -->
                    <div class="participants-section">
                        <h4>Студенти ({{ selectedCourse.students?.length || 0 }})</h4>
                        <div v-if="selectedCourse.students && selectedCourse.students.length > 0">
                            <table class="exams-table">
                                <colgroup>
                                    <col style="width: 40%">
                                    <col style="width: 40%">
                                    <col style="width: 20%">
                                </colgroup>
                                <thead>
                                    <tr>
                                        <th class="left"><span class="pill">ПІБ студента</span></th>
                                        <th class="left"><span class="pill">Email</span></th>
                                        <th class="left"><span class="pill">Статус</span></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="student in selectedCourse.students" :key="student.id">
                                        <td class="left">{{ student.full_name }}</td>
                                        <td class="left">{{ student.email }}</td>
                                        <td class="left">
                                            <span class="status-pill enrolled">{{ student.status }}</span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <p v-else class="empty-list-message">Немає зареєстрованих студентів</p>
                    </div>

                    <!-- Викладачі -->
                    <div class="participants-section">
                        <h4>Викладачі ({{ selectedCourse.teachers?.length || 0 }})</h4>
                        <div v-if="selectedCourse.teachers && selectedCourse.teachers.length > 0">
                            <table class="exams-table">
                                <colgroup>
                                    <col style="width: 50%">
                                    <col style="width: 50%">
                                </colgroup>
                                <thead>
                                    <tr>
                                        <th class="left"><span class="pill">ПІБ викладача</span></th>
                                        <th class="left"><span class="pill">Email</span></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="teacher in selectedCourse.teachers" :key="teacher.id">
                                        <td class="left">{{ teacher.full_name }}</td>
                                        <td class="left">{{ teacher.email }}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <p v-else class="empty-list-message">Немає зареєстрованих викладачів</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <CButton @click="closeModal">Закрити</CButton>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import { getMyCourses, getAllCourses, enrollInCourse, getCoursesForSupervisor, getCourseDetailsForSupervisor } from '../api/courses.js'
import { useAuth } from '../store/loginInfo.js'

const router = useRouter()
const courses = ref([])
const loading = ref(true)
const error = ref(null)
const isEnrolling = ref({})
const selectedCourse = ref(null)

const filters = ref({
    name: '',
    teacher_name: '',
    min_students: null,
    max_students: null,
    min_exams: null,
    max_exams: null,
})

const auth = useAuth()
const header = computed(() => {
    if (auth.isTeacher.value) return 'Мої курси'
    if (auth.isSupervisor.value) return 'Курси'
    return 'Каталог курсів'
})

const hasActiveFilters = computed(() => {
    return !!(
        filters.value.name?.trim() ||
        filters.value.teacher_name?.trim() ||
        (filters.value.min_students !== null && filters.value.min_students !== '') ||
        (filters.value.max_students !== null && filters.value.max_students !== '') ||
        (filters.value.min_exams !== null && filters.value.min_exams !== '') ||
        (filters.value.max_exams !== null && filters.value.max_exams !== '')
    )
})

const displayCourses = computed(() => {
    if (auth.isSupervisor.value) {
        // Для наглядача сортуємо курси
        const sorted = [...courses.value]
        sorted.sort((a, b) => {
            const aVal = String(a.name || '').toLowerCase()
            const bVal = String(b.name || '').toLowerCase()
            return aVal > bVal ? 1 : aVal < bVal ? -1 : 0
        })
        return sorted
    }
    return courses.value
})

onMounted(async () => {
    await loadCourses()
})

async function loadCourses() {
    loading.value = true
    error.value = null
    try {
        if (auth.isSupervisor.value) {
            const response = await getCoursesForSupervisor({
                ...filters.value,
                limit: 200,
                offset: 0
            })
            courses.value = response
        }
        else if (auth.isTeacher.value) {
            const response = await getMyCourses({
                ...filters.value,
                limit: 100,
                offset: 0
            })
            courses.value = response.items
        }
        else if (auth.isStudent.value) {
            const response = await getAllCourses({
                ...filters.value,
                limit: 100,
                offset: 0
            })
            courses.value = response.items
        }
    } catch (err) {
        error.value = err.message || 'Не вдалося завантажити список курсів.'
    } finally {
        loading.value = false
    }
}

function goToExams(courseId) {
    router.push(`/courses/${courseId}/exams`)
}

async function handleEnroll(course) {
    isEnrolling.value[course.id] = true
    try {
        await enrollInCourse(course.id)
        course.is_enrolled = true
    } catch (err) {
        alert(err.message || 'Не вдалося записатися на курс.')
    } finally {
        isEnrolling.value[course.id] = false
    }
}

function createNewCourse() {
    router.push('/courses/create')
}

function applyFilters() {
    // Дебаунс для оптимізації запитів
    clearTimeout(applyFilters.timeout)
    applyFilters.timeout = setTimeout(() => {
        loadCourses()
    }, 500)
}

function clearFilters() {
    filters.value = {
        name: '',
        teacher_name: '',
        min_students: null,
        max_students: null,
        min_exams: null,
        max_exams: null,
    }
    loadCourses()
}

async function viewCourseDetails(courseId) {
    if (!auth.isSupervisor.value) return
    
    loading.value = true
    try {
        const details = await getCourseDetailsForSupervisor(courseId)
        if (details && details.message) {
            selectedCourse.value = {
                id: courseId,
                name: courses.value.find(c => c.id === courseId)?.name || '',
                code: courses.value.find(c => c.id === courseId)?.code || '',
                students: [],
                teachers: [],
                message: details.message
            }
        } else {
            selectedCourse.value = details
        }
    } catch (err) {
        error.value = err.message || 'Не вдалося завантажити деталі курсу.'
    } finally {
        loading.value = false
    }
}

function closeModal() {
    selectedCourse.value = null
}
</script>

<style scoped>
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
}

.filters-section {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    flex-wrap: wrap;
    align-items: center;
}

.clear-filters-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.2s ease;
}

.clear-filters-btn:hover {
    transform: scale(1.1);
}

.clear-icon {
    color: var(--color-red);
    font-size: 24px;
    font-weight: bold;
    line-height: 1;
    display: inline-block;
}

.filter-input {
    flex: 1;
    min-width: 200px;
    padding: 8px 12px;
    border: 1px solid var(--color-gray);
    border-radius: 4px;
    font-size: 1rem;
    font-family: inherit;
    background-color: white;
    color: inherit;
    box-sizing: border-box;
    transition: border-color 0.2s ease;
}

.filter-input:focus {
    outline: none;
    border-color: var(--color-violet, #6b46c1);
}

.filter-input::placeholder {
    color: var(--color-dark-gray, #666);
    opacity: 0.7;
}

.filter-input[type="text"] {
    appearance: none;
    -webkit-appearance: none;
}

/* Для числових полів залишаємо стандартні стрілочки */
.filter-input[type="number"]::-webkit-inner-spin-button,
.filter-input[type="number"]::-webkit-outer-spin-button {
    opacity: 1;
    height: 20px;
    cursor: pointer;
}

.courses-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 36px;
}

.course-card {
    background-color: #f9f9f9;
    border: 1px solid var(--color-gray);
    border-radius: 12px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.course-code {
    color: var(--color-dark-gray);
    display: block;
}

.course-name {
    margin: 0;
}

.card-description {
    color: var(--color-dark-gray);
    font-size: 0.9rem;
    line-height: 1.5;
}

.card-description p {
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
}

.card-stats {
    display: flex;
    gap: 24px;
    color: var(--color-dark-gray);
}

.card-actions {
    display: flex;
    justify-content: space-between;
    gap: 12px;
}

.empty-state {
    text-align: center;
    padding: 80px;
}

.card-teachers {
    display: flex;
    flex-direction: column;
    gap: 8px;
    color: var(--color-dark-gray);
    font-size: 0.9rem;
}

.teachers-label {
    font-weight: bold;
}

.teachers-list {
    color: var(--color-dark-gray);
}

.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background-color: white;
    border-radius: 12px;
    max-width: 900px;
    max-height: 90vh;
    width: 90%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid var(--color-gray);
    background-color: var(--color-violet);
    color: white;
}

.modal-header h3 {
    margin: 0;
    font-size: 1.5rem;
}

.close-button {
    background: none;
    border: none;
    color: white;
    font-size: 2rem;
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    line-height: 1;
}

.close-button:hover {
    background-color: rgba(255, 255, 255, 0.2);
}

.modal-body {
    padding: 24px;
    overflow-y: auto;
    flex: 1;
}

.course-description {
    margin-bottom: 24px;
    color: var(--color-dark-gray);
    line-height: 1.6;
}

.participants-section {
    margin-bottom: 32px;
}

.participants-section:last-child {
    margin-bottom: 0;
}

.participants-section h4 {
    margin-bottom: 16px;
    font-size: 1.2rem;
}

.exams-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 16px;
}

.exams-table thead {
    background-color: var(--color-violet);
    color: white;
}

.exams-table th {
    padding: 12px 16px;
    text-align: left;
    font-weight: bold;
}

.exams-table th.left {
    text-align: left;
}

.exams-table th.right {
    text-align: right;
}

.exams-table td {
    padding: 12px 16px;
    border-bottom: 1px solid var(--color-gray);
}

.exams-table tbody tr:hover {
    background-color: #f5f5f5;
}

.pill {
    display: inline-block;
    padding: 4px 8px;
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}

.status-pill {
    padding: 4px 12px;
    border-radius: 12px;
    white-space: nowrap;
    display: inline-block;
}

.status-pill.enrolled {
    background-color: var(--color-green-half-opacity);
}

.empty-list-message {
    text-align: center;
    padding: 24px;
    color: var(--color-dark-gray);
    font-style: italic;
}

.modal-footer {
    padding: 16px 24px;
    border-top: 1px solid var(--color-gray);
    display: flex;
    justify-content: flex-end;
}
</style>