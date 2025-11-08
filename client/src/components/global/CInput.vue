<template>
  <input
    class="custom-input"
    :value="displayValue"
    @input="handleInput"
    @keydown="handleKeydown"
    :disabled="disabled"
    :type="type"
    :min="min"
    :max="max"
    :id="id"
    :placeholder="placeholder"
    :required="required"
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'text'
  },
  min: {
    type: [String, Number],
    default: undefined
  },
  max: {
    type: [String, Number],
    default: undefined
  },
  id: {
    type: String,
    default: undefined
  },
  placeholder: {
    type: String,
    default: undefined
  },
  required: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

// Конвертуємо modelValue в рядок для відображення
const displayValue = computed(() => {
  if (props.modelValue === null || props.modelValue === undefined) {
    return ''
  }
  return String(props.modelValue)
})

// Обробник зміни значення
function handleInput(event) {
  const value = event.target.value
  if (props.type === 'number') {
    // Для number типів конвертуємо в число, якщо значення не порожнє
    if (value === '') {
      emit('update:modelValue', '')
    } else {
      const numValue = Number(value)
      emit('update:modelValue', isNaN(numValue) ? value : numValue)
    }
  } else {
    emit('update:modelValue', value)
  }
}

// Блокуємо введення нечислових символів та мінуса для числових полів
function handleKeydown(event) {
  if (props.type === 'number') {
    const key = event.key
    
    // Дозволяємо: цифри, Backspace, Delete, Tab, Escape, Enter, стрілки
    const allowedKeys = ['Backspace', 'Delete', 'Tab', 'Escape', 'Enter', 
                         'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
                         'Home', 'End']
    
    if (allowedKeys.includes(key)) {
      return true
    }
    
    // Дозволяємо Ctrl/Cmd + A, C, V, X (вибір, копіювання, вставка, вирізання)
    if (event.ctrlKey || event.metaKey) {
      if (['a', 'c', 'v', 'x'].includes(key.toLowerCase())) {
        return true
      }
    }
    
    // Блокуємо всі інші символи, крім цифр
    if (!/^[0-9]$/.test(key)) {
      event.preventDefault()
      return false
    }
  }
}
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