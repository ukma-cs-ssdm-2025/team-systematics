<template>
    <div class="selector-container">
        <CSelect
            v-model="selectedType"
            :options="questionTypeOptions"
            placeholder="Виберіть тип питання..."
        />
        
        <CButton type="button" @click="addQuestion" :disabled="!selectedType" class="add-btn">
            Додати
        </CButton>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import CButton from '../../components/global/CButton.vue'
import CSelect from '../../components/global/CSelect.vue'

const emit = defineEmits(['add-question'])

const selectedType = ref('')

const questionTypeOptions = [
    { value: 'single_choice', text: 'Одиночний вибір' },
    { value: 'multi_choice', text: 'Множинний вибір' },
    { value: 'short_answer', text: 'Коротка відповідь' },
    { value: 'long_answer', text: 'Розгорнута відповідь' },
    { value: 'matching', text: 'Встановлення відповідності' },
]

function addQuestion() {
    if (selectedType.value) {
        emit('add-question', selectedType.value)
        selectedType.value = ''
    }
}
</script>

<style scoped>
.selector-container {
    display: flex;
    align-items: center; /* Додано для кращого вирівнювання по вертикалі */
    gap: 16px;
    margin-bottom: 32px;
}
</style>