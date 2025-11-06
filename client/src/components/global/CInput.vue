<template>
  <input
    class="custom-input"
    :value="modelValue"
    @input="$emit('update:modelValue', $event.target.value)"
    :disabled="disabled"
  />
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: ''
  },
    disabled: {
    type: Boolean,
    default: false
  },
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.custom-input {
  width: 100%;
  padding: 20px;
  background-color: var(--color-gray);
  border: 3px solid var(--color-gray);
  border-radius: 12px;
  font-family: inherit;
  font-size: inherit;
  transition: all 150ms ease;
  box-shadow: none;
  line-height: 1.5;
}

.custom-input:hover {
  border-color: var(--color-dark-gray);
}

.custom-input:focus-visible {
  outline: 3px solid var(--color-purple);
  outline-offset: 2px;
}

.disabled {
    cursor: not-allowed;
}
</style>