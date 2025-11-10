<template>
    <label class="option-item" :class="{ 'selected': modelValue, 'is-disabled': disabled }">
        <input type="checkbox" class="real-checkbox" :checked="modelValue" :disabled="disabled"
            :aria-label="title || 'Checkbox'"
            @change="$emit('update:modelValue', $event.target.checked)" />
        <div class="custom-checkbox" aria-hidden="true">
            <svg v-if="modelValue" xmlns="http://www.w3.org/2000/svg" width="17" height="13" viewBox="0 0 17 13"
                fill="none">
                <path d="M5.7 12.025L0 6.325L1.425 4.9L5.7 9.175L14.875 0L16.3 1.425L5.7 12.025Z" />
            </svg>
        </div>
    </label>
</template>

<script setup>
defineProps({
    modelValue: { type: Boolean, default: false },
    disabled: { type: Boolean, default: false },
    title: { type: String, default: '' }
});
defineEmits(['update:modelValue']);
</script>

<style scoped>
.option-item {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
}

.real-checkbox {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
}

.custom-checkbox {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 4px;
    background-color: var(--color-gray);
    transition: all 150ms ease;
}

.custom-checkbox svg path {
    fill: var(--cc-icon-fill, var(--color-black));
}

.option-item:has(.real-checkbox:focus-visible) {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.option-item.is-disabled {
    cursor: not-allowed;
}

.option-item.is-disabled:hover {
    border-color: var(--color-gray);
}
</style>