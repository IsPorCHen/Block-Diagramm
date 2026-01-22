def check_number(x):
    if x > 0:
        print("Положительное")
    elif x < 0:
        print("Отрицательное")
    else:
        print("Ноль")

number = int(input("Введите число: "))
check_number(number)