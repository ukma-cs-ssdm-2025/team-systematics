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

export async function registerUser(email, password, firstName, lastName, patronymic = null, majorId = null) {
    try {
        const response = await http.post('/api/auth/register', {
            email,
            password,
            first_name: firstName,
            last_name: lastName,
            patronymic: patronymic || null,
            major_id: majorId || null,
        })
        return response.data

    } catch (error) {
        if (error.response?.status === 400) {
            const detail = error.response?.data?.detail || ''
            if (detail.includes('вже існує') || detail.includes('already exists')) {
                throw new Error('Користувач з такою електронною поштою вже існує.')
            }
            throw new Error(detail || 'Помилка реєстрації. Перевірте введені дані.')
        }
        
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail)
        }

        throw new Error('Помилка реєстрації: не вдалося зв\'язатися з сервером або невідома помилка.')
    }
}
