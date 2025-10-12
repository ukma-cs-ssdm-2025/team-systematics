<template>
    <div class="popup-container">
        <div class="popup-header">
            {{ header }}
        </div>
        <div class="popup-disclaimer">
            {{ disclaimer }}
        </div>
        <div class="buttons-container">
            <CButton class="fst-button" @click="$emit('fstAction')"> {{ fstButton }}</CButton>
            <CButton class="snd-button" @click="$emit('sndAction')"> {{ sndButton }}</CButton>
        </div>
    </div>
</template>

<script setup>
import CButton from '../global/CButton.vue'

defineProps({
    visible: { type: Boolean, default: false },
    header: { type: String, required: true },
    disclaimer: { type: String, required: true },
    fstButton: { type: String, default: 'Підтвердити' },
    sndButton: { type: String, default: 'Скасувати' }
})

defineEmits(['fstAction', 'sndAction'])

</script>

<style scoped>
.popup-container {
    display: flex;
    width: 40%;
    padding: 40px 80px;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 20px;
    border-radius: 40px;
    background: var(--color-white);
    box-shadow: 0 4px 4px 0 rgba(0, 0, 0, 0.25);
    text-align: center;
}

.buttons-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    align-self: stretch;
}

.popup-header {
    font-weight: bold;
}
</style>