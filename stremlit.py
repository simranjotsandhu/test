import argparse
import gradio as gr
import pandas as pd
import os

# Global variable to store tagging results
output_file = "tagged_results.csv"

def upload_excel(file):
    """Handles file upload and validates the format."""
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

    with gr.Blocks() as demo:
        gr.Markdown("# News Tagging Application")
        
        with gr.Tab("Upload File"):
            gr.Markdown("Upload an Excel file with 'URL', 'Company Name', and 'Tag' columns.")
            upload_component = gr.File(label="Upload Excel File", file_types=[".xlsx"])
            upload_button = gr.Button("Upload")
            upload_output = gr.Textbox(label="Upload Status")
            upload_button.click(upload_excel, inputs=[upload_component], outputs=[upload_output])
        
        with gr.Tab("Tag News URLs"):
            gr.Markdown("Tag each news URL based on its relevance.")
            url_input = gr.Textbox(label="News URL")
            company_input = gr.Textbox(label="Company Name")
            tag_input = gr.Radio(choices=["Yes", "No"], label="Is this news related to the company?")
            tag_button = gr.Button("Save Tag")
            tag_output = gr.Textbox(label="Tagging Status")
            tag_button.click(tag_news, inputs=[url_input, company_input, tag_input], outputs=[tag_output])
        
        with gr.Tab("Summary"):
            summary_button = gr.Button("Show Summary")
            summary_output = gr.Textbox(label="Summary")
            summary_button.click(show_summary, inputs=[], outputs=[summary_output])
    
    demo.launch(share=args.share, server_port=args.port)

if __name__ == "__main__":
    main()
