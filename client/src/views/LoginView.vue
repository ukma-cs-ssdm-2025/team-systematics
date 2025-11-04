<template>
    <main class="container">
        <div class="login-card-header">
            <img src="../assets/icons/graduate-hat.svg" alt="Шапка випускника" width="100" height="100">
            <h1>Вітаємо в Systematics!</h1>
        </div>
        <div class="login-card">
            <form id="loginForm" autocomplete="on" @submit="handleLogin">
                <div class="form-group">
                    <label for="email" class="form-label">
                        Електронна пошта
                    </label>
                    <input type="email" id="email" name="email" required v-model="email" class="form-input"
                        placeholder="myemail@gmail.com" autocomplete="email" />
                </div>

                <div class="form-group">
                    <label for="password" class="form-label">
                        Пароль
                    </label>
                    <input type="password" id="password" name="password" required v-model="password" class="form-input"
                        placeholder="password123" autocomplete="current-password" />
                </div>

                <div class="forgot-password-link-container">
                    <a href="#" class="forgot-password-link" aria-label="Забули пароль? Натисніть тут для відновлення.">
                        Забули пароль?
                    </a>
                </div>

                <CButton type="submit" id="submitButton" class="submit-button">
                    Увійти
                </CButton>

                <div class="register-link-container">
                    <div class="register-text">Ще не маєте акаунту? <a href="#" class="register-link"
                            aria-label="Зареєструватися">Зареєструватися</a></div>
                </div>
            </form>
        </div>
    </main>
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
    margin: 0;
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
    background-color: var(--color-lavender);
    color: var(--color-black);
}

#submitButton:hover {
    background-color: var(--color-dark-lavender);
}

</style>

<script setup>
import { ref } from 'vue'
import { useAuth } from '../store/loginInfo'
import { loginUser} from '../api/auth'
import { useRouter } from 'vue-router'
import CButton from '../components/global/CButton.vue'

const email = ref('')
const password = ref('')
const auth = useAuth()
const router = useRouter()
    
// Відправляє дані на бекенд і зберігає токен
const handleLogin = async (e) => {
  e.preventDefault()

  try {
    const data = await loginUser(email.value, password.value)
    // Адаптуємо формат даних
    const adaptedData = {
      access_token: data.access_token,
      token_type: "bearer",
      role: data.user.roles[0],  // Беремо першу роль
      full_name: data.user.full_name,
      major_name: data.user.user_major,
      avatar_url: data.user.avatar_url,
    }
    auth.login(adaptedData)

    console.log(auth.role)

    if (auth.role.value === 'student') {
        router.push('/exams')
    } else if (auth.role.value === 'teacher') {
        router.push('/courses/my')
    } else {
        // Якщо роль невідома або відсутня
        router.push('/forbidden')
    }

  } catch (err) {
    console.error(err)
    alert(err.message)
  }
}
</script>
