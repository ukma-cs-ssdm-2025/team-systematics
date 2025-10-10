<template>
    <header class="header">
        <nav class="nav">
            <div class="nav-list-container">
                <ul class="nav-list">
                    <li class="nav-item" :class="{ active: route.path === '/exams' }">
                        <router-link to="/exams">Мої іспити</router-link>
                    </li>
                    <li class="nav-item" :class="{ active: route.path === '/transcript' }">
                        <router-link to="/transcript">Мій атестат</router-link>
                    </li>
                </ul>
            </div>
            <div class="user-container">
                <div class="user-greeting">
                    Вітаємо, студенте!
                </div>
                <div class="user-avatar">
                    <img src="../../assets/icons/user-avatar-default.svg" alt="Default user avatar">
                </div>
            </div>
        </nav>
    </header>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
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

.nav-list, .user-container {
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

.user-avatar img {
    width: 40px;
    height: 40px;
}
</style>