import pandas as pd
import sys

def merge_excel_sheets(input_files, output_file):
    """
    Merge three Excel sheets into one, preserving all rows and columns.
    
    Parameters:
    input_files (list): List of three input Excel file paths
    output_file (str): Path for the output Excel file
    """
    try:
        # Read the three input Excel files
        print(f"Reading {input_files[0]}")
        df1 = pd.read_excel(input_files[0])
        print(f"Sheet 1 shape: {df1.shape}")
        
        print(f"Reading {input_files[1]}")
        df2 = pd.read_excel(input_files[1])
        print(f"Sheet 2 shape: {df2.shape}")
        
        print(f"Reading {input_files[2]}")
        df3 = pd.read_excel(input_files[2])
        print(f"Sheet 3 shape: {df3.shape}")
        
        # Merge the DataFrames by concatenating rows
        print("Merging the sheets")
        combined_df = pd.concat([df1, df2, df3], axis=0, ignore_index=True)
        print(f"Combined shape: {combined_df.shape}")
        
        # Write the result to a new Excel file
        print(f"Writing to {output_file}")
        combined_df.to_excel(output_file, index=False)
        print("Merge completed successfully!")
        
    except FileNotFoundError as e:
        print(f"Error: One of the input files was not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check for correct number of command-line arguments
    if len(sys.argv) != 5:
        print("Usage: python merge_sheets.py input1.xlsx input2.xlsx input3.xlsx output.xlsx")
        sys.exit(1)
    
    # Get input and output file paths from command line
    input_files = sys.argv[1:4]
    output_file = sys.argv[4]
    
    # Execute the merge
    merge_excel_sheets(input_files, output_file)
