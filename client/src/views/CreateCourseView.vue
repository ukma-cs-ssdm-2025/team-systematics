<!-- views/CreateCourseView.vue -->
<template>
    <div>
        <Header />
        <main class="container">
            <section class="content-section">
                <div class="page-header">
                    <h2>Створення нового курсу</h2>
                </div>

                <div class="form-wrapper">
                    <form @submit.prevent="handleCreateCourse">
                        <div class="form-group">
                            <label for="course-name">Назва курсу</label>
                            <CInput
                                id="course-name"
                                v-model.trim="courseData.name"
                                placeholder="Введіть назву..."
                                required
                                :disabled="loading"
                                maxlength="200"
                                @blur="capitalizeFirstLetter('name')"
                            />
                        </div>

                        <div class="form-group">
                            <label for="course-code">Код курсу</label>
                            <CInput
                                id="course-code"
                                :value="courseData.code"
                                @input="formatCourseCode"
                                placeholder="Введіть унікальний код, наприклад, MA101"
                                required
                                minlength="5"
                                maxlength="5"
                                :disabled="loading"
                            />
                        </div>
                        <div v-if="codeError" class="validation-error">{{ codeError }}</div>

                        <div class="form-group">
                            <label for="course-description">Опис (опціонально)</label>
                            <CTextarea
                                id="course-description"
                                v-model.trim="courseData.description"
                                placeholder="Розкажіть, про що цей курс..."
                                :disabled="loading"
                                @blur="capitalizeFirstLetter('description')"
                            />
                        </div>

                        <div v-if="error" class="status-message error">{{ error }}</div>
                        <div v-if="success" class="status-message success">Курс успішно створено!</div>

                        <CButton type="submit" :disabled="loading" class="submit-button">
                            {{ loading ? 'Створення...' : 'Створити курс' }}
                        </CButton>
                    </form>
                </div>
            </section>
        </main>
    </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import Header from '../components/global/Header.vue'
import CButton from '../components/global/CButton.vue'
import CInput from '../components/global/CInput.vue'
import CTextarea from '../components/global/CTextarea.vue'
import { createNewCourse } from '../api/courses.js'     

const router = useRouter()
const loading = ref(false)
const error = ref(null)
const success = ref(false)
const codeError = ref('')

const courseData = ref({
    name: '',
    code: '',
    description: null,
})

function capitalizeFirstLetter(fieldName) {
    const value = courseData.value[fieldName];
    if (value && value.length > 0) {
        courseData.value[fieldName] = value.charAt(0).toUpperCase() + value.slice(1);
    }
}

function formatCourseCode(event) {
    const inputElement = event.target
    
    const formattedValue = inputElement.value
        .toUpperCase()
        .replaceAll(/[^A-Z0-9]/g, '')
        .slice(0, 5)
    
    courseData.value.code = formattedValue
    inputElement.value = formattedValue
}


watch(() => courseData.value.code, (newCode) => {
    const requiredPattern = /^[A-Z]{2}\d{3}$/
    
    if (newCode && newCode.length === 5 && !requiredPattern.test(newCode)) {
        codeError.value = 'Невірний формат. Потрібно 2 літери та 3 цифри (напр., CS101).'
    } else {
        codeError.value = ''
    }
})

async function handleCreateCourse() {
    loading.value = true
    error.value = null
    success.value = false

    try {
        const payload = {
            ...courseData.value,
            description: courseData.value.description || null
        }
        
        await createNewCourse(payload)
        success.value = true
        router.push('/courses/me')

    } catch (err) {
        error.value = err.message || 'Не вдалося створити курс. Перевірте введені дані.'
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>

.form-wrapper {
    max-width: 800px;
}

.form-group, .validation-error {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 12px;
    font-weight: bold;
    color: var(--color-dark-gray);
}

.status-message {
  padding: 12px;
  margin-bottom: 20px;
  border-radius: 8px;
  text-align: center;
}

.error, .validation-error {
  color: var(--color-red);
}

.success {
  color: var(--color-green);
}
</style>