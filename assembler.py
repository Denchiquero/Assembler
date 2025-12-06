import json


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
        self.binary_data = bytearray()

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

        # Генерация бинарного кода
        if not self._generate_binary():
            return False

        # Запись бинарного файла
        self._write_binary_file(output_file)

        # Вывод информации о количестве команд
        print(f"Assembled commands: {len(self.program)}")

        # В режиме тестирования добавить вывод байтов
        if test_mode:
            self._print_internal_representation()
            self._print_binary_representation()

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
            'C': cmd['value'],
            'size_C': 25
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
            'C': cmd['dest_reg'],
            'size_C': 7
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
            'C': cmd['dest_addr'],
            'size_C': 13
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
            'C': cmd['dest_addr'],
            'size_C': 13
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

    def _print_binary_representation(self):

        print("\nBinary representation:")
        print("-" * 50)

        total_bytes = len(self.binary_data)
        commands = total_bytes // 5

        for i in range(commands):
            start_idx = i * 5
            end_idx = start_idx + 5
            cmd_bytes = self.binary_data[start_idx:end_idx]

            print(f"Command {i}: ", end="")

            # Формат: 0xF8, 0x6B, 0x36, 0x00, 0x00
            hex_bytes = [f"0x{b:02X}" for b in cmd_bytes]
            print(", ".join(hex_bytes))

            # Дополнительно: битовое представление
            print(f"  Bits: ", end="")
            for b in cmd_bytes:
                print(f"{b:08b} ", end="")
            print()

        print(f"\nTotal bytes: {total_bytes}")
        print(f"Total commands: {commands}")
        print("-" * 50)

    def _save_intermediate(self, output_file):

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.program, f, indent=2, ensure_ascii=False)

    def _write_binary_file(self, output_file):

        with open(output_file, 'wb') as f:  # 'wb' - бинарный режим
            f.write(self.binary_data)

    def _generate_binary(self):

        self.binary_data = bytearray()

        for cmd in self.program:
            # Собираем 40-битное значение
            value = 0

            if cmd['opcode'] == 'load_const':
                # load_const: A(6) + B(7) + C(25) + unused(2)
                # Биты: 0-5:A, 6-12:B, 13-37:C, 38-39:0
                value = (cmd['A'] & 0x3F)  # A занимает биты 0-5
                value |= (cmd['B'] & 0x7F) << 6  # B занимает биты 6-12
                value |= (cmd['C'] & 0x1FFFFFF) << 13  # C занимает биты 13-37 (25 бит)
                # Неиспользуемые биты 38-39 = 0
                # Сдвигаем влево на 0 бит биты 38-39 уже в конце

            elif cmd['opcode'] == 'read_mem':
                # read_mem: A(6) + B(7) + C(7) + zeros(13) + unused(7)
                # Биты: 0-5:A, 6-12:B, 13-19:C, 20-37:0, 38-39:0
                value = (cmd['A'] & 0x3F)  # A занимает биты 0-5
                value |= (cmd['B'] & 0x7F) << 6  # B занимает биты 6-12
                value |= (cmd['C'] & 0x7F) << 13  # C занимает биты 13-19 (7 бит)
                # Биты 20-37 = 0
                # Неиспользуемые биты 38-39 = 0

            elif cmd['opcode'] == 'write_mem' or cmd['opcode'] == 'not':
                # write_mem/not: A(6) + B(7) + C(13) + zeros(12) + unused(2)
                # Биты: 0-5:A, 6-12:B, 13-25:C, 26-37:0, 38-39:0
                value = (cmd['A'] & 0x3F)  # биты 0-5
                value |= (cmd['B'] & 0x7F) << 6  # биты 6-12
                value |= (cmd['C'] & 0x1FFF) << 13  # биты 13-25 (13 бит)
                # Биты 26-37 = 0
                # Неиспользуемые биты 38-39 = 0
            else:
                print(f"Unknown opcode: {cmd['opcode']}")
                return False

            bytes_5 = value.to_bytes(5, byteorder='little')
            self.binary_data.extend(bytes_5)

        return True
