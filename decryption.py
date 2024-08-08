import plistlib
import os
import re
import shutil

def rename_files_in_directory(input_dir, prefix):
    # Rename all files in the input directory
    for i, file_name in enumerate(os.listdir(input_dir), start=1):
        # Construct full file path
        file_path = os.path.join(input_dir, file_name)

        # Skip directories, only rename files
        if os.path.isdir(file_path):
            continue

        # Construct new file name with prefix and number
        new_file_name = f"{prefix}_{i}{os.path.splitext(file_name)[1]}"
        new_file_path = os.path.join(input_dir, new_file_name)

        # Rename the file
        os.rename(file_path, new_file_path)
        print(f'Renamed {file_path} to {new_file_path}')

def create_bplist_copy(file_path):
    # Construct the new file path with .bplist extension
    new_file_path = file_path + '.bplist'
    shutil.copy(file_path, new_file_path)
    print(f'Created {new_file_path} as a copy of {file_path}')
    return new_file_path

def clean_output_directory(output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    print(f'Cleaned the output directory {output_dir}')

def process_files_in_directory(input_dir, output_dir):
    for file_name in os.listdir(input_dir):
        # Construct full file path
        file_path = os.path.join(input_dir, file_name)

        # Skip directories, only process files
        if os.path.isdir(file_path):
            continue

        # Create a new file with .bplist extension and get the new file path
        bplist_file_path = create_bplist_copy(file_path)

        try:
            # Read the binary property list file
            with open(bplist_file_path, 'rb') as file:
                data = plistlib.load(file)
        except plistlib.InvalidFileException:
            print(f"Invalid file: {bplist_file_path}")
            continue

        # Convert plist data to string
        data_str = str(data)

        # Create a parent directory for the current file within the output directory
        base_name = os.path.splitext(file_name)[0]
        parent_dir = os.path.join(output_dir, base_name)
        os.makedirs(parent_dir, exist_ok=True)

        # Create a directory to store binary text files within the parent directory
        binarytext_dir = os.path.join(parent_dir, 'binarytext')
        os.makedirs(binarytext_dir, exist_ok=True)

        # Regular expression to find all occurrences of binary data enclosed by b'\x89PNG\ and \x82'
        pattern = re.compile(r"b'\\x89PNG.*?\\x82'", re.DOTALL)

        # Find all matches
        matches = pattern.findall(data_str)

        # Save each match to a separate file in the binarytext directory
        for i, match in enumerate(matches, start=1):
            binarytext_file_path = os.path.join(binarytext_dir, f'{base_name}binaryText{i}.txt')
            with open(binarytext_file_path, 'w') as file:
                file.write(match)

        # Create a directory to store output images within the parent directory
        images_output_dir = os.path.join(parent_dir, 'output')
        os.makedirs(images_output_dir, exist_ok=True)

        # Process each binary text file to check if the data is a valid PNG image
        image_counter = 1  # Initialize a counter for naming the output images
        for binarytext_file in os.listdir(binarytext_dir):
            binarytext_file_path = os.path.join(binarytext_dir, binarytext_file)
            
            # Read the string data from the binary text file
            with open(binarytext_file_path, "r") as f:
                raw_data = f.read()

            # Convert the string representation to raw bytes
            clean_data = bytes(raw_data, "utf-8").decode("unicode_escape").encode("latin1")

            # Check if the cleaned data has the PNG signature
            is_png = clean_data[2:].startswith(b'\x89PNG\r\n\x1a\n')

            # Save the binary data to an output file if it's a valid PNG image
            if (is_png):
                output_file_path = os.path.join(images_output_dir, f'{base_name}_output{image_counter}.png')
                with open(output_file_path, "wb") as f:
                    f.write(clean_data[2:])
                print(f"Saved PNG image to {output_file_path}")
                image_counter += 1  # Increment the counter for the next image
            else:
                print(f"The binary data in {binarytext_file_path} is not a valid PNG image.")

def collect_png_files(output_dir, album_dir):
    # Create the album directory
    os.makedirs(album_dir, exist_ok=True)

    # Walk through the output directory to find all PNG files
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith('.png'):
                # Construct the full file path
                file_path = os.path.join(root, file)

                # Construct the destination path in the album directory
                dest_path = os.path.join(album_dir, file)

                # Copy the PNG file to the album directory
                shutil.copy(file_path, dest_path)
                print(f'Copied {file_path} to {dest_path}')

def cleanup_files_and_directories(input_dir, output_dir):
    # Remove all .bplist files from the input directory
    for file_name in os.listdir(input_dir):
        if file_name.endswith('.bplist'):
            file_path = os.path.join(input_dir, file_name)
            os.remove(file_path)
            print(f'Deleted {file_path}')

    # Remove the entire output directory
    shutil.rmtree(output_dir)
    print(f'Deleted the output directory {output_dir}')

print("Script execution completed.")

# Path to the directory containing the input files
input_directory = "input"
output_directory = "output"

# Ensure the output directory exists
clean_output_directory(output_directory)

# Iterate through each subdirectory in the input directory
for sub_dir in os.listdir(input_directory):
    sub_dir_path = os.path.join(input_directory, sub_dir)
    if os.path.isdir(sub_dir_path):
        print(f"Processing folder: {sub_dir}")

        # Use the folder name as the prefix
        prefix = sub_dir

        # Rename files in the subdirectory
        rename_files_in_directory(sub_dir_path, prefix)

        # Process files in the subdirectory
        process_files_in_directory(sub_dir_path, output_directory)

        # Define a separate album directory for each subdirectory
        album_directory = os.path.join("album", sub_dir)
        clean_output_directory(album_directory)

        # Collect all PNG files into the album directory
        collect_png_files(output_directory, album_directory)

        # Cleanup .bplist files in the subdirectory and the output directory
        cleanup_files_and_directories(sub_dir_path, output_directory)
