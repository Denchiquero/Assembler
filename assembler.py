import json
import sys
import os


class Assembler:
    # Коды операций из спецификации
    OPCODES = {
        'load_const': 56,
        'write_mem': 54,
        'not': 59,
        'read_mem': 62
    }

    def __init__(self):
        self.program = []

    def assemble(self, input_file, output_file, test_mode=False):

        # Чтение и парсинг JSON
        with open(input_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                return False

        # Проверяем структуру данных
        if not isinstance(data, list):
            print("Error: command list expected")
            return False

        # Трансляция команд
        for i, cmd in enumerate(data):
            if not self._translate_command(cmd, i):
                return False

        # В режиме тестирования внутреннее представление
        if test_mode:
            self._print_internal_representation()

        # Промежуточное представление
        self._save_intermediate(output_file)

        return True

    def _translate_command(self, cmd, line_num):

        if 'opcode' not in cmd:
            print(f"Error in line {line_num}: opcode is missing")
            return False

        opcode = cmd['opcode']

        if opcode == 'load_const':
            return self._translate_load_const(cmd, line_num)
        elif opcode == 'read_mem':
            return self._translate_read_mem(cmd, line_num)
        elif opcode == 'write_mem':
            return self._translate_write_mem(cmd, line_num)
        elif opcode == 'not':
            return self._translate_not(cmd, line_num)
        else:
            print(f"Error in line {line_num}: unknown opcode '{opcode}'")
            return False

    def _translate_load_const(self, cmd, line_num):

        required = ['dest_reg', 'value']
        if not all(field in cmd for field in required):
            print(f"Error in line {line_num}: command load_const requires {required}")
            return False

        # Проверка диапазонов
        if not (0 <= cmd['dest_reg'] <= 127):
            print(f"Error in line {line_num}: dest_reg must be between 0-127")
            return False

        if not (0 <= cmd['value'] <= 0x1FFFFFF):  # 25 бит
            print(f"Error in line {line_num}: value must be between 0-{0x1FFFFFF}")
            return False

        self.program.append({
            'opcode': 'load_const',
            'A': self.OPCODES['load_const'],
            'B': cmd['dest_reg'],
            'C': cmd['value']
        })
        return True

    def _translate_read_mem(self, cmd, line_num):

        required = ['src_reg', 'dest_reg']
        if not all(field in cmd for field in required):
            print(f"Error in line {line_num}: command read_mem requires {required}")
            return False

        # Проверка диапазонов
        if not (0 <= cmd['src_reg'] <= 127):
            print(f"Error in line {line_num}: src_reg must be between 0-127")
            return False

        if not (0 <= cmd['dest_reg'] <= 127):
            print(f"Error in line {line_num}: dest_reg must be between 0-127")
            return False

        self.program.append({
            'opcode': 'read_mem',
            'A': self.OPCODES['read_mem'],
            'B': cmd['src_reg'],
            'C': cmd['dest_reg']
        })
        return True

    def _translate_write_mem(self, cmd, line_num):

        required = ['src_reg', 'dest_addr']
        if not all(field in cmd for field in required):
            print(f"Error in line {line_num}: command write_mem requires {required}")
            return False

        # Проверка диапазонов
        if not (0 <= cmd['src_reg'] <= 127):
            print(f"Error in line {line_num}: src_reg must be between 0-127")
            return False

        if not (0 <= cmd['dest_addr'] <= 0x1FFF):  # 13 бит
            print(f"Error in line {line_num}: dest_addr must be between 0-{0x1FFF}")
            return False

        self.program.append({
            'opcode': 'write_mem',
            'A': self.OPCODES['write_mem'],
            'B': cmd['src_reg'],
            'C': cmd['dest_addr']
        })
        return True

    def _translate_not(self, cmd, line_num):

        required = ['src_reg', 'dest_addr']
        if not all(field in cmd for field in required):
            print(f"Error in line {line_num}: command not requires {required}")
            return False

        # Проверка диапазонов
        if not (0 <= cmd['src_reg'] <= 127):
            print(f"Error in line {line_num}: src_reg must be between 0-127")
            return False

        if not (0 <= cmd['dest_addr'] <= 0x1FFF):  # 13 бит
            print(f"Error in line {line_num}: dest_addr must be between 0-{0x1FFF}")
            return False

        self.program.append({
            'opcode': 'not',
            'A': self.OPCODES['not'],
            'B': cmd['src_reg'],
            'C': cmd['dest_addr']
        })
        return True

    def _print_internal_representation(self):

        print("\nInternal representation:")
        print("-" * 40)
        for i, cmd in enumerate(self.program):
            print(f"Command {i}:")
            print(f"  Instruction: {cmd['opcode']}")
            print(f"  A: {cmd['A']} (0x{cmd['A']:02X})")
            print(f"  B: {cmd['B']} (0x{cmd['B']:02X})")
            print(f"  C: {cmd['C']} (0x{cmd['C']:02X})")
            print("-" * 40)

    def _save_intermediate(self, output_file):

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.program, f, indent=2, ensure_ascii=False)


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


def main():

    if len(sys.argv) < 3:
        print("Usage: python assembler.py <input_file> <output_file> [--test]")
        print("Example: python assembler.py program.json intermediate.json --test")
        print("\nFor creating test files: python assembler.py --create-tests")
        return

    if sys.argv[1] == '--create-tests':
        create_test_files()
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