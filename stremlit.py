import gradio as gr
import pandas as pd
import os

# Global variable to store tagging results
tagged_data = []
output_file = 'tagged_results.csv'

# Function to handle file upload and parse the Excel file
def upload_excel(file):
    if file is None:
        return "Please upload an Excel file."
    df = pd.read_excel(file.name)
    if not {'URL', 'Company Name', 'Tag'}.issubset(df.columns):
        return "The Excel file must contain 'URL', 'Company Name', and 'Tag' columns."
    return df

# Function to handle tagging
def tag_news(url, company_name, tag):
    global tagged_data
    tagged_data.append({'URL': url, 'Company Name': company_name, 'Tag': tag})
    # Save the tagging result to a CSV file
    pd.DataFrame(tagged_data).to_csv(output_file, index=False)
    return f"Saved tag: {tag} for URL: {url}"

# Function to show the summary of tags
def show_summary():
    if not os.path.exists(output_file):
        return "No tagging data found."
    df = pd.read_csv(output_file)
    total = len(df)
    yes_count = len(df[df['Tag'] == 'Yes'])
    no_count = len(df[df['Tag'] == 'No'])
    return f"Total URLs: {total}\nRelated to Company (Yes): {yes_count}\nNot Related to Company (No): {no_count}"

# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("# News Tagging Application")
    gr.Markdown("Upload an Excel file with 'URL', 'Company Name', and 'Tag' columns.")

    upload_component = gr.File(label="Upload Excel File", file_count="single", type="file")
    upload_button = gr.Button("Upload")
    output_text = gr.Textbox(label="Upload Status")
    upload_button.click(upload_excel, inputs=[upload_component], outputs=[output_text])

    gr.Markdown("## Tag News URLs")
    url_input = gr.Textbox(label="News URL")
    company_input = gr.Textbox(label="Company Name")
    tag_input = gr.Radio(choices=["Yes", "No"], label="Is this news related to the company?")
    tag_button = gr.Button("Save Tag")
    tag_output = gr.Textbox(label="Tagging Status")
    tag_button.click(tag_news, inputs=[url_input, company_input, tag_input], outputs=[tag_output])

    gr.Markdown("## Tagging Summary")
    summary_button = gr.Button("Show Summary")
    summary_output = gr.Textbox(label="Summary")
    summary_button.click(show_summary, inputs=[], outputs=[summary_output])

demo.launch(share=True)
