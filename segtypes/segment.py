# segtypes/segment.py
import os

class Segment:
    def __init__(self, start, end, name):
        self.start = start
        self.end = end
        self.name = name

    def process(self, segment_data):
        # Check if the "data/bin" folder exists and create it if necessary
        bin_folder = os.path.join("data", "bin")
        os.makedirs(bin_folder, exist_ok=True)

        # Define the full path to save the binary file in the "data/bin" folder
        file_path = os.path.join(bin_folder, f"{self.name}.bin")

        # Example: Save the data as a binary file in the "data/bin" folder
        with open(file_path, 'wb') as binary_file:
            binary_file.write(segment_data)
        print(f"Segment {self.name}: Saved as a binary file in data/bin/{self.name}.bin.")
