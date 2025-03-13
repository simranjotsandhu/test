import pandas as pd
import sys

def merge_excel_sheets(input_files, output_file):
    """
    Merge four Excel files into one, adding a 'filenames' column to track the source file(s) of each row.
    If a row is identical across multiple files, list all filenames separated by commas.

    Parameters:
    input_files (list): List of four input Excel file paths.
    output_file (str): Path for the output Excel file.
    """
    try:
        # Step 1 & 2: Read each file and add 'filenames' column
        dfs = []
        for file in input_files:
            print(f"Reading {file}")
            df = pd.read_excel(file)
            df['filenames'] = file  # Add the filename to each row
            dfs.append(df)

        # Step 3: Concatenate all DataFrames
        print("Concatenating the sheets")
        combined_df = pd.concat(dfs, axis=0, ignore_index=True)
        print(f"Combined shape: {combined_df.shape}")

        # Step 4: Merge identical rows by grouping
        print("Merging duplicate rows")
        # Group by all columns except 'filenames'
        group_cols = [col for col in combined_df.columns if col != 'filenames']
        merged_df = combined_df.groupby(group_cols, dropna=False, sort=False).agg({
            'filenames': lambda x: ', '.join(x.unique())  # Join unique filenames with commas
        }).reset_index()
        print(f"Merged shape: {merged_df.shape}")

        # Step 5: Write the result to the output file
        print(f"Writing to {output_file}")
        merged_df.to_excel(output_file, index=False)
        print("Merge completed successfully!")

    except FileNotFoundError as e:
        print(f"Error: One of the input files was not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check for correct number of command-line arguments
    if len(sys.argv) != 6:
        print("Usage: python merge_sheets.py input1.xlsx input2.xlsx input3.xlsx input4.xlsx output.xlsx")
        sys.exit(1)

    # Extract input and output file paths
    input_files = sys.argv[1:5]  # First four arguments after script name
    output_file = sys.argv[5]    # Last argument

    # Execute the merge function
    merge_excel_sheets(input_files, output_file)
