<template>
    <div class="container">
        <div class="login-card-header">
            <img src="../assets/icons/graduate-hat.svg" alt="Шапка випускника" width="100" height="100">
            <h1>Вітаємо в Systematics!</h1>
        </div>
        <!-- Login Card -->
        <div class="login-card">
            <form id="loginForm" autocomplete="on" @submit="handleLogin">
                <!-- Email Field -->
                <div class="form-group">
                    <label for="email" class="form-label">
                        Електронна пошта
                    </label>
                    <input type="email" id="email" name="email" required v-model="email" class="form-input"
                        placeholder="myemail@gmail.com" autocomplete="email" />
                </div>

                <!-- Password Field -->
                <div class="form-group">
                    <label for="password" class="form-label">
                        Пароль
                    </label>
                    <input type="password" id="password" name="password" required v-model="password" class="form-input"
                        placeholder="password123" autocomplete="current-password" />
                </div>

                <!-- Forgot Password Link -->
                <div class="forgot-password-link-container">
                    <a href="#" class="forgot-password-link" aria-label="Забули пароль? Натисніть тут для відновлення.">
                        Забули пароль?
                    </a>
                </div>

                <!-- Submit Button -->
                <button type="submit" id="submitButton" class="submit-button">
                    Увійти
                </button>

                <!-- Registration Link -->
                <div class="register-link-container">
                    <div class="register-text">Ще не маєте акаунту? <a href="#" class="register-link"
                            aria-label="Зареєструватися">Зареєструватися</a></div>
                </div>
            </form>
        </div>
    </div>
</template>

<style scoped>
.container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    width: 100%;
    gap: 40px;
}

h1 {
    text-align: center;
}

.login-card {
    border-radius: 40px;
    background-color: var(--color-violet);
    color: var(--color-white);
    min-width: 450px;
    padding: 40px;
}

.login-card-header {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

#loginForm {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

#loginForm .form-label {
    font-weight: bold;
}

.forgot-password-link,
.register-link {
    text-decoration: underline;
}

.register-link-container {
    display: flex;
    justify-content: center;
}

#submitButton {
    display: flex;
    padding: 20px 50px;
    justify-content: center;
    align-items: center;
    gap: 10px;
    align-self: stretch;
    border-radius: 50px;
    background: var(--color-lavender);
    box-shadow: 0 4px 4px 0 rgba(0, 0, 0, 0.25);
    cursor: pointer;
    font-weight: bold;
}
</style>

<script setup>
import { ref } from 'vue'
import { useAuth } from '../store/token'
import { loginUser} from '../api/auth'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const { login } = useAuth()
const router = useRouter()
    
// Відправляє дані на бекенд і зберігає токен
const handleLogin = async (e) => {
  e.preventDefault()

  try {
    const data = await loginUser(email.value, password.value)
    login(data.access_token)
    alert('Вхід успішний!')
    router.push('/exams')
  } catch (err) {
    console.error(err)
    alert(err.message)
  }
}
</script>
