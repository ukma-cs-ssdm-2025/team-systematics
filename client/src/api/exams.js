import { http } from '../api/http.js'
import mockExams from '../mocks/exams.json'
import examJournalMock from '../mocks/examJournal.json'

// Тимчасово використовуємо заглушку
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

// Отримує іспити, вже розділені бекендом на майбутні та виконані
export async function getExams() {
    if (USE_MOCK_DATA) {
        return mockExams
    }

    try {
        const response = await http.get('/api/exams')
        return response.data
    } catch (error) {
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail);
        }
        throw new Error('Помилка завантаження іспитів: не вдалося зв’язатися з сервером.')
    }
}

// Отримує абсолютно всі іспити одним списком
export async function getAllExams() {
    if (USE_MOCK_DATA) {
        return mockExams
    }

    try {
        // Додаємо параметр ?view=all до запиту
        const response = await http.get('/api/exams', {
                params: {
                view: 'all'
            } 
        })
        return response.data
    } catch (error) {
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail);
        }
        throw new Error('Помилка завантаження іспитів: не вдалося зв’язатися з сервером.')
    }
}

// Отримує інформацію про іспит за ID
export async function getExam(examId) {
    if (USE_MOCK_DATA) {
        // Повертаємо мокові дані, якщо потрібно
        return mockExams.future_exams?.[0] || mockExams.completed_exams?.[0] || {}
    }
    try {
        const response = await http.get(`/api/exams/${examId}`)
        return response.data
    } catch (error) {
        console.error(`API Error fetching exam ${examId}:`, error)
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail)
        }
        throw new Error('Не вдалося завантажити інформацію про іспит.')
    }
}

// Отримує дані для журналу конкретного іспиту
export async function getExamJournal(examId) {
    if (USE_MOCK_DATA) {
        return examJournalMock
    }
    try {
        // Ендпоінт тепер прив'язаний до іспиту
        const response = await http.get(`/api/exams/${examId}/journal`)
        return response.data
    } catch (error) {
        console.error(`API Error fetching exam journal for ${examId}:`, error)
        throw new Error('Не вдалося завантажити дані журналу.')
    }
}

// Створює зв'язок між екзаменом та курсом
async function linkExamToCourse(examId, courseId) {
    try {
        const response = await http.post(`/api/exams/${examId}/courses/${courseId}`)
        return response.data
    } catch (error) {
        console.error('Error linking exam to course:', error)
        throw error
    }
}

// Створює питання для екзамену
async function createQuestion(examId, questionData) {
    try {
        const response = await http.post(`/api/exams/${examId}/questions`, questionData)
        return response.data
    } catch (error) {
        console.error("API Error creating question:", error)
        throw error
    }
}

export async function createExam(examData) {
    try {
        // Створюємо екзамен
        const examResponse = await http.post("/api/exams", {
            title: examData.title,
            instructions: examData.instructions || null,
            start_at: examData.start_at,
            end_at: examData.end_at,
            duration_minutes: examData.duration_minutes,
            max_attempts: examData.max_attempts,
            pass_threshold: examData.pass_threshold,
            owner_id: examData.owner_id
        })
        const exam = examResponse.data
        
        // Зв'язуємо з курсом (якщо є course_id)
        if (examData.course_id) {
            try {
                await linkExamToCourse(exam.id, examData.course_id)
            } catch (linkError) {
                // Продовжуємо, навіть якщо зв'язок не вдався
                console.warn('Failed to link exam to course:', linkError)
            }
        }
        
        // Створюємо питання
        if (examData.questions && examData.questions.length > 0) {
            for (const question of examData.questions) {
                await createQuestion(exam.id, question)
            }
        }
        
        return exam
    } catch (error) {
        console.error("API Error creating a new exam", error)
        if (error.response?.data?.detail) {
            throw error
        }
        throw new Error('Не вдалося створити новий іспит.')
    }
}

// Отримує іспит з питаннями для редагування
export async function getExamForEdit(examId) {
    try {
        const response = await http.get(`/api/exams/${examId}/edit`)
        return response.data
    } catch (error) {
        console.error("API Error fetching exam for edit:", error)
        if (error.response?.data?.detail) {
            throw error
        }
        throw new Error('Не вдалося завантажити іспит для редагування.')
    }
}

// Публікує іспит (змінює статус з draft на published)
export async function publishExam(examId) {
    try {
        const response = await http.post(`/api/exams/${examId}/publish`)
        return response.data
    } catch (error) {
        console.error("API Error publishing exam:", error)
        if (error.response?.data?.detail) {
            throw error
        }
        throw new Error('Не вдалося опублікувати іспит.')
    }
}

// Видаляє іспит
export async function deleteExam(examId) {
    try {
        await http.delete(`/api/exams/${examId}`)
    } catch (error) {
        console.error("API Error deleting exam:", error)
        if (error.response?.data?.detail) {
            throw error
        }
        throw new Error('Не вдалося видалити іспит.')
    }
}

// Оновлює іспит
export async function updateExam(examId, examData) {
    try {
        // Оновлюємо основні дані іспиту
        const examResponse = await http.patch(`/api/exams/${examId}`, {
            title: examData.title,
            instructions: examData.instructions || null,
            start_at: examData.start_at,
            end_at: examData.end_at,
            duration_minutes: examData.duration_minutes,
            max_attempts: examData.max_attempts,
            pass_threshold: examData.pass_threshold
        })
        const exam = examResponse.data
        
        // Видаляємо всі старі питання та створюємо нові
        // Спочатку отримуємо список існуючих питань
        const existingExam = await getExamForEdit(examId)
        if (existingExam.questions) {
            for (const question of existingExam.questions) {
                try {
                    await http.delete(`/api/exams/${examId}/questions/${question.id}`)
                } catch (deleteError) {
                    // Ігноруємо помилки видалення окремих питань
                    console.warn(`Failed to delete question ${question.id}:`, deleteError)
                }
            }
        }
        
        // Створюємо нові питання
        if (examData.questions && examData.questions.length > 0) {
            for (const question of examData.questions) {
                await createQuestion(examId, question)
            }
        }
        
        return exam
    } catch (error) {
        console.error("API Error updating exam:", error)
        if (error.response?.data?.detail) {
            throw error
        }
        throw new Error('Не вдалося оновити іспит.')
    }
}