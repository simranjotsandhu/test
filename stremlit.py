import argparse
import gradio as gr
import pandas as pd
import os

# Global variable to store tagging results
output_file = "tagged_results.csv"
admin_password = "securepassword"  # Change this to a secure password

def upload_excel(file, password):
    """Handles file upload and validates the format, protected by a password."""
    if password != admin_password:
        return "Unauthorized: Incorrect password."
    if file is None:
        return "Please upload an Excel file."
    df = pd.read_excel(file.name)
    if not {'URL', 'Company Name', 'Tag'}.issubset(df.columns):
        return "The Excel file must contain 'URL', 'Company Name', and 'Tag' columns."
    df.to_csv(output_file, index=False)
    return "File uploaded and saved successfully."

def tag_news(url, company_name, tag):
    """Handles tagging of news items."""
    if not os.path.exists(output_file):
        return "No uploaded data found. Please upload a file first."
    df = pd.read_csv(output_file)
    new_entry = pd.DataFrame({'URL': [url], 'Company Name': [company_name], 'Tag': [tag]})
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(output_file, index=False)
    return f"Saved tag: {tag} for URL: {url}"

def show_summary():
    """Displays summary of tagging results."""
    if not os.path.exists(output_file):
        return "No tagging data found."
    df = pd.read_csv(output_file)
    total = len(df)
    yes_count = len(df[df['Tag'] == 'Yes'])
    no_count = len(df[df['Tag'] == 'No'])
    return f"Total URLs: {total}\nRelated to Company (Yes): {yes_count}\nNot Related to Company (No): {no_count}"

def main():
    parser = argparse.ArgumentParser(description="Run the Gradio News Tagging App")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the app on (default: 7860)")
    parser.add_argument("--share", action="store_true", help="Generate a public Gradio link")
    args = parser.parse_args()
    
    upload_interface = gr.Interface(fn=upload_excel, 
                                   inputs=[gr.File(label="Upload Excel File", file_types=[".xlsx"]), gr.Textbox(label="Admin Password", type="password")], 
                                   outputs=gr.Textbox(label="Upload Status"),
                                   title="Upload Excel File")
    
    tag_interface = gr.Interface(fn=tag_news, 
                                 inputs=[gr.Textbox(label="News URL"), gr.Textbox(label="Company Name"), gr.Radio(choices=["Yes", "No"], label="Is this news related to the company?")], 
                                 outputs=gr.Textbox(label="Tagging Status"),
                                 title="Tag News URLs")
    
    summary_interface = gr.Interface(fn=show_summary, 
                                     inputs=[], 
                                     outputs=gr.Textbox(label="Summary"),
                                     title="Tagging Summary")
    
    gr.TabbedInterface([upload_interface, tag_interface, summary_interface], ["Upload File", "Tag News", "Summary"]).launch(share=args.share, server_port=args.port)

if __name__ == "__main__":
    main()
