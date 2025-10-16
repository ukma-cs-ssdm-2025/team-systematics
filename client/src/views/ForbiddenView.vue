<template>
    <div class="forbidden-message">
        <h1>403: Доступ заборонено</h1>
        <p>У вас немає прав для доступу до цієї сторінки.</p>
        <div>
            <router-link class="login-link" to="/login">Увійти в акаунт</router-link>
        </div>
    </div>
</template>

<style scoped>
.forbidden-message {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 20px;
    min-height: 100vh;
}

.forbidden-message h1 {
    font-size: 5rem;
    color: var(--color-purple);
}

.forbidden-message p, .login-link {
    font-size: 1.2rem;
}

.login-link {
    text-decoration: underline;
}

</style>