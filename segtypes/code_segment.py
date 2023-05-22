import os
from z80dis import z80
from segtypes.segment import Segment


class CodeSegment(Segment):
    def __init__(self, start, end, name):
        super().__init__(start, end, name)
        self.instructions = []

    def disassemble(self, segment_data):
        address = self.start
        while address < self.end:
            decoded = z80.decode(segment_data[address::], address)
            if decoded.status != z80.DECODE_STATUS.OK:
                break
            self.instructions.append((address, z80.disasm(decoded)))
            address += decoded.len

    def print_instructions(self):
        for address, instruction in self.instructions:
            print(f"[0x{address:04X}]: {instruction}")

    def process(self, segment_data):
        self.disassemble(segment_data)
        #self.print_instructions()
        # Save the instructions to an .asm file
        asm_folder = "data/asm"
        os.makedirs(asm_folder, exist_ok=True)
        asm_file = os.path.join(asm_folder, f"{self.name}.asm")
        with open(asm_file, "w") as f:
            for address, instruction in self.instructions:
                f.write(f"[0x{address:04X}]: {instruction}\n")

        print(f"Segment {self.name}: Saved as a code in {asm_file}.")