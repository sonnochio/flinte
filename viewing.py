import numpy as np
import pandas as pd

# Load the .npz file
file_path = '/Users/sonny/Downloads/graph_data.npz'  # Replace with your .npz file path
data = np.load(file_path)

# List all keys (array names) in the file
print("Keys in .npz file:", data.keys())

# Access and print each array
for key in data.keys():
    array = data[key]
    print(f"\nData for key: {key}")
    print(array)

    # If the array is 2D, display it as a table
    if array.ndim == 2:
        df = pd.DataFrame(array)
        print(df)
