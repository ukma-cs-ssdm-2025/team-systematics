import { http } from './http.js'

/**
 * Отримує аналітику курсу: статистика по іспитах
 */
export async function getCourseAnalytics(courseId) {
    try {
        const response = await http.get(`/api/courses/${courseId}/analytics`)
        return response.data
    } catch (error) {
        console.error(`API Error fetching course analytics for ${courseId}:`, error)
        throw new Error('Не вдалося завантажити аналітику курсу.')
    }
}

/**
 * Отримує аналітику групи: середній/мін/макс/медіана оцінок
 */
export async function getGroupAnalytics(courseId) {
    try {
        const response = await http.get(`/api/courses/${courseId}/group-analytics`)
        return response.data
    } catch (error) {
        console.error(`API Error fetching group analytics for ${courseId}:`, error)
        throw new Error('Не вдалося завантажити аналітику групи.')
    }
}

/**
 * Отримує динаміку результатів по іспиту
 */
export async function getExamProgress(courseId, examId) {
    try {
        const response = await http.get(`/api/exams/${courseId}/exams/${examId}/progress`)
        return response.data
    } catch (error) {
        console.error(`API Error fetching exam progress for ${examId}:`, error)
        throw new Error('Не вдалося завантажити динаміку результатів.')
    }
}

/**
 * Отримує статистику по іспиту
 */
export async function getExamStatistics(courseId, examId) {
    try {
        const response = await http.get(`/api/exams/${courseId}/exams/${examId}/statistics`)
        return response.data
    } catch (error) {
        console.error(`API Error fetching exam statistics for ${examId}:`, error)
        throw new Error('Не вдалося завантажити статистику іспиту.')
    }
}

