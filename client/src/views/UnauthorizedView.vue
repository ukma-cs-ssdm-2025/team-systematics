<template>
    <div class="unauthorized-message">
        <Header />
        <main class="container">
            <div class="unauthorized-content">
                <h1>401: Неавторизований доступ</h1>
                <p>Вам потрібно увійти, щоб отримати доступ до цієї сторінки.</p>
                <div class="actions">
                    <CButton @click="goBack" variant="secondary">Назад</CButton>
                    <CButton @click="goToLogin" variant="secondary">Увійти в акаунт</CButton>
                </div>
            </div>
        </main>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'

const router = useRouter()

function goBack() {
    router.go(-1)
}

function goToLogin() {
    router.push('/login')
}
</script>

<style scoped>
.unauthorized-message {
    min-height: 100vh;
}

.unauthorized-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 24px;
    padding: 60px 20px;
    min-height: calc(100vh - 200px);
}

.unauthorized-content h1 {
    font-size: 4rem;
    color: var(--color-purple);
    margin: 0;
}

.unauthorized-content p {
    font-size: 1.2rem;
    color: var(--color-dark-gray);
    margin: 0;
}

.actions {
    display: flex;
    gap: 16px;
    margin-top: 16px;
}

@media (max-width: 768px) {
    .unauthorized-content h1 {
        font-size: 3rem;
    }
    
    .actions {
        flex-direction: column;
        width: 100%;
        max-width: 300px;
    }
}

</style>