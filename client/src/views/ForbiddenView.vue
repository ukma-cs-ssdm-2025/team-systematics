<template>
    <div class="forbidden-message">
        <Header />
        <main class="container">
            <div class="forbidden-content">
                <h1>403: Доступ заборонено</h1>
                <p>У вас немає прав для доступу до цієї сторінки або виконаної дії.</p>
                <div class="actions">
                    <CButton @click="goBack" variant="secondary">Назад</CButton>
                    <CButton @click="goHome" variant="secondary">На головну</CButton>
                </div>
            </div>
        </main>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import { useAuth } from '../store/loginInfo.js'

const router = useRouter()
const auth = useAuth()

function goBack() {
    router.go(-1)
}

function goHome() {
    const auth = useAuth()
    if (auth.isStudent.value) {
        router.push('/exams')
    } else if (auth.isTeacher.value) {
        router.push('/courses/my')
    } else if (auth.isSupervisor.value) {
        router.push('/courses/supervisor')
    } else {
        router.push('/login')
    }
}
</script>

<style scoped>
.forbidden-message {
    min-height: 100vh;
}

.forbidden-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 24px;
    padding: 60px 20px;
    min-height: calc(100vh - 200px);
}

.forbidden-content h1 {
    font-size: 4rem;
    color: var(--color-purple);
    margin: 0;
}

.forbidden-content p {
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
    .forbidden-content h1 {
        font-size: 3rem;
    }
    
    .actions {
        flex-direction: column;
        width: 100%;
        max-width: 300px;
    }
}

</style>