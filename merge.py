import pandas as pd
import argparse

def aggregate_filenames(group, special_col):
    """Aggregate filenames based on unique values in the special column."""
    # Drop NaN values and get unique values in the special column
    unique_values = group[special_col].dropna().unique()
    
    # If fewer than 2 unique values (0 or 1), no conflict exists
    if len(unique_values) < 2:
        return ""
    
    # Map each unique value to the first filename where it appears
    filename_map = {}
    for value in unique_values:
        # Find the first row with this value
        first_row = group[group[special_col] == value].iloc[0]
        filename_map[value] = first_row['filename']
    
    # Combine filenames for all unique values
    return ", ".join(sorted(set(filename_map.values())))

def process_files(file_list, key_columns, special_col, output_file):
    """Process Excel files, merge them, and aggregate based on key columns."""
    all_dfs = []
    
    # Read each file and add filename column
    for file in file_list:
        try:
            df = pd.read_excel(file)
            print(f"Read {len(df)} rows from {file}")
            if not df.empty:
                # Add filename column
                df['filename'] = file
                all_dfs.append(df)
        except FileNotFoundError:
            print(f"Error: File {file} not found.")
            return
        except pd.errors.ParserError:
            print(f"Error: Failed to parse {file}. Please check the file format.")
            return
        except Exception as e:
            print(f"Unexpected error reading {file}: {str(e)}")
            return
    
    # Check if any files were successfully read
    if not all_dfs:
        print("Error: No valid files to process.")
        return
    
    # Concatenate all DataFrames
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    # Validate columns
    missing_keys = [col for col in key_columns if col not in merged_df.columns]
    if missing_keys:
        print(f"Error: Key column(s) {missing_keys} not found in input files.")
        return
    if special_col not in merged_df.columns:
        print(f"Error: Special column '{special_col}' not found in input files.")
        return
    
    # Warn if special column is a key column
    if special_col in key_columns:
        print(f"Warning: Special column '{special_col}' is also a key column. "
              "The 'filename' column will always be empty due to no possible conflicts.")
    
    # Group by key columns and aggregate
    grouped = merged_df.groupby(key_columns, dropna=False).apply(
        lambda g: pd.Series({
            special_col: ", ".join(g[special_col].dropna().astype(str).unique()),
            'filename': aggregate_filenames(g, special_col)
        })
    ).reset_index()
    
    print(f"Merged into {len(grouped)} unique groups based on key columns {key_columns}")
    
    # Save to output file
    try:
        grouped.to_excel(output_file, index=False)
        print(f"Output written to {output_file}")
    except Exception as e:
        print(f"Error writing to {output_file}: {str(e)}")

def main():
    """Parse command-line arguments and run the processing."""
    parser = argparse.ArgumentParser(description="Merge Excel files and identify conflicts.")
    parser.add_argument('--files', nargs='+', required=True, help="List of Excel files to process")
    parser.add_argument('--key_columns', nargs='+', required=True, help="Columns to group by")
    parser.add_argument('--special_col', required=True, help="Special column to check for conflicts")
    parser.add_argument('--output', required=True, help="Output Excel file")
    
    args = parser.parse_args()
    
    # Process the files
    process_files(args.files, args.key_columns, args.special_col, args.output)

if __name__ == "__main__":
    main()
