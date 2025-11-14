import { http } from './http.js'
import coursesMock from '../mocks/courses.json'
import courseExamsMock from '../mocks/courseExams.json'

// Тимчасово використовуємо заглушку
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

/**
 * Допоміжна функція для побудови параметрів запиту з фільтрів
 */
function buildQueryParams(filters) {
    const params = new URLSearchParams()
    
    if (filters.name && filters.name.trim()) {
        params.append('name', filters.name.trim())
    }
    if (filters.teacher_name && filters.teacher_name.trim()) {
        params.append('teacher_name', filters.teacher_name.trim())
    }
    
    // Фільтри для кількості студентів
    if (filters.min_students !== undefined && filters.min_students !== null && filters.min_students !== '') {
        params.append('min_students', filters.min_students)
    }
    if (filters.max_students !== undefined && filters.max_students !== null && filters.max_students !== '') {
        params.append('max_students', filters.max_students)
    }
    
    // Фільтри для кількості іспитів
    if (filters.min_exams !== undefined && filters.min_exams !== null && filters.min_exams !== '') {
        params.append('min_exams', filters.min_exams)
    }
    if (filters.max_exams !== undefined && filters.max_exams !== null && filters.max_exams !== '') {
        params.append('max_exams', filters.max_exams)
    }
    
    // Пагінація
    if (filters.limit) params.append('limit', filters.limit)
    if (filters.offset) params.append('offset', filters.offset)
    
    return params
}

/**
 * Допоміжна функція для виконання GET запиту з обробкою помилок
 */
async function fetchCoursesWithErrorHandling(url, errorMessage) {
    try {
        const response = await http.get(url)
        return response.data
    } catch (error) {
        console.error(`API Error: ${errorMessage}`, error)
        throw new Error(errorMessage)
    }
}

// Отримує список курсів, які викладає поточний користувач.
export async function getMyCourses(filters = {}) {
    if (USE_MOCK_DATA) {
        return coursesMock
    }
    const params = buildQueryParams(filters)
    const queryString = params.toString()
    const url = queryString ? `/api/courses/me?${queryString}` : '/api/courses/me'
    return fetchCoursesWithErrorHandling(url, 'Не вдалося завантажити список курсів викладача.')
}

export async function getAllCourses(filters = {}) {
    if (USE_MOCK_DATA) {
        return coursesMock
    }
    const params = buildQueryParams(filters)
    const queryString = params.toString()
    const url = queryString ? `/api/courses?${queryString}` : '/api/courses'
    return fetchCoursesWithErrorHandling(url, 'Не вдалося завантажити список усіх курсів.')
}

// Створює новий курс.
export async function createNewCourse(payload) {
    if (USE_MOCK_DATA) {
        // ...
    }
    try {
        const response = await http.post('/api/courses', payload)
        return response.data
    } catch (error) {
        console.error(`API Error fetching students for course:`, error)
        throw error
    }
}

// Отримує список іспитів для конкретного курсу.
export async function getCourseExams(courseId) {
    if (USE_MOCK_DATA) {
        return courseExamsMock
    }
    try {
        const response = await http.get(`/api/courses/${courseId}/exams`)
        return response.data
    } catch (error) {
        console.error(`API Error fetching exams for course ${courseId}:`, error)
        throw new Error('Не вдалося завантажити список іспитів.')
    }
}

// Записати студента на конкретний курс.
export async function enrollInCourse(courseId) {
    if (USE_MOCK_DATA) {
        return courseExamsMock
    }
    try {
        const response = await http.post(`/api/courses/${courseId}/enroll`)
        return response.data
    } catch (error) {
        console.error(`API Error enrolling student in course ${courseId}:`, error)
        throw new Error('Не вдалося записати студента на курс.')
    }
}

// Виписати студента з конкретного курсу.
export async function unenrollFromCourse(courseId) {
    if (USE_MOCK_DATA) {
        return {}
    }
    try {
        const response = await http.delete(`/api/courses/${courseId}/enroll`)
        return response.data
    } catch (error) {
        console.error(`API Error unenrolling student from course ${courseId}:`, error)
        throw new Error('Не вдалося виписати студента з курсу.')
    }
}

// Отримує список курсів для наглядача з фільтрами
export async function getCoursesForSupervisor(filters = {}) {
    if (USE_MOCK_DATA) {
        return []
    }
    const params = buildQueryParams(filters)
    const queryString = params.toString()
    const url = queryString ? `/api/courses/supervisor?${queryString}` : '/api/courses/supervisor'
    return fetchCoursesWithErrorHandling(url, 'Не вдалося завантажити список курсів.')
}

// Отримує детальну інформацію про курс для наглядача
export async function getCourseDetailsForSupervisor(courseId) {
    if (USE_MOCK_DATA) {
        return null
    }
    try {
        const response = await http.get(`/api/courses/supervisor/${courseId}`)
        return response.data
    } catch (error) {
        console.error(`API Error fetching course details for supervisor ${courseId}:`, error)
        throw new Error('Не вдалося завантажити деталі курсу.')
    }
}