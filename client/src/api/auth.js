import { http } from '../api/http.js'

export async function loginUser(email, password) {
    try {
        const response = await http.post('/api/auth/login', {
            email,
            password,
        })
        return response.data

    } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            throw new Error(error.response.data.detail)
        }

        throw new Error('Помилка входу: не вдалося зв’язатися з сервером або невідома помилка.')
    }
}