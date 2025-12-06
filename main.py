import sys
import os
import json
from assembler import Assembler
from interpreter import Interpreter

def create_test_files():

    # Тест 1: Загрузка константы (A=56, B=47, C=435)
    test1 = [
        {"opcode": "load_const", "dest_reg": 47, "value": 435}
    ]

    # Тест 2: Чтение из памяти (A=62, B=111, C=117)
    test2 = [
        {"opcode": "read_mem", "src_reg": 111, "dest_reg": 117}
    ]

    # Тест 3: Запись в память (A=54, B=45, C=298)
    test3 = [
        {"opcode": "write_mem", "src_reg": 45, "dest_addr": 298}
    ]

    # Тест 4: Побитовое НЕ (A=59, B=7, C=893)
    test4 = [
        {"opcode": "not", "src_reg": 7, "dest_addr": 893}
    ]

    # Сохраняем тестовые файлы
    tests = {
        "test1.json": test1,
        "test2.json": test2,
        "test3.json": test3,
        "test4.json": test4
    }

    for filename, content in tests.items():
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"Test file created: {filename}")


def create_test_program():
    """Создание тестовой программы для копирования массива"""
    # Программа копирует массив из адреса 100 в адрес 200 (5 элементов)
    test_program = [
        # Инициализируем регистры с адресами
        {"opcode": "load_const", "dest_reg": 1, "value": 100},  # R1 = начальный адрес источника
        {"opcode": "load_const", "dest_reg": 2, "value": 200},  # R2 = начальный адрес назначения
        {"opcode": "load_const", "dest_reg": 3, "value": 5},  # R3 = количество элементов

        # Цикл копирования
        # 1. Читаем элемент из источника
        {"opcode": "read_mem", "src_reg": 1, "dest_reg": 10},  # R10 = M[R1]
        # 2. Записываем элемент в назначение
        {"opcode": "write_mem", "src_reg": 10, "dest_addr": 0},  # Временно используем C=0
        # Нужно исправить C на правильный адрес (будет заменено позже)

        # 3. Увеличиваем адреса
        {"opcode": "load_const", "dest_reg": 4, "value": 1},  # R4 = 1 (инкремент)
        # В реальной УВМ нужны команды сложения, но их нет в спецификации
        # Используем простой подход с предварительным вычислением

        # Завершение
        {"opcode": "load_const", "dest_reg": 0, "value": 0},  # Простая заглушка
    ]

    # Сохраняем тестовую программу
    with open("copy_array.json", 'w', encoding='utf-8') as f:
        json.dump(test_program, f, indent=2)

    print("Test program created: copy_array.json")
    return True


def verify_test_results():
    print("\n" + "=" * 60)
    print("VERIFICATION OF UVM SPECIFICATION TESTS")
    print("=" * 60)

    tests = [
        ("test1.json", "load_const", [0xF8, 0x6B, 0x36, 0x00, 0x00]),
        ("test2.json", "read_mem", [0xFE, 0xBB, 0x0E, 0x00, 0x00]),
        ("test3.json", "write_mem", [0x76, 0x4B, 0x25, 0x00, 0x00]),
        ("test4.json", "not", [0xFB, 0xA1, 0x6F, 0x00, 0x00])
    ]

    all_passed = True

    for test_file, cmd_name, expected_bytes in tests:
        if not os.path.exists(test_file):
            print(f"File {test_file} not found!")
            print("Run 'python assembler.py --create-tests' first")
            all_passed = False
            continue

        print(f"\nTesting {cmd_name}...")

        # Запускаем ассемблер
        assembler = Assembler()
        binary_file = test_file.replace('.json', '.bin')

        if assembler.assemble(test_file, binary_file, test_mode=False):
            # Читаем сгенерированные байты
            with open(binary_file, 'rb') as f:
                generated_bytes = list(f.read())

            # Сравниваем
            if generated_bytes == expected_bytes:
                print(f"  MATCH!")
                print(f"  Bytes: {[f'0x{b:02X}' for b in generated_bytes]}")
            else:
                print(f"  NO MATCH!")
                print(f"  Expected: {[f'0x{b:02X}' for b in expected_bytes]}")
                print(f"  Got:      {[f'0x{b:02X}' for b in generated_bytes]}")
                all_passed = False

            # Удаляем временный файл
            if os.path.exists(binary_file):
                os.remove(binary_file)
        else:
            print(f"  Assembly error for {test_file}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED")
        print("   This might be due to specification errors")
    print("=" * 60)

    return all_passed


def interpreter_main():
    """Основная функция интерпретатора"""
    if len(sys.argv) < 5:
        print("Usage: python assembler.py --run <binary_file> <dump_file> <start_addr> <end_addr>")
        print("Example: python assembler.py --run program.bin dump.xml 0 100")
        return

    binary_file = sys.argv[2]
    dump_file = sys.argv[3]
    start_addr = int(sys.argv[4])
    end_addr = int(sys.argv[5])

    if not os.path.exists(binary_file):
        print(f"Error: binary file {binary_file} not found")
        return

    # Создаем и запускаем интерпретатор
    interpreter = Interpreter()

    # Загружаем программу
    if not interpreter.load_program(binary_file):
        return

    # Запускаем выполнение
    interpreter.run()

    # Сохраняем дамп памяти
    interpreter.save_memory_dump(dump_file, start_addr, end_addr)

    # Выводим состояние регистров
    print("\nRegister state (non-zero):")
    for i, val in enumerate(interpreter.registers):
        if val != 0:
            print(f"  R[{i}] = {val} (0x{val:X})")


def main():
    if len(sys.argv) < 2:
        print("Usage options:")
        print("  Assembler: python assembler.py <input_file> <output_file> [--test]")
        print("  Interpreter: python assembler.py --run <binary_file> <dump_file> <start_addr> <end_addr>")
        print("  Test creation: python assembler.py --create-tests")
        print("  Test verification: python assembler.py --verify-tests")
        print("  Create array copy test: python assembler.py --create-copy-test")
        print("\nExamples:")
        print("  python assembler.py program.json program.bin --test")
        print("  python assembler.py --run program.bin dump.xml 0 100")
        print("  python assembler.py --create-copy-test")
        return

    if sys.argv[1] == '--create-tests':
        create_test_files()
        return

    if sys.argv[1] == '--verify-tests':
        verify_test_results()
        return

    if sys.argv[1] == '--create-copy-test':
        create_test_program()
        return

    if sys.argv[1] == '--run':
        interpreter_main()
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    test_mode = '--test' in sys.argv

    # Проверка существования входного файла
    if not os.path.exists(input_file):
        print(f"Error: file {input_file} not found")
        return

    # Создание и запуск ассемблера
    assembler = Assembler()

    if assembler.assemble(input_file, output_file, test_mode):
        print(f"Assembly complete!")
        print(f"Result is saved in {output_file}")
        if test_mode:
            print(f"Command assembly: {len(assembler.program)}")
    else:
        print("Assembly complete with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()