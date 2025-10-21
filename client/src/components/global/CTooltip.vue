<template>
  <div 
    class="tooltip-container" 
    @mouseenter="showTooltip" 
    @mouseleave="hideTooltip"
  >
    <!-- Елемент, який викликає підказку (напр., іконка) -->
    <slot name="trigger"></slot>
    
    <!-- Сама підказка -->
    <div 
      ref="tooltipRef" 
      class="tooltip-text" 
      :class="{ visible: isVisible }"
    >
      <slot name="content"></slot>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const tooltipRef = ref(null)
const isVisible = ref(false)

async function showTooltip() {
  isVisible.value = true
  
  // nextTick чекає, поки Vue оновить DOM і зробить тултіп видимим
  await nextTick()
  
  const tooltipEl = tooltipRef.value
  if (!tooltipEl) return
  
  // Отримуємо "коробку" з розмірами та позицією тултіпа
  const rect = tooltipEl.getBoundingClientRect()
  
  // Перевіряємо, чи виходить тултіп за лівий або правий край екрану
  if (rect.left < 0) {
    // Якщо виходить зліва, "притискаємо" його до лівого краю
    tooltipEl.style.left = '0'
    tooltipEl.style.transform = 'translateX(0)'
  } else if (rect.right > window.innerWidth) {
    // Якщо виходить справа, "притискаємо" до правого
    tooltipEl.style.left = 'auto'
    tooltipEl.style.right = '0'
    tooltipEl.style.transform = 'translateX(0)'
  }
}

function hideTooltip() {
  isVisible.value = false
  
  const tooltipEl = tooltipRef.value
  if (!tooltipEl) return;
  
  tooltipEl.style.left = '50%'
  tooltipEl.style.right = 'auto'
  tooltipEl.style.transform = 'translateX(-50%)'
}
</script>

<style scoped>
.tooltip-container {
  position: relative;
  display: inline-block;
}

.tooltip-text {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  z-index: 10;
  bottom: 125%; 
  left: 50%;
  transform: translateX(-50%); 
  

  width: 400px;
  background-color: #f0f0f0;
  padding: 15px;
  border-radius: 10px;
  border: 2px solid var(--color-orange);
  
  transition: opacity 0.3s, visibility 0.3s;
  pointer-events: none; 
}

.tooltip-text::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border-width: 8px;
  border-style: solid;
  border-color: var(--color-orange) transparent transparent transparent;
}

.tooltip-text.visible {
  visibility: visible;
  opacity: 1;
}
</style>