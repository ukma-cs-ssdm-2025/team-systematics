import { http } from './http.js'
import coursesMock from '../mocks/courses.json'
import courseExamsMock from '../mocks/courseExams.json'

// Тимчасово використовуємо заглушку
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

// Отримує список курсів, які викладає поточний користувач.
export async function getMyCourses() {
    if (USE_MOCK_DATA) {
        return coursesMock
    }
    try {
        const response = await http.get('/api/courses/me')
        return response.data
    } catch (error) {
        console.error('API Error fetching teacher courses:', error)
        throw new Error('Не вдалося завантажити список курсів викладача.')
    }
}

export async function getAllCourses() {
    if (USE_MOCK_DATA) {
        return coursesMock
    }
    try {
        const response = await http.get('/api/courses')
        return response.data
    } catch (error) {
        console.error('API Error fetching teacher courses:', error)
        throw new Error('Не вдалося завантажити список усіх курсів.')
    }
}

// Створює новий курс.
export async function createNewCourse(courseId) {
    if (USE_MOCK_DATA) {
        // ...
    }
    try {
        const response = await http.post(`/api/courses`)
        return response.data
    } catch (error) {
        console.error(`API Error fetching students for course ${courseId}:`, error)
        throw new Error('Не вдалося створити новий курс.')
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