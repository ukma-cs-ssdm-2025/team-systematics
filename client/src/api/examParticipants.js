import { http } from './http.js'

/**
 * Отримує список активних учасників іспиту
 */
export async function getExamParticipants(examId) {
    try {
        const response = await http.get(`/api/exams/${examId}/participants`)
        return response.data
    } catch (error) {
        console.error(`API Error fetching exam participants for ${examId}:`, error)
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Не вдалося завантажити список учасників іспиту.')
    }
}

/**
 * Додає студента до іспиту
 * @param {string} examId - ID іспиту
 * @param {string} userId - ID студента
 * @param {string} courseId - ID курсу для перевірки зарахування
 */
export async function addExamParticipant(examId, userId, courseId) {
    try {
        const response = await http.post(`/api/exams/${examId}/participants`, {
            user_id: userId,
            course_id: courseId
        })
        return response.data
    } catch (error) {
        console.error(`API Error adding participant to exam ${examId}:`, error)
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Не вдалося додати студента до іспиту.')
    }
}

/**
 * Видаляє студента з іспиту
 * @param {string} examId - ID іспиту
 * @param {string} userId - ID студента
 */
export async function removeExamParticipant(examId, userId) {
    try {
        const response = await http.delete(`/api/exams/${examId}/participants/${userId}`)
        return response.data
    } catch (error) {
        console.error(`API Error removing participant from exam ${examId}:`, error)
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Не вдалося видалити студента з іспиту.')
    }
}

