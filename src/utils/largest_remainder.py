import math
from typing import Dict, Any, List

def distribute_largest_remainder(
    items_with_values: Dict[Any, float], 
    target_total: int = 100
) -> Dict[Any, int]:
    """
    Розподіляє цілі числа, зберігаючи задану суму, за методом найбільшого залишку.

    Ця функція вирішує проблему, коли сума заокруглених чисел не дорівнює
    заокругленій сумі. Вона гарантує, що сума фінальних цілих значень
    буде точно дорівнювати `target_total`.

    Принцип роботи:
    1. Усі значення заокруглюються вниз до найближчого цілого.
    2. Розраховується різниця між `target_total` і сумою заокруглених значень.
    3. Ця різниця (залишок) розподіляється по одному балу між елементами,
       які мали найбільшу дробову частину.

    Args:
        items_with_values (Dict[Any, float]): Словник, де ключі - це унікальні
            ідентифікатори (напр. UUID питання), а значення - це початкові
            дробові числа (напр. розраховані бали).
        target_total (int): Цільова сума, до якої має дорівнювати сума
            фінальних значень. За замовчуванням 100.

    Returns:
        Dict[Any, int]: Словник з тими ж ключами, але зі скоригованими цілими
            значеннями, сума яких дорівнює `target_total`.
    """
    if not items_with_values:
        return {}

    # 1. Створюємо структуру для сортування, зберігаючи ID, заокруглене значення та залишок
    processed_items = []
    for item_id, value in items_with_values.items():
        floor_value = math.floor(value)
        fractional_part = value - floor_value
        processed_items.append({
            "id": item_id,
            "floor_value": floor_value,
            "fractional": fractional_part
        })

    # 2. Розраховуємо, скільки балів "загубилося" при заокругленні вниз
    current_total = sum(item['floor_value'] for item in processed_items)
    difference = target_total - current_total
    
    # 3. Сортуємо елементи за спаданням їхньої дробової частини
    processed_items.sort(key=lambda x: x['fractional'], reverse=True)
    
    # 4. Створюємо фінальну мапу з початковими заокругленими значеннями
    final_values_map = {item['id']: item['floor_value'] for item in processed_items}
    
    # 5. Розподіляємо "загублені" бали між елементами з найбільшим залишком
    for i in range(difference):
        if i < len(processed_items):
            item_id_to_increment = processed_items[i]['id']
            final_values_map[item_id_to_increment] += 1
            
    return final_values_map