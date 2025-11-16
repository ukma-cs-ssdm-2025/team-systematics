<template>
    <div>
        <Header />
        <main class="container">
            <Breadcrumbs />
            <!-- 1. Стан завантаження -->
            <div v-if="loading" class="status-message">
                Завантаження профілю...
            </div>

            <!-- 2. Стан помилки -->
            <div v-else-if="error" class="status-message error">
                Помилка завантаження: {{ error }}
            </div>

            <!-- 3. Основний контент -->
            <div v-else class="profile-layout">
                <div class="profile-section">
                    <h2 class="section-title">Мій профіль</h2>
                    <div class="profile-details">
                        <div class="avatar-container">
                            <img :src="avatarSrc" @error="handleAvatarError" alt="Аватар профілю"
                                class="profile-avatar">

                            <!-- 2. Клік на кнопці викликає клік на прихованому input -->
                            <button @click="triggerFileInput" class="edit-avatar-btn" title="Змінити аватар">
                                <img src="../assets/icons/user-edit.svg" alt="Редагувати">
                            </button>

                            <!-- 3. Прихований input для вибору файлу -->
                            <input type="file" ref="fileInput" @change="handleFileChange"
                                accept="image/png, image/jpeg, image/webp" style="display: none;">
                        </div>
                        <div class="info-grid">
                            <div class="info-label">Повне ім'я</div>
                            <div class="info-value">{{ userProfile.full_name }}</div>

                            <div class="info-label">Електронна пошта</div>
                            <div class="info-value">{{ userProfile.email }}</div>

                            <div class="info-label">Спеціальність</div>
                            <div class="info-value">{{ userProfile.major_name }}</div>
                        </div>
                    </div>
                </div>

                <div class="notification-section">
                    <h2 class="section-title">Сповіщення</h2>
                    <div class="notification-toggle-row">
                        <p>Я хочу отримувати сповіщення на свою електронну пошту з нагадуванням про майбутні іспити.</p>
                        <label class="switch">
                            <input type="checkbox" v-model="notificationSettings.enabled" tabindex="0"
                                @keydown.enter.prevent="notificationSettings.enabled = !notificationSettings.enabled"
                                @keydown.space.prevent="notificationSettings.enabled = !notificationSettings.enabled">
                            <span class="slider round"></span>
                        </label>
                    </div>

                    <transition name="fade">
                        <div v-if="notificationSettings.enabled" class="notification-options">
                            <label v-for="option in reminderOptions" :key="option.value" class="option-item">
                                <!-- 1. Прихований чекбокс з v-model -->
                                <input type="checkbox" class="real-checkbox" :value="option.value"
                                    v-model="notificationSettings.remind_before_hours" />

                                <!-- 2. Кастомний чекбокс, який тепер реагує на v-model -->
                                <div class="custom-checkbox" aria-hidden="true">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="17" height="13" viewBox="0 0 17 13"
                                        fill="none"
                                        v-if="notificationSettings.remind_before_hours.includes(option.value)">
                                        <path
                                            d="M5.7 12.025L0 6.325L1.425 4.9L5.7 9.175L14.875 0L16.3 1.425L5.7 12.025Z"
                                            fill="black" />
                                    </svg>
                                </div>

                                <!-- 3. Текст варіанту -->
                                <div class="option-content">
                                    <p class="option-text">{{ option.text }}</p>
                                </div>
                            </label>
                        </div>
                    </transition>
                </div>

                <div class="actions">
                    <CButton @click="saveSettings" :disabled="isSaving" class="save-button">
                        {{ isSaving ? 'Збереження...' : 'Зберегти зміни' }}
                    </CButton>
                </div>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Header from '../components/global/Header.vue'
import Breadcrumbs from '../components/global/Breadcrumbs.vue'
import CButton from '../components/global/CButton.vue'
import * as userModule from '../api/users'
import defaultAvatar from '../assets/icons/user-avatar-default.svg'
import { useAuth } from '../store/loginInfo'

const userProfile = ref(null)
const notificationSettings = ref({
    enabled: false,
    remind_before_hours: []
})
const loading = ref(true)
const error = ref(null)
const isSaving = ref(false)

const reminderOptions = ref([
    { text: 'За 24 години', value: 24 },
    { text: 'За 8 годин', value: 8 },
    { text: 'За 1 годину', value: 1 }
])

const fileInput = ref(null)
const avatarPreview = ref(null) // URL для миттєвого прев'ю
const selectedFile = ref(null) // Сам обраний файл
const avatarError = ref(false)

const auth = useAuth()

const avatarSrc = computed(() => {
    if (avatarPreview.value) {
        return avatarPreview.value
    }
    const url = userProfile.value?.avatar_url
    // Якщо є помилка або URL порожній/null, використовуємо дефолтну аватарку
    if (avatarError.value || !url || (typeof url === 'string' && url.trim() === '')) {
        return defaultAvatar
    }
    return url
})

