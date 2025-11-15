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

                <div v-if="errorMessage" class="error-message">
                    {{ errorMessage }}
                </div>

                <CButton type="submit" id="submitButton" class="submit-button" :disabled="loading">
                    {{ loading ? 'Вхід...' : 'Увійти' }}
                </CButton>

                <div class="register-link-container">
                    <div class="register-text">Ще не маєте акаунту? <router-link to="/register" class="register-link"
                            aria-label="Зареєструватися">Зареєструватися</router-link></div>
                </div>
            </form>
        </div>
    </main>
</template>

<style scoped>
.container {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    align-items: center;
    min-height: 100vh;
    width: 100%;
    margin: 0;
    padding-top: calc(50vh - 300px);
    padding-bottom: 120px;
}

h1 {
    text-align: center;
    margin: 0;
}

.login-card {
    border-radius: 40px;
    background-color: var(--color-violet);
    color: var(--color-white);
    min-width: 450px;
    padding: 40px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.login-card-header {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 180px;
    margin-bottom: 40px;
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


.register-link {
    text-decoration: underline;
    color: var(--color-white);
}

.register-link-container {
    display: flex;
    justify-content: center;
}

#submitButton {
    background-color: var(--color-lavender);
    color: var(--color-black);
    margin-top: 36px;
}

#submitButton:hover {
    background-color: var(--color-dark-lavender);
}

#submitButton:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.error-message {
    color: var(--color-red, #ff6b6d);
    background-color: rgba(255, 107, 109, 0.1);
    border: 1px solid var(--color-red, #ff6b6d);
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    font-size: 0.9rem;
    margin-top: 12px;
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
const errorMessage = ref('')
const loading = ref(false)
const auth = useAuth()
const router = useRouter()
    
// Відправляє дані на бекенд і зберігає токен
const handleLogin = async (e) => {
  e.preventDefault()
  errorMessage.value = ''
  loading.value = true

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

    if (auth.role.value === 'student') {
        router.push('/exams')
    } else if (auth.role.value === 'teacher') {
        router.push('/courses/my')
    } else if (auth.role.value === 'supervisor') {
        router.push('/courses/supervisor')
    } else {
        // Якщо роль невідома або відсутня
        router.push('/forbidden')
    }

  } catch (err) {
    console.error(err)
    errorMessage.value = err.message || 'Помилка входу. Спробуйте ще раз.'
  } finally {
    loading.value = false
  }
}
</script>
