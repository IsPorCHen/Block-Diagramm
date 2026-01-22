"""
Тестовый файл для проверки генератора блок-схем
Содержит: классы, функции, ветвления, циклы, try/except
"""


class Calculator:
    """Класс калькулятора"""
    
    def __init__(self, name):
        self.name = name
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(result)
        return result
    
    def divide(self, a, b):
        if b == 0:
            return None
        else:
            return a / b


def find_max_number(numbers):
    """Поиск максимального числа"""
    if not numbers:
        return None
    
    max_num = numbers[0]
    
    for num in numbers:
        if num > max_num:
            max_num = num
    
    return max_num


def safe_divide(a, b):
    """Деление с обработкой ошибок"""
    try:
        result = a / b
        print("Результат:", result)
        return result
    except ZeroDivisionError as e:
        print("Ошибка: деление на ноль")
        return None
    except TypeError:
        print("Ошибка типа данных")
        return None


def factorial(n):
    """Вычисление факториала"""
    result = 1
    i = 1
    
    while i <= n:
        result = result * i
        i = i + 1
    
    return result


# Основная программа
numbers = [45, 23, 78, 12, 90, 34, 56]
print("Список чисел:", numbers)

max_result = find_max_number(numbers)
print("Максимум:", max_result)

calc = Calculator("Мой калькулятор")
sum_result = calc.add(10, 20)
print("Сумма:", sum_result)
