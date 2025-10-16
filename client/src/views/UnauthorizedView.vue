<template>
    <div class="unauthorized-message">
        <h1>401: Неавторизований доступ</h1>
        <p>Вам потрібно увійти, щоб отримати доступ до цієї сторінки.</p>
        <div>
            <router-link class="login-link" to="/login">Увійти в акаунт</router-link>
        </div>
    </div>
</template>

<style scoped>
.unauthorized-message {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 20px;
    min-height: 100vh;
}

.unauthorized-message h1 {
    font-size: 5rem;
    color: var(--color-purple);
}

.unauthorized-message p, .login-link {
    font-size: 1.2rem;
}

.login-link {
    text-decoration: underline;
}

</style>