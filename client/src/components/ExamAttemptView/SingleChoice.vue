<template>
    <div class="question-block">
        <ol class="single-choice-list">
            <li v-for="(option, i) in options" :key="option.id">
                <label 
                    class="option-item" 
                    :class="{ 'selected': modelValue === option.id }"
                >
                    <!-- 1. Справжня радіокнопка, яку повністю приховаємо -->
                    <input 
                        type="radio"
                        class="real-radio-button"
                        :name="uniqueGroupName"
                        :value="option.id"
                        :checked="modelValue === option.id"
                        @change="$emit('update:modelValue', option.id)"
                    />
                    
                    <!-- 2. Бейдж з літерою, який тепер виконує роль кастомної кнопки -->
                    <div class="letter-badge" aria-hidden="true">
                        {{ letter(i) }}
                    </div>

                    <!-- 3. Текст варіанту відповіді -->
                    <span class="option-text">{{ option.text }}</span>
                </label>
            </li>
        </ol>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    options: { type: Array, required: true },
    modelValue: { type: [String, Number], default: null }
})

defineEmits(['update:modelValue'])

// Генеруємо унікальне ім'я для групи радіокнопок, щоб вони працювали коректно
const uniqueGroupName = computed(() => `group-${Math.random()}`)

// Функція для генерації літер A, B, C...
const letter = (index) => String.fromCharCode(65 + index)
</script>

<style scoped>
.question-block {
    width: 60%;
}

.single-choice-list li {
    list-style: none;
}

.option-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border: 3px solid var(--color-gray);
    border-radius: 12px;
    cursor: pointer;
    transition: all 150ms ease;
}

.option-item:hover {
    border-color: var(--color-dark-gray);
}

.option-item.selected {
    border-color: var(--color-purple);
    background-color: var(--color-lavender);
}

.real-radio-button {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
    cursor: pointer;
}

.letter-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: var(--color-gray);
    color: var(--color-black);
    font-weight: bold;
    transition: all 150ms ease;
}

.option-item.selected .letter-badge {
    background-color: var(--color-purple);
    color: white;
}
</style>