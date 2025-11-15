<template>
    <main class="container">
        <div class="login-card-header">
            <img src="../assets/icons/graduate-hat.svg" alt="Шапка випускника" width="100" height="100">
            <h1>Реєстрація в Systematics</h1>
        </div>
        <div class="login-card">
            <form id="registerForm" autocomplete="on" @submit="handleRegister">
                <div class="form-group">
                    <label for="email" class="form-label">
                        Електронна пошта
                    </label>
                    <input type="email" id="email" name="email" required v-model="email" class="form-input"
                        placeholder="myemail@gmail.com" autocomplete="email" />
                </div>

                <div class="form-group">
                    <label for="firstName" class="form-label">
                        Ім'я
                    </label>
                    <input type="text" id="firstName" name="firstName" required v-model="firstName" class="form-input"
                        placeholder="Іван" autocomplete="given-name" />
                </div>

                <div class="form-group">
                    <label for="lastName" class="form-label">
                        Прізвище
                    </label>
                    <input type="text" id="lastName" name="lastName" required v-model="lastName" class="form-input"
                        placeholder="Іванов" autocomplete="family-name" />
                </div>

                <div class="form-group">
                    <label for="patronymic" class="form-label">
                        По батькові (необов'язково)
                    </label>
                    <input type="text" id="patronymic" name="patronymic" v-model="patronymic" class="form-input"
                        placeholder="Іванович" autocomplete="additional-name" />
                </div>

                <div class="form-group">
                    <label for="major" class="form-label">
                        Спеціальність
                    </label>
                    <input 
                        type="text" 
                        id="major" 
                        name="major" 
                        required 
                        v-model="selectedMajorName" 
                        class="form-input"
                        placeholder="Почніть вводити назву спеціальності..."
                        autocomplete="off"
                        list="majors-list"
                        @input="handleMajorInput"
                        @change="handleMajorChange"
                    />
                    <datalist id="majors-list">
                        <option v-for="major in majors" :key="major.id" :value="major.name" :data-id="major.id">
                            {{ major.name }}
                        </option>
                    </datalist>
                </div>

                <div class="form-group">
                    <label for="password" class="form-label">
                        Пароль
                    </label>
                    <input type="password" id="password" name="password" required v-model="password" class="form-input"
                        placeholder="password123" autocomplete="new-password" />
                </div>

                <div class="form-group">
                    <label for="confirmPassword" class="form-label">
                        Підтвердіть пароль
                    </label>
                    <input type="password" id="confirmPassword" name="confirmPassword" required v-model="confirmPassword" class="form-input"
                        placeholder="password123" autocomplete="new-password" />
                </div>

                <div v-if="errorMessage" class="error-message">
                    {{ errorMessage }}
                </div>

                <CButton type="submit" id="submitButton" class="submit-button" :disabled="loading">
                    {{ loading ? 'Реєстрація...' : 'Зареєструватися' }}
                </CButton>

                <div class="register-link-container">
                    <div class="register-text">Вже маєте акаунт? <router-link to="/login" class="register-link"
                            aria-label="Увійти">Увійти</router-link></div>
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

#registerForm {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

#registerForm .form-label {
    font-weight: bold;
}

/* Приховуємо стрілочку для input з datalist */
#registerForm input[list]::-webkit-calendar-picker-indicator {
    display: none !important;
    opacity: 0;
    pointer-events: none;
    position: absolute;
    width: 0;
    height: 0;
}

#registerForm input[list]::-webkit-inner-spin-button,
#registerForm input[list]::-webkit-outer-spin-button {
    display: none !important;
    -webkit-appearance: none;
    margin: 0;
}

#registerForm input[list] {
    -webkit-appearance: none;
    -moz-appearance: textfield;
    appearance: none;
}

#registerForm input[list]::-ms-expand {
    display: none;
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
import { ref, onMounted } from 'vue'
import { useAuth } from '../store/loginInfo'
import { registerUser } from '../api/auth'
import { useRouter } from 'vue-router'
import CButton from '../components/global/CButton.vue'
import { http } from '../api/http.js'

const email = ref('')
const firstName = ref('')
const lastName = ref('')
const patronymic = ref('')
const selectedMajorName = ref('')
const selectedMajorId = ref(null)
const password = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')
const loading = ref(false)
const majors = ref([])
const auth = useAuth()
const router = useRouter()

// Оновлює значення спеціальності на основі введеного тексту
function updateMajorFromInput(inputValue) {
    const trimmedValue = inputValue.trim()
    selectedMajorName.value = trimmedValue
    updateMajorId(trimmedValue)
}

// Обробка введення спеціальності
function handleMajorInput(event) {
    updateMajorFromInput(event.target.value)
}

// Обробка зміни спеціальності (коли вибрано зі списку)
function handleMajorChange(event) {
    updateMajorFromInput(event.target.value)
}

// Оновлює ID спеціальності на основі назви
function updateMajorId(majorName) {
    const major = majors.value.find(m => m.name.toLowerCase() === majorName.toLowerCase())
    if (major) {
        selectedMajorId.value = major.id
    } else {
        selectedMajorId.value = null
    }
}

// Завантажуємо список спеціальностей
onMounted(async () => {
    try {
        const response = await http.get('/api/users/majors')
        majors.value = response.data
    } catch (error) {
        console.error('Помилка завантаження спеціальностей:', error)
        errorMessage.value = 'Не вдалося завантажити список спеціальностей.'
    }
})
    
// Відправляє дані на бекенд і реєструє користувача
const handleRegister = async (e) => {
  e.preventDefault()
  errorMessage.value = ''
  
  // Перевірка паролів
  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Паролі не співпадають.'
    return
  }

  // Перевірка вибору спеціальності
  if (!selectedMajorName.value || !selectedMajorId.value) {
    errorMessage.value = 'Будь ласка, оберіть спеціальність зі списку.'
    return
  }

  loading.value = true

  try {
    const data = await registerUser(
      email.value,
      password.value,
      firstName.value,
      lastName.value,
      patronymic.value || null,
      selectedMajorId.value
    )
    
    // Адаптуємо формат даних
    const adaptedData = {
      access_token: data.access_token,
      token_type: "bearer",
      role: data.user.roles[0],  // Беремо першу роль (завжди 'student' при реєстрації)
      full_name: data.user.full_name,
      major_name: data.user.user_major,
      avatar_url: data.user.avatar_url,
    }
    auth.login(adaptedData)

    // Після реєстрації користувач автоматично логіниться і перенаправляється
    if (auth.role.value === 'student') {
        router.push('/exams')
    } else {
        router.push('/forbidden')
    }

  } catch (err) {
    console.error(err)
    errorMessage.value = err.message || 'Помилка реєстрації. Спробуйте ще раз.'
  } finally {
    loading.value = false
  }
}
</script>

