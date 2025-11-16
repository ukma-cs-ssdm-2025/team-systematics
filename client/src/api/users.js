import { http } from '../api/http.js'
import userProfileMock from '../mocks/userProfile.json'
import userNotificationMocks from '../mocks/userNotificationSettings.json'

// Тимчасово використовуємо заглушку
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'


// Отримує дані профілю поточного користувача
export async function getUserProfile() {
    if (USE_MOCK_DATA) {
        return userProfileMock
    }
    try {
        const response = await http.get('/api/users/me')
        return response.data
    } catch (error) {
        console.error('API Error fetching user profile:', error)
        throw new Error('Не вдалося завантажити дані профілю.')
    }
}

// Отримує налаштування сповіщень поточного користувача
export async function getUserNotificationSettings() {
    if (USE_MOCK_DATA) {
        return userNotificationMocks
    }
    try {
        const response = await http.get('/api/users/me/notifications')
        return response.data
    } catch (error) {
        console.error('API Error fetching notification settings:', error)
        throw new Error('Не вдалося завантажити налаштування сповіщень.')
    }
}

// Оновлює налаштування сповіщень поточного користувача
export async function updateUserNotificationSettings(settings) {
    try {
        const response = await http.put('/api/users/me/notifications', settings)
        return response.data
    } catch (error) {
        console.error('API Error updating notification settings:', error)
        throw new Error('Не вдалося зберегти налаштування.')
    }
}

// Завантажує новий аватар користувача на сервер
export async function uploadAvatar(file) {
    if (USE_MOCK_DATA) {
        return newAvatarMock
    }

    // Створюємо об'єкт FormData для відправки файлу
    const formData = new FormData()
    formData.append('avatar_file', file)

    try {
        const response = await http.post('/api/users/me/avatar', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return response.data
    } catch (error) {
        console.error('API Error uploading avatar:', error)
        throw new Error('Не вдалося завантажити аватар.')
    }
}