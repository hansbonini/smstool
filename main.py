# main.py
import os
import yaml
from segtypes.segment import Segment
from segtypes.binary_segment import BinarySegment
from segtypes.text_segment import TextSegment
from segtypes.image_segment import ImageSegment
from segtypes.code_segment import CodeSegment

def read_rom(rom_file, yaml_file):
    with open(yaml_file, 'r') as yaml_content:
        yaml_data = yaml.safe_load(yaml_content)

    with open(rom_file, 'rb') as rom_content:
        rom = rom_content.read()

    segment_classes = {
        cls.__name__.lower().replace("segment", ""): cls for cls in Segment.__subclasses__()
    }

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

        segment_data = rom[start:end + 1]
        segment_obj.process(segment_data)


if __name__ == "__main__":
    # Example usage
    rom_file = 'rom.sms'
    yaml_file = 'segments.yaml'
    read_rom(rom_file, yaml_file)
