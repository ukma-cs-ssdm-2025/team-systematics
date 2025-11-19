<template>
    <span v-html="highlightedText"></span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    text: {
        type: String,
        required: true
    },
    ranges: {
        type: Array,
        default: () => []
    }
})

const highlightedText = computed(() => {
    if (!props.ranges || props.ranges.length === 0) {
        return escapeHtml(props.text)
    }
    
    // Сортуємо ranges за start позицією
    const sortedRanges = [...props.ranges].sort((a, b) => a.start - b.start)
    
    // Об'єднуємо перекриваючі ranges
    const mergedRanges = []
    for (const range of sortedRanges) {
        const start = Math.max(0, Math.min(range.start, props.text.length))
        const end = Math.max(start, Math.min(range.end || range.start, props.text.length))
        
        if (mergedRanges.length === 0) {
            mergedRanges.push({ start, end })
        } else {
            const lastRange = mergedRanges[mergedRanges.length - 1]
            if (start <= lastRange.end) {
                // Перекриваються - об'єднуємо
                lastRange.end = Math.max(lastRange.end, end)
            } else {
                // Не перекриваються - додаємо новий
                mergedRanges.push({ start, end })
            }
        }
    }
    
    // Створюємо HTML з виділенням
    let result = ''
    let lastIndex = 0
    
    for (const range of mergedRanges) {
        // Додаємо текст до початку виділення
        result += escapeHtml(props.text.slice(lastIndex, range.start))
        
        // Додаємо виділений текст
        result += `<mark class="plagiarism-highlight">${escapeHtml(props.text.slice(range.start, range.end))}</mark>`
        
        lastIndex = range.end
    }
    
    // Додаємо решту тексту після останнього виділення
    result += escapeHtml(props.text.slice(lastIndex))
    
    return result
})

function escapeHtml(text) {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
}
</script>

<style scoped>
:deep(.plagiarism-highlight) {
    background-color: #ffeb3b;
    padding: 2px 0;
    border-radius: 2px;
    font-weight: 500;
}
</style>

