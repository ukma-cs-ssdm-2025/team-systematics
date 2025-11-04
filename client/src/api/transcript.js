import { http } from './http.js'
import mockTranscript from '../mocks/transcript.json'

// Тимчасово використовуємо заглушку
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

export async function getTranscript(sortBy, order) {
    if (USE_MOCK_DATA) {
        return mockTranscript
    }

    try {
        // шукаємо параметри сортування
        const params = new URLSearchParams()
        if (sortBy) params.append('sort_by', sortBy)
        if (order) params.append('order', order)
        const response = await http.get(`/api/transcript?${params.toString()}`)
        return response.data
    } catch (error) {
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Помилка завантаження атестату: не вдалося зв’язатися з сервером.')
    }
}