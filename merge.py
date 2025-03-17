import pandas as pd
import sys

def merge_excel_sheets(input_files, special_col, output_file):
    """
    Merge four Excel files based on columns A, B, and C with special handling for a specified column.
    
    Parameters:
    input_files (list): List of four input Excel file paths.
    special_col (str): The special column to handle differently during merging.
    output_file (str): Path for the output Excel file.
    """
    try:
        # Step 1: Read and validate input Excel files
        dfs = []
        for i, file in enumerate(input_files, start=1):
            print(f"Reading {file}")
            df = pd.read_excel(file)
            # Check for required columns: A, B, C, and the special column
            required_cols = ['A', 'B', 'C', special_col]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"Error: File {file} is missing columns: {', '.join(missing_cols)}")
                sys.exit(1)
            df['file_id'] = i  # Assign file identifier based on input order
            dfs.append(df)
        
        # Step 2: Concatenate all DataFrames
        print("Concatenating the sheets")
        combined_df = pd.concat(dfs, axis=0, ignore_index=True)
        print(f"Combined shape: {combined_df.shape}")
        
        # Step 3: Group by A, B, C and process each group
        print("Processing groups based on columns A, B, C")
        grouped = combined_df.groupby(['A', 'B', 'C'], as_index=False)
        merged_rows = []
        skipped_a_values = []
        
        for name, group in grouped:
            # Identify non-special columns (excluding A, B, C, special_col, and file_id)
            non_special_cols = [col for col in group.columns if col not in ['A', 'B', 'C', special_col, 'file_id']]
            # Check if any non-special column has multiple unique values
            has_multiple_values = any(group[col].nunique(dropna=False) > 1 for col in non_special_cols)
            
            if has_multiple_values:
                # Skip merging this group and record column A value
                skipped_a_values.append(name[0])  # name[0] is the value of A
                continue
            
            # Process the special column: concatenate values with file identifiers
            special_values = group[[special_col, 'file_id']].dropna(subset=[special_col])
            if not special_values.empty:
                special_combined = ', '.join(
                    f"{val}-{file_id}" for val, file_id in zip(special_values[special_col], special_values['file_id'])
                )
            else:
                special_combined = ''
            
            # Create the merged row for this group
            merged_row = {'A': name[0], 'B': name[1], 'C': name[2], special_col: special_combined}
            for col in non_special_cols:
                # Take the first non-NaN value for non-special columns (should be unique due to check)
                merged_row[col] = group[col].iloc[0] if not group[col].isna().all() else ''
            merged_rows.append(merged_row)
        
        # Step 4: Create the merged DataFrame from processed rows
        if merged_rows:
            merged_df = pd.DataFrame(merged_rows)
            print(f"Merged shape: {merged_df.shape}")
        else:
            print("No rows to merge after filtering")
            merged_df = pd.DataFrame()
        
        # Step 5: Write the merged DataFrame to the output file
        print(f"Writing to {output_file}")
        merged_df.to_excel(output_file, index=False)
        print("Merge completed successfully!")
        
        # Step 6: Print skipped column A values
        if skipped_a_values:
            print("Skipped column A values due to multiple values in non-special columns:")
            print(', '.join(map(str, skipped_a_values)))
        else:
            print("No merges were skipped.")
        
    except FileNotFoundError as e:
        print(f"Error: One of the input files was not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Validate command-line arguments
    if len(sys.argv) != 7:
        print("Usage: python merge_sheets.py input1.xlsx input2.xlsx input3.xlsx input4.xlsx special_col output.xlsx")
        sys.exit(1)
    
    # Extract arguments
    input_files = sys.argv[1:5]  # First four arguments are input files
    special_col = sys.argv[5]    # Fifth argument is the special column name
    output_file = sys.argv[6]    # Sixth argument is the output file
    
    # Run the merge function
    merge_excel_sheets(input_files, special_col, output_file)
