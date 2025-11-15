import { http } from '../api/http.js'

export async function loginUser(email, password) {
    try {
        const response = await http.post('/api/auth/login', {
            email,
            password,
        })
        return response.data

    } catch (error) {
        if (error.response?.status === 401) {
            // Перекладаємо повідомлення помилок на українську
            const detail = error.response?.data?.detail || ''
            if (detail.includes('Invalid password') || detail.includes('password')) {
                throw new Error('Неправильний пароль. Спробуйте ще раз.')
            } else if (detail.includes('User not found') || detail.includes('not found')) {
                throw new Error('Користувача з такою електронною поштою не знайдено.')
            } else {
                throw new Error('Неправильна електронна пошта або пароль.')
            }
        }
        
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail)
        }

        throw new Error('Помилка входу: не вдалося зв\'язатися з сервером або невідома помилка.')
    }
}
