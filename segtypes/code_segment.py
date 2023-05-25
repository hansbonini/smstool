import os
from z80dis import z80
from segtypes.segment import Segment


class CodeSegment(Segment):
    def __init__(self, start, end, name, labels={}):
        super().__init__(start, end, name)
        self.instructions = []
        self.labels = labels

    def disassemble(self, segment_data):
        address = self.start
        while address < self.end:
            decoded = z80.decode(segment_data[address::], address)
            if decoded.status != z80.DECODE_STATUS.OK:
                break
            # print(f"\t {z80.disasm(decoded).replace('0x', '$').lower()}")
            # print(decoded.operands)
            self.instructions.append((address, decoded))
            address += decoded.len

    def print_instructions(self):
        for address, instruction in self.instructions:
            print(f"\t {z80.disasm(instruction).replace('0x', '$').lower()}")

    def get_labels(self):
        return self.labels

    def process(self, segment_data):
        self.disassemble(segment_data)
        # self.print_instructions()
        # Save the instructions to an .asm file
        asm_folder = "data/asm"
        os.makedirs(asm_folder, exist_ok=True)
        asm_file = os.path.join(asm_folder, f"{self.name}.asm")
        lines = []
        definitions = []
        i = 0
        for address, instruction in self.instructions:
            line = z80.disasm(instruction).lower()
            operands = [t for types in instruction.operands for t in types]
            if f'{address:04X}' in self.labels:
                lines.append((address, f'\n\nLABEL_{self.labels[address]}:\n'))
            # Put definitions at start of the code and replace on every OUT instruction
            if instruction.op is z80.OP.OUT:
                if "0x00be" in line:
                    def_name = "Port_VDPData"
                    definition = f"\t.def {def_name}\t$BF\n"
                    if definition not in definitions:
                        lines.insert(0, (address, definition))
                        definitions.append(definition)
                    line = line.replace('0x00bf', def_name)
                elif "0x00bf" in line:
                    def_name = "Port_VDPAddress"
                    definition = f"\t.def {def_name}\t$BF\n"
                    if definition not in definitions:
                        lines.insert(0, (address, definition))
                        definitions.append(definition)
                    line = line.replace('0x00bf', def_name)
            # Put definitions at start of the code and replace on every IN instruction
            elif instruction.op is z80.OP.IN:
                if "0x00bf" in line:
                    def_name = "Port_VDPStatus"
                    definition = f"\t.def {def_name}\t$BF\n"
                    if definition not in definitions:
                        lines.insert(0, (address, definition))
                        definitions.append(definition)
                    line = line.replace('0x00bf', def_name)
                elif "0x00dc" in line:
                    def_name = "Port_IOPort1"
                    definition = f"\t.def {def_name}\t$DC\n"
                    if definition not in definitions:
                        lines.insert(0, (address, definition))
                        definitions.append(definition)
                    line = line.replace('0x00dc', def_name)
                elif "0x00dd" in line:
                    def_name = "Port_IOPort2"
                    definition = f"\t.def {def_name}\t$DD\n"
                    if definition not in definitions:
                        lines.insert(0, (address, definition))
                        definitions.append(definition)
                    line = line.replace('0x00dd', def_name)

            if z80.OPER_TYPE.IMM in operands:
                line = line.replace('0x', '$')
            elif z80.OPER_TYPE.ADDR_DEREF in operands:
                line = line.replace('0x', '$')
            if i == 0:
                # Put a label before every first instruction
                if address == 0x0:
                    label = '_START:'
                    lines.append((address, f"\n{label}\n"))
                    self.labels[address] = label
                else:
                    label = f'{address:04X}'
                    lines.append((address, f'\n\nLABEL_{label}:\n'))
                    self.labels[address] = label
            if instruction.typ is z80.INSTRTYPE.JUMP_CALL_RETURN:
                print(instruction.operands)
                # Put a label after every RET instruction except last
                if instruction.op is z80.OP.RET and (i < len(self.instructions)-1):
                    lines.append((address,
                                  f"\t{line}\n"))
                    label = f'{(address+instruction.len):04X}'
                    lines.append(((address+instruction.len),
                                 f'\n\nLABEL_{label}:\n'))
                    self.labels[address+instruction.len] = label
                else:
                    for oper in instruction.operands:
                        if oper[0] is z80.OPER_TYPE.ADDR:
                            label = f'{oper[1]:04X}'
                            if oper[1] not in self.labels.keys():
                                self.labels[oper[1]] = label
                                if oper[1] < address:
                                    x = 0
                                    for l in lines:
                                        if l[0] == oper[1]:
                                            lines.insert(
                                                x, (address, f'\n\nLABEL_{label}:\n'))
                                            break
                                        x += 1
                            line = line.replace(
                                f"0x{oper[1]:04x}", f'LABEL_{label}')
                    lines.append((address,
                                  f"\t{line}\n"))
            else:
                lines.append((address,
                              f"\t{line}\n"))
            i += 1
        with open(asm_file, "w") as f:
            for address, line in lines:
                f.write(line)
        print(f"Segment {self.name}: Saved as a code in {asm_file}.")
