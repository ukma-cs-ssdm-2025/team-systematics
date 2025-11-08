<template>
    <select
        class="custom-select"
        :value="modelValue"
        @change="$emit('update:modelValue', $event.target.value)"
        :disabled="disabled"
    >
        <option disabled value="">{{ placeholder }}</option>
        <option v-for="option in options" :key="option.value" :value="option.value">
            {{ option.text }}
        </option>
    </select>
</template>

<script setup>
defineProps({
    modelValue: {
        type: [String, Number, null],
        default: ''
    },
    options: {
        type: Array,
        required: true,
        validator: (value) => value.every(opt => 'value' in opt && 'text' in opt)
    },
    placeholder: {
        type: String,
        default: 'Виберіть зі списку...'
    },
    disabled: {
        type: Boolean,
        default: false
    }
});

defineEmits(['update:modelValue']);
</script>

<style scoped>
.custom-select {
    display: flex;
    align-items: center;
    width: 100%;
    height: 100%;
    min-height: 50px;
    padding: 0 16px;
    border: 2px solid var(--color-gray);
    border-radius: 8px;
    background-color: white;
    font-family: inherit;
    font-size: inherit;
    transition: all 150ms ease;

    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml,%3csvg xmlns='http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c%2Fsvg%3e");
    background-position: right 16px center;
    background-repeat: no-repeat;
    background-size: 24px;
}

.custom-select:hover {
    border-color: var(--color-dark-gray);
}

.custom-select:focus-visible {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.custom-select:disabled {
    cursor: not-allowed;
}
</style>