# main.py
import os
import yaml
from z80dis import z80
from segtypes.segment import Segment
from segtypes.binary_segment import BinarySegment
from segtypes.text_segment import TextSegment
from segtypes.image_segment import ImageSegment
from segtypes.code_segment import CodeSegment


def disassemble(rom_data):
    labels = {}
    constants = []
    instructions = []
    lines = []
    address = 0
    i = 0
    # Disassemble rom code
    while address < len(rom_data):
        decoded = z80.decode(rom_data[address::], address)
        if decoded.status is z80.DECODE_STATUS.OK:
            instructions.append((address, decoded))
        address += decoded.len
    # Adjust disassembled code to WLA-DX syntax
    for address, instruction in instructions:
        line = z80.disasm(instruction).lower()
        operands = [t for types in instruction.operands for t in types]
        if address in labels.keys():
            if (address, f'\n\nLABEL_{labels[address]}:\n') not in lines:
                lines.append(
                    (address, f'\n\nLABEL_{labels[address]}:\n'))
        # Put constants at start of the code and replace on every OUT instruction
        if instruction.op is z80.OP.OUT:
            if "0x00be" in line:
                const_name = "Port_VDPData"
                constant = f"\t{const_name} = \t$BE\n"
                if constant not in constants:
                    constants.append(constant)
                line = line.replace('0x00be', const_name)
            elif "0x00bf" in line:
                const_name = "Port_VDPAddress"
                constant = f"\t{const_name} = \t$BF\n"
                if constant not in constants:
                    constants.append(constant)
                line = line.replace('0x00bf', const_name)
        # Put constants at start of the code and replace on every IN instruction
        elif instruction.op is z80.OP.IN:
            if "0x00bf" in line:
                const_name = "Port_VDPStatus"
                constant = f"\t{const_name} = \t$BF\n"
                if constant not in constants:
                    constants.append(constant)
                line = line.replace('0x00bf', const_name)
            elif "0x00dc" in line:
                const_name = "Port_IOPort1"
                constant = f"\t{const_name} = \t$DC\n"
                if constant not in constants:
                    constants.append(constant)
                line = line.replace('0x00dc', const_name)
            elif "0x00dd" in line:
                const_name = "Port_IOPort2"
                constant = f"\t{const_name} = \t$DD\n"
                if constant not in constants:
                    constants.append(constant)
                line = line.replace('0x00dd', const_name)

        if z80.OPER_TYPE.IMM in operands:
            line = line.replace('0x', '$')
        elif z80.OPER_TYPE.ADDR_DEREF in operands:
            line = line.replace('0x', '$')

        if i == 0:
            # Put a label before every first instruction
            if address == 0x0:
                label = '_START:'
                lines.append((address, f"\n{label}\n"))
                labels[address] = label
            else:
                label = f'{address:04X}'
                lines.append((address, f'\n\nLABEL_{label}:\n'))
                labels[address] = label

        if instruction.typ is z80.INSTRTYPE.JUMP_CALL_RETURN:
            # Put a label after every RET instruction except last
            if instruction.op is z80.OP.RET and (i < len(instructions)-1):
                lines.append((address,
                              f"\t{line}\n"))
                if ((address+instruction.len),
                        f'\n\nLABEL_{label}:\n') not in lines:
                    label = f'{(address+instruction.len):04X}'
                    lines.append(((address+instruction.len),
                                  f'\n\nLABEL_{label}:\n'))
                    labels[address+instruction.len] = label
            else:
                for oper in instruction.operands:
                    if oper[0] is z80.OPER_TYPE.ADDR:
                        label = f'{oper[1]:04X}'
                        if oper[1] not in labels.keys():
                            labels[oper[1]] = label
                            # print(f'{oper[1]:04X} {address:04X}')
                            if oper[1] < address:
                                x = 0
                                for l in lines:
                                    if l[0] == oper[1]:
                                        if (oper[1], f'\n\nLABEL_{label}:\n') not in lines:
                                            lines.insert(
                                                x, (oper[1], f'\n\nLABEL_{label}:\n'))
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
    constants.sort()
    for constant in constants:
        lines.insert(0, (0, constant))
    return lines


def read_rom(rom_file, yaml_file):
    with open(yaml_file, 'r') as yaml_content:
        yaml_data = yaml.safe_load(yaml_content)

    with open(rom_file, 'rb') as rom_content:
        rom = rom_content.read()

    segment_classes = {
        cls.__name__.lower().replace("segment", ""): cls for cls in Segment.__subclasses__()
    }

    lines = disassemble(rom)

    for segment in yaml_data['segments']:
        start = segment['start']
        end = segment['end']
        segment_type = segment['type']
        name = segment['name']

        segment_class = segment_classes.get(segment_type.lower())

        if segment_class is None:
            print(f"Segment {name}: Invalid segment type.")
            continue

        segment_obj = segment_class(start, end, name)
        if isinstance(segment_obj, ImageSegment):
            segment_obj.bpp = segment.get('bpp', 4)
            segment_obj.width = segment.get('width', None)
            segment_obj.height = segment.get('height', None)
            segment_obj.lines = lines

        if isinstance(segment_obj, CodeSegment):
            segment_obj.lines = lines

        segment_data = rom[start:end + 1]
        segment_obj.process(segment_data)

    asm_folder = "data/asm"
    os.makedirs(asm_folder, exist_ok=True)
    asm_file = os.path.join(asm_folder, f"main.asm")

    with open(asm_file, "w") as f:
        for addr, line in lines:
            # f.write(f'[{addr:04X}{line}')
            f.write(f'{line}')


if __name__ == "__main__":
    # Example usage
    rom_file = 'rom.sms'
    yaml_file = 'segments.yaml'
    read_rom(rom_file, yaml_file)
