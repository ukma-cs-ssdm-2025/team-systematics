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
</style>