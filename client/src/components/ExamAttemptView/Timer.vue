<template>
    <div class="timer-container" :class="{ 'warning-time': isWarningTime }">
        <svg class="timer-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path
                d="M12 2C6.486 2 2 6.486 2 12s4.486 10 10 10 10-4.486 10-10S17.514 2 12 2zm0 18c-4.411 0-8-3.589-8-8s3.589-8 8-8 8 3.589 8 8-3.589 8-8 8z">
            </path>
            <path d="M13 7h-2v5.414l3.293 3.293 1.414-1.414L13 11.586z"></path>
        </svg>
        <div class="time-display">
            {{ formattedTime }}
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
    durationMinutes: {
        type: Number,
        required: true,
        validator: (value) => value > 0
    }
})

const emit = defineEmits(['time-up'])
const remainingSeconds = ref(0)
const timerId = ref(null)

// Форматує залишок секунд у вигляд "ГГ:ХХ:ХХ" або "ХХ:ХХ"
const formattedTime = computed(() => {
    const totalSeconds = remainingSeconds.value

    // Якщо часу залишилося менше години
    if (totalSeconds < 3600) {
        const minutes = Math.floor(totalSeconds / 60)
        const seconds = totalSeconds % 60

        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }
    // Якщо часу залишилося година або більше
    else {
        const hours = Math.floor(totalSeconds / 3600)
        const minutes = Math.floor((totalSeconds % 3600) / 60)
        const seconds = totalSeconds % 60

        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }
});

// Вмикає "режим попередження", якщо залишилось 5 хвилин або менше
const isWarningTime = computed(() => remainingSeconds.value <= 300)

function startTimer() {
    remainingSeconds.value = props.durationMinutes * 60

    // Створюємо інтервал, який буде спрацьовувати кожну секунду (1000 мс)
    timerId.value = setInterval(() => {
        // Зменшуємо лічильник
        remainingSeconds.value--

        if (remainingSeconds.value <= 0) {
            clearInterval(timerId.value)
            remainingSeconds.value = 0
            emit('time-up')
        }
    }, 1000)
}

onMounted(() => {
    startTimer()
})

onUnmounted(() => {
    if (timerId.value) {
        clearInterval(timerId.value);
    }
});
</script>

<style scoped>
.timer-container {
    display: inline-flex;
    align-items: center;
    justify-items: center;
    gap: 4px;
    background-color: var(--color-red);
    padding: 12px;
    border-radius: 20px;
    border: 2px solid transparent;
    transition: all 0.3s ease;
}

.timer-icon {
    width: 24px;
    height: 24px;
    margin-bottom: 2px;
    color: var(--color-black);
}

.timer-container.warning-time {
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.05);
    }

    100% {
        transform: scale(1);
    }
}
</style>