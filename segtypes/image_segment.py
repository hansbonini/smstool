# segtypes/image_segment.py
import os
import math
from PIL import Image
from .segment import Segment
import yaml


class ImageSegment(Segment):
    def __init__(self, start, end, name, bpp=4, width=None, height=None, lines=[]):
        super().__init__(start, end, name)
        self.bpp = bpp
        self.width = width
        self.height = height
        self.lines = lines

    @staticmethod
    def convert_to_bpp_planar(segment_data, bpp, width, height):
        tile_count = len(segment_data) // (8 * bpp)
        grid_default = math.ceil(math.sqrt(tile_count))
        grid_width = (width * 8) // 8 if width is not None else grid_default
        grid_height = (height * 8) // 8 if height is not None else grid_default

        pixel_buffer = [[0] * (grid_width * 8) for _ in range(grid_height * 8)]

        for i in range(tile_count):
            tile_data = segment_data[i * 8 * bpp: (i + 1) * 8 * bpp]
            tile_pixels = ImageSegment.convert_tile_to_pixels(tile_data, bpp)

            row = i // grid_width
            col = i % grid_width

            for y in range(8):
                for x in range(8):
                    if row * 8 + y < grid_height * 8 and col * 8 + x < grid_width * 8:
                        pixel_buffer[row * 8 + y][col *
                                                  8 + x] = tile_pixels[y][x]

        return pixel_buffer

    @staticmethod
    def convert_tile_to_pixels(tile_data, bpp):
        pixels = [[0] * 8 for _ in range(8)]

        for y in range(8):
            planes = [tile_data[y * bpp + p] for p in range(bpp)]

            for x in range(8):
                pixel = sum(((plane >> (7 - x)) & 0x01) <<
                            p for p, plane in enumerate(planes))
                pixels[y][x] = pixel

        return pixels

    @staticmethod
    def convert_to_rgb(image, bpp):
        palette = [
            (0, 0, 0),          # Color #0: Black
            (17, 17, 17),       # Color #1: Dark Gray #1
            (34, 34, 34),       # Color #2: Dark Gray #2
            (51, 51, 51),       # Color #3: Dark Gray #3
            (68, 68, 68),       # Color #4: Dark Gray #4
            (85, 85, 85),       # Color #5: Medium Gray #1
            (102, 102, 102),    # Color #6: Medium Gray #2
            (119, 119, 119),    # Color #7: Medium Gray #3
            (136, 136, 136),    # Color #8: Medium Gray #4
            (153, 153, 153),    # Color #9: Medium Gray #5
            (170, 170, 170),    # Color #10: Light Gray #1
            (187, 187, 187),    # Color #11: Light Gray #2
            (204, 204, 204),    # Color #12: Light Gray #3
            (221, 221, 221),    # Color #13: Light Gray #4
            (238, 238, 238),    # Color #14: Light Gray #5
            (255, 255, 255)     # Color #15: White
        ] if bpp > 1 else [
            (0, 0, 0),          # Color #0: Black
            (255, 255, 255)     # Color #1: White
        ]

        width = len(image[0])
        height = len(image)

        rgb_image = Image.new("RGB", (width, height))
        pixels = rgb_image.load()

        for y in range(height):
            for x in range(width):
                pixel_value = image[y][x]
                pixels[x, y] = palette[pixel_value]

        return rgb_image

    def process(self, segment_data):
        images_folder = os.path.join("data", "images")
        os.makedirs(images_folder, exist_ok=True)

        binaries_folder = os.path.join("data", "images", "bin")
        os.makedirs(binaries_folder, exist_ok=True)

        converted_data = self.convert_to_bpp_planar(
            segment_data, self.bpp, self.width, self.height)
        rgb_data = self.convert_to_rgb(converted_data, self.bpp)

        image_path = os.path.join(images_folder, f"{self.name}_{self.bpp}bpp.png")
        self.save_image(rgb_data, image_path)

        file_path = os.path.join(binaries_folder, f"{self.name}_{self.bpp}bpp.bin")
        with open(file_path, 'wb') as binary_file:
            binary_file.write(segment_data)

        # Segment address range into a asm file
        seg_lines = []
        include = None
        for i in range(len(self.lines)):
            addr, line = self.lines[i]
            if (addr >= self.start) and (addr < self.end):
                if (addr == self.start):
                    include = (i-1, addr)
                seg_lines.append((addr, line))

        #  Replace code segment by include
        for addr, line in seg_lines:
            self.lines.remove((addr, line))
        if include != None:
            self.lines.insert(
                include[0], (include[1], f'\n\n.INCLUDE "{file_path}"\n\n'))

        print(
            f"Segment {self.name}: Converted to {self.bpp}bpp planar and saved as image in {image_path}.")

    @staticmethod
    def save_image(image, path):
        image.save(path)
