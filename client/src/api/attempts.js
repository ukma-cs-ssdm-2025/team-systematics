import { http } from '../api/http.js'
import mockAttemptData from '../mocks/examAttempts.json'

// Тимчасово використовуємо заглушку
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'
const MOCK_ID_ATTEMPT = "04c1572b-01f8-4dd0-9f92-ad6add80b2e0"

export async function startExamAttempt(examId) {
    if (USE_MOCK_DATA) {
        return { attempt_id: MOCK_ID_ATTEMPT }
    }

    try {
        const response = await http.post(`/api/exams/${examId}/attempts`)
        return response.data
    } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Не вдалося розпочати іспит. Спробуйте ще раз.')
    }
}

/* Завантажуємо деталі спроби іспиту за її ID
Бекенд збирає всі необхідні дані (назву, статус, питання, варіанти відповідей тощо)
Сервер не повертає правильні відповіді, щоб користувач не міг їх побачити в коді відповіді */
export async function getExamAttemptDetails(attemptId) {
    if (USE_MOCK_DATA) {
        return mockAttemptData
    }

    try {
        const response = await http.get(`/api/attempts/${attemptId}`)
        return response.data
    } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Не вдалося завантажити дані іспиту. Спробуйте ще раз.')
    }
}

// Зберігаємо відповідь користувача на сервері
export async function saveAnswer(attemptId, questionId, answer) {
    if (USE_MOCK_DATA) {
        console.log(`MOCK: Збереження відповіді для attemptId=${attemptId}, questionId=${questionId}`, answer)
        return
    }

    try {
        const url = `/api/exam-attempts/${attemptId}/answers`

        // Формуємо тіло запиту, яке буде надіслано на сервер
        const payload = {
            question_id: questionId,
            answer: answer
        }

        const response = await http.post(url, payload)
        return response.data;

   } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Не вдалося зберегти відповідь. Спробуйте ще раз.')
    }
}