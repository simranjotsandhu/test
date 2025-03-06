      import argparse
import gradio as gr
import pandas as pd
import os
import secrets

# Global variables
output_file = "tagged_results.csv"
admin_password = "x"  # Change this to a secure password
credentials_file = "user_credentials.csv"

# Load dataset
global news_data
news_data = []

# Admin: Upload Excel and Account IDs

def upload_excel(file, account_ids_file, password):
    global news_data
    if password != admin_password:
        return "**Error:** Unauthorized - Incorrect password.", pd.DataFrame()
    if file is None or account_ids_file is None:
        return "**Error:** Please upload both Excel and Account IDs files.", pd.DataFrame()
    df = pd.read_excel(file.name)
    if not {'URL', 'Company Name', 'Tag'}.issubset(df.columns):
        return "**Error:** Excel file must contain 'URL', 'Company Name', and 'Tag'.", pd.DataFrame()
    df.to_csv("tagged_results.csv", index=False)
    news_data = df.to_dict(orient='records')

    account_ids = open(account_ids_file.name).read().splitlines()
    credentials = pd.DataFrame({
        'account_id': account_ids,
        'password': [secrets.token_urlsafe(8) for _ in account_ids]
    })
    credentials.to_csv(credentials_file, index=False)

    return "**Files uploaded and credentials created successfully!**", credentials

# User authentication

def authenticate(account_id, password):
    if not os.path.exists(credentials_file):
        return False
    credentials = pd.read_csv(credentials_file)
    user = credentials[(credentials['account_id'] == account_id) & (credentials['password'] == password)]
    return not user.empty

def tag_news(account_id, password, index, tag):
    global news_data
    if not authenticate(account_id, password):
        return "**Authentication failed.**", "", "", -1
    if index == -1 or not news_data:
        return "**All records tagged.**", "", "", -1
    if 0 <= index < len(news_data):
        news_data[index]['Tag'] = tag
        pd.DataFrame(news_data).to_csv(output_file, index=False)
    if index + 1 < len(news_data):
        next_url = news_data[index + 1]['URL']
        embed_code = f'<iframe src="{next_url}" width="100%" height="500px"></iframe>'
        return next_url, news_data[index + 1]['Company Name'], embed_code, index + 1
    else:
        return "**All records tagged.**", "", "", -1

def show_summary(password):
    if password != admin_password:
        return gr.update(visible=False)
    if not os.path.exists("tagged_results.csv"):
        return gr.update(value=pd.DataFrame({"Error": ["No tagging data found."]}), visible=True)
    df = pd.read_csv("tagged_results.csv")
    yes_count = df[df['Tag'] == 'Yes'].shape[0]
    no_count = df[df['Tag'] == 'No'].shape[0]
    return gr.update(value=pd.DataFrame({"Tag": ["Yes", "No"], "Count": [yes_count, no_count]}), visible=True)

# Main app

def main():
    parser = argparse.ArgumentParser(description="Gradio News Tagging App")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    with gr.Blocks(theme=gr.themes.Ocean()) as app:
        gr.Markdown("# News Tagging Application")

        with gr.Tab("Upload File"):
            admin_pwd = gr.Textbox(label="Admin Password", type="password")
            excel_file = gr.File(label="Excel File (.xlsx)")
            account_ids_file = gr.File(label="Upload Account IDs (.txt)")
            upload_btn = gr.Button("Upload", variant="primary")
            upload_status = gr.Markdown()
            credentials_table = gr.DataFrame()

            upload_btn.click(
                upload_excel, 
                [excel_file, account_ids_file, admin_pwd],
                [upload_status, credentials_table]
            )

        with gr.Tab("Tag News"):
            with gr.Row():
                user_account_display = gr.Markdown(visible=False)
                time_spent_display = gr.Markdown(visible=False)
            auth_status = gr.Markdown()
            user_id = gr.Textbox(label="Account ID")
            user_pwd = gr.Textbox(label="User Password", type="password")
            login_btn = gr.Button("Login", variant="primary")
            url_display = gr.Markdown(visible=False)
            company_display = gr.Textbox(label="Company Name", interactive=False, visible=False)
            preview = gr.HTML(visible=False)
            idx_input = gr.Number(label="Index", value=0, interactive=False, visible=False)
            tag_input = gr.Radio(["Yes", "No"], label="Related?", visible=False)
            tag_btn = gr.Button("Submit", interactive=False, visible=False, variant="primary")

            def user_login(account_id, password):
                global news_data
                if authenticate(account_id, password):
                    if news_data:
                        news_url = news_data[0]['URL']
                        company_name = news_data[0]['Company Name']
                        embed_code = f'<iframe src="{news_url}" width="100%" height="500px"></iframe>'
                        return ("**Authenticated ✅**", gr.update(visible=False), gr.update(visible=False), gr.update(value=news_url, visible=True), gr.update(value=company_name, visible=True), gr.update(value=embed_code, visible=True), gr.update(value=0, visible=True), gr.update(visible=True), gr.update(interactive=False, visible=True))
                    else:
                        return ("**No news data found.**", gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
                else:
                    return ("**Authentication failed.**", gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
            
            login_btn.click(
                user_login, 
                [user_id, user_pwd], 
                [user_account_display, user_id, user_pwd, url_display, company_display, preview, idx_input, tag_input, tag_btn]
            ).then(
                lambda account_id: gr.update(value=f'**Logged in as:** {account_id}', visible=True),
                inputs=[user_id],
                outputs=[user_account_display]
            ).then(
                lambda _: gr.update(visible=True),
                inputs=[user_id],
                outputs=[time_spent_display]
            )

            tag_input.change(
                lambda choice: gr.update(interactive=True), 
                inputs=[tag_input], 
                outputs=[tag_btn]
            )

            tag_btn.click(
                tag_news,
                inputs=[user_id, user_pwd, idx_input, tag_input],
                outputs=[url_display, company_display, preview, idx_input]
            ).then(
                lambda idx: gr.update(interactive=False) if idx == -1 else gr.update(interactive=True),
                inputs=[idx_input],
                outputs=[tag_btn]
            )

        with gr.Tab("Summary"):
            summary_pwd = gr.Textbox(label="Admin Password", type="password")
            summary_btn = gr.Button("Show Summary", variant="primary")
            summary_output = gr.DataFrame(visible=False)

            summary_btn.click(show_summary, [summary_pwd], summary_output)

    app.launch(share=args.share, server_port=args.port)

if __name__ == "__main__":
    main()
