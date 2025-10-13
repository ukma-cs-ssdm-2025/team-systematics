<template>
    <div class="question-block">
        <textarea class="textarea-input" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)"
            placeholder="Введіть вашу відповідь..."></textarea>
    </div>
</template>

<script setup>
defineProps({
    modelValue: {
        type: String,
        default: ''
    }
});

defineEmits(['update:modelValue'])
</script>

<style scoped>
.question-block {
    width: 60%;
    height: 400px;
    margin-bottom: 20px;
}

.textarea-input {
    height: 100%;
    width: 100%;
    padding: 20px;
    background-color: var(--color-gray);
    border: 3px solid var(--color-gray);
    border-radius: 12px;
    font-family: inherit;
    font-size: inherit;
    transition: all 150ms ease;
    box-shadow: none;
    resize: none;
    line-height: 1.5;
}

.textarea-input:hover {
    border-color: var(--color-dark-gray);
}

.textarea-input:focus-visible {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}
</style>