function handleAvatarError(event) {
    // Якщо зображення не завантажилося, встановлюємо помилку
    avatarError.value = true
    // Встановлюємо src на дефолтну аватарку
    if (event.target) {
        event.target.src = defaultAvatar
    }
}

function triggerFileInput() {
    fileInput.value.click()
}

function handleFileChange(event) {
    const file = event.target.files[0]
    if (!file) return

    // Зберігаємо файл для подальшого завантаження
    selectedFile.value = file
    avatarError.value = false // Скидаємо помилку при виборі нового файлу

    // Створюємо тимчасовий URL для миттєвого попереднього перегляду
    const reader = new FileReader()
    reader.onload = (e) => {
        avatarPreview.value = e.target.result
    }
    reader.readAsDataURL(file)
}

function toggleNotifications(event) {
    notificationSettings.value.enabled = !notificationSettings.value.enabled
}

async function saveSettings() {
    isSaving.value = true
    try {
        // Створюємо масив промісів для паралельного виконання
        const tasks = []

        // Якщо був обраний новий файл, додаємо його завантаження до завдань
        if (selectedFile.value) {
            const avatarResponse = await userModule.uploadAvatar(selectedFile.value)
            auth.updateAvatarUrl(avatarResponse.avatar_url)

            if (userProfile.value) {
                userProfile.value.avatar_url = avatarResponse.avatar_url
            }
        }


        // Додаємо оновлення налаштувань сповіщень до завдань
        const notificationsPayload = {
            ...notificationSettings.value,
            remind_before_hours: notificationSettings.value.enabled
                ? notificationSettings.value.remind_before_hours
                : []
        }
        tasks.push(userModule.updateUserNotificationSettings(notificationsPayload))

        // Виконуємо всі завдання паралельно
        await Promise.all(tasks)

        // Очищуємо прев'ю після успішного збереження
        avatarPreview.value = null
        selectedFile.value = null
    } catch (err) {
        alert(err.message || 'Помилка збереження.')
    } finally {
        isSaving.value = false
    }
}

onMounted(async () => {
    try {
        // Завантажуємо дані паралельно для швидкості
        const [profileData, notificationsData] = await Promise.all([
            userModule.getUserProfile(),
            userModule.getUserNotificationSettings()
        ])
        userProfile.value = profileData
        notificationSettings.value = notificationsData
        avatarError.value = false // Скидаємо помилку при завантаженні профілю
    } catch (err) {
        error.value = err.message || "Не вдалося завантажити дані."
    } finally {
        loading.value = false
    }
})
</script>

<style scoped>
.profile-details {
    display: flex;
    align-items: center;
    gap: 40px;
}

.avatar-container {
    position: relative;
}

.profile-avatar {
    width: 240px;
    height: 240px;
    border-radius: 50%;
    background-color: var(--color-gray);
}

.edit-avatar-btn {
    position: absolute;
    bottom: 5px;
    right: 5px;
    background: white;
    border: 1px solid var(--color-gray);
    border-radius: 50%;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.edit-avatar-btn:hover {
    background-color: #f5f5f5;
}

.info-grid {
    display: grid;
    grid-template-columns: 150px 1fr;
    gap: 16px;
    font-size: 1rem;
}

.info-label {
    font-weight: bold;
}

.notification-toggle-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-radius: 8px;
}

.notification-toggle-row p {
    margin: 0;
}

.notification-options {
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.switch {
    position: relative;
    display: inline-block;
    width: 60px;
    height: 34px;
}

.switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--color-dark-gray);
    transition: .4s;
}

.slider:before {
    position: absolute;
    content: "";
    height: 26px;
    width: 26px;
    left: 4px;
    bottom: 4px;
    background-color: var(--color-white);
    transition: .4s;
}

.switch input:focus-visible + .slider {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

input:checked+.slider {
    background-color: var(--color-violet);
}

input:checked+.slider:before {
    transform: translateX(26px);
}

.slider.round {
    border-radius: 34px;
}

.slider.round:before {
    border-radius: 50%;
}

.slider:focus-visible {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.actions {
    margin-top: 20px;
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

.option-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-radius: 12px;
    cursor: pointer;
    transition: all 150ms ease;
}

.option-item:hover {
    border-color: var(--color-dark-gray);
}

.option-item.selected {
    border-color: var(--color-purple);
    background-color: var(--color-lavender);
}

.real-checkbox {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
    cursor: pointer;
}

.custom-checkbox {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 4px;
    background-color: var(--color-gray);
    transition: all 150ms ease;
}

.check-icon {
    width: 24px;
    height: 24px;
    stroke: var(--color-dark-purple);
    opacity: 0;
    transform: scale(0.5);
    transition: all 150ms ease;
}

.option-item.selected .check-icon {
    opacity: 1;
    transform: scale(1);
}

.option-item:has(.real-checkbox:focus-visible) {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.option-content {
    display: flex;
    justify-content: space-between;
    flex-grow: 1;
}
</style>