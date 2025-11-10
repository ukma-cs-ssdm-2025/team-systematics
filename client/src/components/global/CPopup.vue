<template>
    <div v-if="visible" class="popup-overlay" @click.self="$emit('sndAction')">
        <div class="popup-container">
            <div class="popup-header">
                {{ header }}
            </div>
            <div class="popup-disclaimer">
                {{ disclaimer }}
            </div>
            <div class="buttons-container">
                <CButton class="fst-button" :variant="fstButtonVariant" @click="$emit('fstAction')"> {{ fstButton }}</CButton>
                <CButton class="snd-button" :variant="sndButtonVariant" @click="$emit('sndAction')"> {{ sndButton }}</CButton>
            </div>
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
    sndButton: { type: String, default: 'Скасувати' },
    fstButtonVariant: { type: String, default: 'default' },
    sndButtonVariant: { type: String, default: 'default' }
})

defineEmits(['fstAction', 'sndAction'])

</script>

<style scoped>
.popup-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

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
    gap: 20px;
}

.popup-header {
    font-weight: bold;
    font-size: 1.2rem;
}
</style>