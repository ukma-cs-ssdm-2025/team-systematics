<template>
    <button class="custom-button">
        <slot></slot>
    </button>
</template>

<style scoped>
.custom-button {
    display: inline-flex;
    padding: 20px 40px;
    justify-content: center;
    align-items: center;
    gap: 10px;
    border-radius: 40px;
    background: var(--color-violet);
    color: var(--color-white);
    font-weight: bold;
    text-align: center;
}

.custom-button:hover {
    background-color: var(--color-purple);
    cursor: pointer;
}

.custom-button:focus-visible {
    outline: 3px solid var(--color-dark-purple);
    outline-offset: 2px;
    /* Невеликий відступ рамки від елемента */
}
</style>