<template>
    <header class="header">
        <nav class="nav">
            <div class="nav-list-container">
                <ul class="nav-list">
                    <li v-if="auth.isStudent.value" class="nav-item" :class="{ active: route.path === '/exams' }">
                        <router-link to="/exams">Мої іспити</router-link>
                    </li>
                    <li v-if="auth.isStudent.value" class="nav-item" :class="{ active: route.path === '/transcript' }">
                        <router-link to="/transcript">Мій атестат</router-link>
                    </li>
                    <li v-if="auth.isTeacher.value" class="nav-item" :class="{ active: route.path === '/courses/my' }">
                        <router-link to="/courses/my">Мої курси</router-link>
                    </li>
                    <li v-if="auth.isTeacher.value" class="nav-item" :class="{ active: route.path === '/plagiarism-check' }">
                        <router-link to="/plagiarism-check">Перевірка плагіату</router-link>
                    </li>
                    <li v-if="auth.isStudent.value" class="nav-item" :class="{ active: route.path === '/courses' }">
                        <router-link to="/courses">Каталог курсів</router-link>
                    </li>
                    <li v-if="auth.isSupervisor.value" class="nav-item" :class="{ active: route.path === '/courses/supervisor' }">
                        <router-link to="/courses/supervisor">Курси</router-link>
                    </li>
                </ul>
            </div>
            <div class="user-container">
                <div class="user-greeting">
                    Вітаємо, {{ auth.fullName || 'користувачу' }}!
                </div>

                <div class="user-profile" ref="dropdownMenu">
                    <button type="button" class="user-avatar" @click="toggleDropdown" tabindex="0"
                        @keydown="handleKeyDown" :aria-expanded="isDropdownVisible"
                        aria-label="Відкрити меню користувача">
                        <img :src="avatarSrc" @error="handleAvatarError" alt="Аватар користувача">
                    </button>

                    <div v-if="isDropdownVisible" class="dropdown-content">
                        <ul>
                            <li>
                                <router-link to="/my-profile">
                                    <img src="../../assets/icons/user-edit.svg" alt="Налаштування профіля"> Налаштування
                                    профіля
                                </router-link>
                            </li>
                            <router-link to="/login" @click="handleLogout">
                                <img src="../../assets/icons/log-out.svg" alt="Вийти з акаунту"> Вийти
                            </router-link>
                        </ul>
                    </div>
                </div>
            </div>
        </nav>
    </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '../../store/loginInfo'
import defaultAvatar from '../../assets/icons/user-avatar-default.svg'

const auth = useAuth()
const route = useRoute()

const isDropdownVisible = ref(false)
const dropdownMenu = ref(null)
const avatarError = ref(false)

const avatarSrc = computed(() => {
    const url = auth.avatarUrl.value
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

// Функція для перемикання видимості меню
function toggleDropdown() {
    isDropdownVisible.value = !isDropdownVisible.value
}

function handleKeyDown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault()
        toggleDropdown()
    }
}

function handleLogout() {
    auth.logout()
    isDropdownVisible.value = false
}

function handleClickOutside(event) {
    if (isDropdownVisible.value && dropdownMenu.value && !dropdownMenu.value.contains(event.target)) {
        isDropdownVisible.value = false
    }
}

onMounted(() => {
    document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.header {
    background-color: var(--color-violet);
}

.nav {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    margin: 0 120px;
    color: var(--color-white);
    font-weight: bold;
    font-size: 24px;
}

.nav-list,
.user-container {
    display: flex;
    flex-direction: row;
    justify-content: flex-start;
    align-items: center;
    gap: 40px;
}

.nav-item {
    list-style: none;
    padding: 20px;
}

.nav-item a,
.nav-item a:visited {
    text-decoration: none;
    color: var(--color-white);
}

.nav-item.active {
    background-color: var(--color-purple);
}

.user-greeting {
    white-space: nowrap;
}

.user-profile {
    position: relative;
    display: inline-block;
}

.user-avatar {
    border: none;
    cursor: pointer;
    border-radius: 50%;
    padding: 0;
    background: transparent;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.user-avatar img {
    width: 40px;
    height: 40px;
    display: block;
    object-fit: cover;
    border-radius: 50%;
}

.dropdown-content {
    position: absolute;
    right: 0;
    top: calc(100% + 36px);
    background-color: var(--color-violet);
    min-width: 400px;
    box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 16px 0;
    z-index: 100;
    font-size: 16px;
}

.dropdown-content ul {
    list-style: none;
    margin: 0;
    padding: 0;
}

.dropdown-content li,
a {
    width: 100%;
    color: var(--color-white);
    padding: 12px 20px;
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.dropdown-content li:has(a) {
    padding: 0;
}

.dropdown-content li:hover,
.dropdown-content a:hover {
    background-color: var(--color-purple);
}
</style>