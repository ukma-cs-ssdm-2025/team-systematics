import { http } from '../api/http.js'
import mockTranscript from '../mocks/transcript.json'

// Тимчасово використовуємо заглушку
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

export async function getTranscript() {
    if (USE_MOCK_DATA) {
        return mockTranscript
    }

    try {
        const response = await http.get('/api/users/me/transcript')
        return response.data
    } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Помилка завантаження атестату: не вдалося зв’язатися з сервером.')
    }
}