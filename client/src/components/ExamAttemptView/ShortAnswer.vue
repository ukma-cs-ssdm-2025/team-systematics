<template>
    <div class="question-block">
        <input 
            :type="inputType"
            class="text-input"
            :value="modelValue"
            @input="handleInput"
            :placeholder="inputType === 'text' ? 'Введіть вашу відповідь...' : 'Введіть число...'"
        />
    </div>
</template>

<script setup>
defineProps({
    modelValue: { 
        type: String, 
        default: '' 
    },
    inputType: {
        type: String,
        default: 'text', // За замовчуванням - текстове поле
        validator: (value) => ['text', 'number'].includes(value) // Дозволяємо тільки 'text' або 'number'
    }
});

const emit = defineEmits(['update:modelValue'])

function handleInput(event) {
    let value = event.target.value
    if (props.inputType === 'number') {
        const parsedValue = parseFloat(value)
        if (value.trim() !== '' && !isNaN(parsedValue)) {
            value = parsedValue
        }
    }
    emit('update:modelValue', value)
}
</script>

<style scoped>
.question-block {
    width: 60%;
    margin-bottom: 20px;
}

.text-input {
    width: 40%;
    padding: 20px;
    background-color: var(--color-gray);
    border: 3px solid var(--color-gray);
    border-radius: 12px;;
    font-family: inherit;
    font-size: inerhit;
    transition: all 150ms ease;
    box-shadow: none;
}

.text-input:hover {
    border-color: var(--color-dark-gray);
}

.text-input:focus-visible {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px; 
}
</style>