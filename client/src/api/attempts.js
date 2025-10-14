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
        const startTimeKey = `exam_startTime_${attemptId}`
        let savedStartedAt = localStorage.getItem(startTimeKey)

        if (!savedStartedAt) {
            console.log("MOCK: Не знайдено збережений час початку. Генеруємо новий.")
            savedStartedAt = new Date().toISOString()
            localStorage.setItem(startTimeKey, savedStartedAt)
        } else {
            console.log("MOCK: Знайдено збережений час початку:", savedStartedAt)
        }

        return {
            ...mockAttemptData,
            started_at: savedStartedAt
        }
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

// Зберігаємо спробу іспиту як завершену
export async function submitExamAttempt(attemptId) {
    if (USE_MOCK_DATA) {
        console.log(`MOCK: Завершення (submit) спроби ${attemptId}`)
        return { // Приклад
            id: attemptId,
            exam_id: "e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b", 
            user_id: "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            status: "completed",
            score_percent: 88,
            started_at: "2025-10-13T19:25:55.930Z",
            submitted_at: new Date().toISOString(), 
            due_at: "2025-12-22T18:00:00+02:00"
        }
    }

    try {
        const url = `/api/attempts/${attemptId}/submit`
        const response = await http.post(url, {})
        return response.data

    } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Не вдалося зберегти спробу. Спробуйте ще раз.')
    }
}