import os
from z80dis import z80
from segtypes.segment import Segment


class CodeSegment(Segment):
    def __init__(self, start, end, name, lines=[]):
        super().__init__(start, end, name)
        self.lines = lines

    def process(self, segment_data):
        # Save the instructions to an .asm file
        asm_folder = "data/asm/segment"
        os.makedirs(asm_folder, exist_ok=True)
        asm_file = os.path.join(asm_folder, f"{self.name}.asm")

        # Segment address range into a asm file
        seg_lines = []
        include = None
        for i in range(len(self.lines)):
            addr, line = self.lines[i]
            if (addr >= self.start) and (addr < self.end):
                if (addr == self.start):           
                    include = (i, addr)
                seg_lines.append((addr, line))

        #  Replace code segment by include
        if include is not None:
            self.lines.insert(
                include[0], (include[1], f'\n\n.INCLUDE "{asm_file}"\n\n'))
        for addr, line in seg_lines:
            self.lines.remove((addr, line))
        # Remove first two breaklines from segment
        if '\n\n' in seg_lines[0][1]:
            seg_lines[0] = (seg_lines[0][0], seg_lines[0]
                            [1].replace('\n\n', ''))

        with open(asm_file, "w") as f:
            for addr, line in seg_lines:
                f.write(f'{line}')
        print(f"Segment {self.name}: Saved as a code in {asm_file}.")
