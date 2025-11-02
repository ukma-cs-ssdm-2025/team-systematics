import { http } from '../api/http.js'
import mockExams from '../mocks/exams.json'
import examJournalMock from '../mocks/examJournal.json'

// Тимчасово використовуємо заглушку
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

// Отримує іспити, вже розділені бекендом на майбутні та виконані
export async function getExams() {
    if (USE_MOCK_DATA) {
        return mockExams
    }

    try {
        const response = await http.get('/api/exams')
        return response.data
    } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Помилка завантаження іспитів: не вдалося зв’язатися з сервером.')
    }
}

// Отримує абсолютно всі іспити одним списком
export async function getAllExams() {
    if (USE_MOCK_DATA) {
        return mockExams
    }

    try {
        // Додаємо параметр ?view=all до запиту
        const response = await http.get('/api/exams', {
                params: {
                view: 'all'
            } 
        })
        return response.data
    } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Помилка завантаження іспитів: не вдалося зв’язатися з сервером.')
    }
}

// Отримує дані для журналу конкретного іспиту
export async function getExamJournal(examId) {
    if (USE_MOCK_DATA) {
        return examJournalMock
    }
    try {
        // Ендпоінт тепер прив'язаний до іспиту
        const response = await http.get(`/api/teacher/exams/${examId}/journal`)
        return response.data
    } catch (error) {
        console.error(`API Error fetching exam journal for ${examId}:`, error)
        throw new Error('Не вдалося завантажити дані журналу.')
    }
}