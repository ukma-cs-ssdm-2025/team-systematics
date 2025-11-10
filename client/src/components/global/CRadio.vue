<template>
    <label class="option-item" :class="{ 'selected': isChecked, 'is-disabled': disabled }">
        <!-- 1. Справжня радіокнопка -->
        <input type="radio" class="real-radio-button" :name="name" :value="value" :checked="isChecked"
            :disabled="disabled" @change="$emit('update:modelValue', value)" />

        <!-- 2. Бейдж, який ми стилізуємо -->
        <div class="letter-badge" aria-hidden="true">
            {{ badgeContent }}
        </div>
    </label>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
    modelValue: { type: [String, Number, null] },
    value: { type: [String, Number], required: true },
    name: { type: String, required: true },
    disabled: { type: Boolean, default: false },
    badgeContent: { type: [String, Number], default: '' }
});

defineEmits(['update:modelValue']);

const isChecked = computed(() => props.modelValue === props.value);
</script>

<style scoped>
.option-item {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
}

.real-radio-button {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
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
    background-color: var(--cr-selected-bg, var(--color-purple));
    color: var(--cr-selected-text, var(--color-white));
}

.option-item:has(.real-radio-button:focus-visible) {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.option-item.is-disabled {
    cursor: not-allowed;
}
</style>