# segtypes/text_segment.py
from .segment import Segment

class TextSegment(Segment):
    @staticmethod
    def decode_segment_data(segment_data):
        return segment_data.decode('utf-8')

    def process(self, segment_data):
        text = self.decode_segment_data(segment_data)
        print(f"Segment {self.name}: Text found:\n{text}")
