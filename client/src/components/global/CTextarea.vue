<template>
  <textarea
    class="custom-textarea"
    :value="modelValue"
    @input="$emit('update:modelValue', $event.target.value)"
    :disabled="disabled"
  ></textarea>
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
.custom-textarea {
  width: 100%;
  min-height: 150px;
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

.custom-textarea:hover {
  border-color: var(--color-dark-gray);
}

.custom-textarea:focus-visible {
  outline: 3px solid var(--color-purple);
  outline-offset: 2px;
}

.disabled {
    cursor: not-allowed;
}
</style>