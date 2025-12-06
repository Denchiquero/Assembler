from xml.dom import minidom
import xml.etree.ElementTree as ET

class Interpreter:
    """Интерпретатор для УВМ"""

    # Обратное отображение кодов операций
    REVERSE_OPCODES = {
        56: 'load_const',
        54: 'write_mem',
        59: 'not',
        62: 'read_mem'
    }

    def __init__(self):
        # Раздельная память как в спецификации
        self.instruction_memory = bytearray()  # Память команд
        self.data_memory = [0] * 8192  # Память данных (8K слов)
        self.registers = [0] * 128  # Регистры (0-127)

        # Регистры состояния
        self.pc = 0  # Program Counter
        self.halted = False

    def load_program(self, binary_file):
        """Загрузка программы из бинарного файла"""
        try:
            with open(binary_file, 'rb') as f:
                self.instruction_memory = bytearray(f.read())
            print(f"Program loaded: {len(self.instruction_memory)} bytes")
            return True
        except Exception as e:
            print(f"Error loading program: {e}")
            return False

    def decode_instruction(self, instruction_bytes):
        """Декодирование 5 байт инструкции в промежуточное представление"""
        if len(instruction_bytes) != 5:
            return None

        # Конвертируем 5 байт в 40-битное значение (little-endian)
        value = int.from_bytes(instruction_bytes, 'little')

        # Извлекаем поля
        A = value & 0x3F  # Биты 0-5
        B = (value >> 6) & 0x7F  # Биты 6-12

        # Определяем тип инструкции по A
        opcode_name = self.REVERSE_OPCODES.get(A)
        if not opcode_name:
            return None

        # Извлекаем C в зависимости от типа инструкции
        if opcode_name == 'load_const':
            # C: 25 бит (биты 13-37)
            C = (value >> 13) & 0x1FFFFFF
        elif opcode_name == 'read_mem':
            # C: 7 бит (биты 13-19)
            C = (value >> 13) & 0x7F
        else:  # write_mem и not
            # C: 13 бит (биты 13-25)
            C = (value >> 13) & 0x1FFF

        return {
            'opcode': opcode_name,
            'A': A,
            'B': B,
            'C': C
        }

    def execute_instruction(self, instruction):
        """Выполнение одной инструкции"""
        if instruction['opcode'] == 'load_const':
            # load_const B C: R[B] = C
            self.registers[instruction['B']] = instruction['C']
            print(f"  load_const: R[{instruction['B']}] = {instruction['C']}")

        elif instruction['opcode'] == 'read_mem':
            # read_mem B C: R[C] = M[R[B]]
            src_addr = self.registers[instruction['B']]
            if 0 <= src_addr < len(self.data_memory):
                self.registers[instruction['C']] = self.data_memory[src_addr]
                print(f"  read_mem: R[{instruction['C']}] = M[{src_addr}] = {self.data_memory[src_addr]}")
            else:
                print(f"  Memory read error: address {src_addr} out of bounds")

        elif instruction['opcode'] == 'write_mem':
            # write_mem B C: M[C] = R[B]
            dest_addr = instruction['C']
            if 0 <= dest_addr < len(self.data_memory):
                self.data_memory[dest_addr] = self.registers[instruction['B']]
                print(f"  write_mem: M[{dest_addr}] = R[{instruction['B']}] = {self.registers[instruction['B']]}")
            else:
                print(f"  Memory write error: address {dest_addr} out of bounds")

        elif instruction['opcode'] == 'not':
            # not B C: M[C] = ~R[B]
            dest_addr = instruction['C']
            if 0 <= dest_addr < len(self.data_memory):
                self.data_memory[dest_addr] = ~self.registers[instruction['B']] & 0xFFFFFFFF
                print(f"  not: M[{dest_addr}] = ~R[{instruction['B']}] = {self.data_memory[dest_addr]}")
            else:
                print(f"  Memory write error: address {dest_addr} out of bounds")

    def run(self):
        """Основной цикл выполнения программы"""
        print("Starting program execution...")

        while not self.halted and self.pc < len(self.instruction_memory):
            # Читаем следующую инструкцию (5 байт)
            if self.pc + 5 > len(self.instruction_memory):
                print(f"Warning: incomplete instruction at PC={self.pc}")
                break

            instruction_bytes = self.instruction_memory[self.pc:self.pc + 5]

            # Декодируем инструкцию
            instruction = self.decode_instruction(instruction_bytes)
            if not instruction:
                print(f"Error: cannot decode instruction at PC={self.pc}")
                break

            print(f"PC={self.pc}: {instruction['opcode']} B={instruction['B']} C={instruction['C']}")

            # Выполняем инструкцию
            self.execute_instruction(instruction)

            # Увеличиваем счетчик команд
            self.pc += 5

            # Простая проверка на останов (можно расширить)
            if self.pc >= len(self.instruction_memory):
                self.halted = True

        print("Program execution finished.")

    def save_memory_dump(self, output_file, start_addr, end_addr):
        """Сохранение дампа памяти в формате XML"""
        if start_addr < 0 or end_addr >= len(self.data_memory) or start_addr > end_addr:
            print(f"Error: invalid address range {start_addr}-{end_addr}")
            return False

        try:
            # Создаем XML структуру
            root = ET.Element("memory_dump")

            # Добавляем информацию о диапазоне
            range_elem = ET.SubElement(root, "range")
            range_elem.set("start", str(start_addr))
            range_elem.set("end", str(end_addr))

            # Добавляем данные памяти
            data_elem = ET.SubElement(root, "data")
            for addr in range(start_addr, end_addr + 1):
                cell = ET.SubElement(data_elem, "cell")
                cell.set("address", str(addr))
                cell.set("value", str(self.data_memory[addr]))
                cell.set("hex", f"0x{self.data_memory[addr]:08X}")

            # Форматируем XML
            xml_str = ET.tostring(root, encoding='utf-8')
            dom = minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent="  ")

            # Сохраняем в файл
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)

            print(f"Memory dump saved to {output_file}")
            return True

        except Exception as e:
            print(f"Error saving memory dump: {e}")
            return False