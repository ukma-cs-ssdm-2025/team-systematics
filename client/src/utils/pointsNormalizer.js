/**
 * Нормалізує бали питань так, щоб їхня сума дорівнювала точно 100.
 * Використовує метод найбільшого залишку (largest remainder method),
 * щоб гарантувати точну суму без округлень.
 * 
 * @param {Array} questions - Масив питань з полем points
 * @returns {Array} - Масив питань з нормалізованими балами
 */
export function normalizeQuestionPoints(questions) {
    if (!questions || questions.length === 0) {
        return questions
    }

    // Створюємо мапу з початковими значеннями
    const pointsMap = new Map()
    for (let index = 0; index < questions.length; index++) {
        const q = questions[index]
        pointsMap.set(index, q.points || 1)
    }

    // Розраховуємо суму початкових балів
    const totalPoints = Array.from(pointsMap.values()).reduce((sum, val) => sum + (val || 1), 0)
    
    // Якщо сума вже 100, повертаємо як є
    if (totalPoints === 100) {
        return questions
    }

    // Розраховуємо коефіцієнт масштабування
    const scaleFactor = 100 / totalPoints

    // Створюємо структуру для сортування з заокругленими значеннями та залишками
    const processedItems = []
    for (const [index, value] of pointsMap) {
        const scaledValue = value * scaleFactor
        const floorValue = Math.floor(scaledValue)
        const fractionalPart = scaledValue - floorValue
        processedItems.push({
            index,
            floorValue,
            fractional: fractionalPart,
            originalValue: value
        })
    }

    // Розраховуємо різницю між 100 та сумою заокруглених значень
    const currentTotal = processedItems.reduce((sum, item) => sum + item.floorValue, 0)
    const difference = 100 - currentTotal

    // Сортуємо за спаданням дробової частини
    processedItems.sort((a, b) => b.fractional - a.fractional)

    // Створюємо фінальну мапу з початковими заокругленими значеннями
    const finalValuesMap = new Map()
    for (const item of processedItems) {
        finalValuesMap.set(item.index, item.floorValue)
    }

    // Розподіляємо "загублені" бали між елементами з найбільшим залишком
    for (let i = 0; i < difference; i++) {
        if (i < processedItems.length) {
            const itemIndex = processedItems[i].index
            finalValuesMap.set(itemIndex, finalValuesMap.get(itemIndex) + 1)
        }
    }

    // Оновлюємо бали в питаннях
    const normalizedQuestions = questions.map((q, index) => ({
        ...q,
        points: finalValuesMap.get(index) || 1
    }))

    return normalizedQuestions
}

