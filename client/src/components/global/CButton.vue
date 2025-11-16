<template>
    <button class="custom-button" :class="[variantClass]" :type="type" :disabled="disabled">
        <slot></slot>
    </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    type: {
        type: String,
        default: 'button'
    },
    disabled: {
        type: Boolean,
        default: false
    },
    variant: {
        type: String,
        default: 'default', // 'default', 'green', 'red', etc.
        validator: (value) => ['default', 'green', 'red'].includes(value)
    }
})

const variantClass = computed(() => {
    return `variant-${props.variant}`
})

</script>

<style scoped>
.custom-button {
    display: inline-flex;
    padding: 20px 40px;
    justify-content: center;
    align-items: center;
    gap: 10px;
    border-radius: 40px;
    border: none;
    background: var(--color-violet);
    color: var(--color-white);
    font-weight: bold;
    text-align: center;
    transition: all 150ms ease;
}

.custom-button:hover {
    background-color: var(--color-purple);
    cursor: pointer;
}

.custom-button:focus-visible {
    outline: 3px solid var(--color-purple);
    outline-offset: 2px;
}

.custom-button:disabled {
  background-color: var(--color-gray);
  color: var(--color-dark-gray);
  cursor: not-allowed;
}

.custom-button.variant-green {
    background: var(--color-green);
}

.custom-button.variant-green:hover:not(:disabled) {
    background-color: var(--color-green-dark, #2d8a47);
}

.custom-button.variant-green:focus-visible {
    outline: 3px solid var(--color-green);
    outline-offset: 2px;
}

.custom-button.variant-red {
    background: var(--color-red);
}

.custom-button.variant-red:hover:not(:disabled) {
    background-color: var(--color-red-dark, #c92a2a);
}

.custom-button.variant-red:focus-visible {
    outline: 3px solid var(--color-red);
    outline-offset: 2px;
}
</style>