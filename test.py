import argparse
import gradio as gr
import pandas as pd
import os
import secrets
import random

# Global variables
output_file = "tagged_results.csv"
admin_password = "x"  # Change this to a secure password
credentials_file = "user_credentials.csv"

# Load dataset and assignment mappings
global news_data, user_to_rows, sets, set_to_users
news_data = []
user_to_rows = {}
sets = []
set_to_users = {}

# Admin: Upload Excel and Account IDs
def upload_excel(file, account_ids_file, password, num_sets, num_users_per_set):
    global news_data, user_to_rows, sets, set_to_users
    if password != admin_password:
        return "**Error:** Unauthorized - Incorrect password.", None, None, gr.update(visible=False), gr.update(visible=False)
    if file is None or account_ids_file is None:
        return "**Error:** Please upload both Excel and Account IDs files.", None, None, gr.update(visible=False), gr.update(visible=False)
    df = pd.read_excel(file.name)
    if not {'URL', 'Company Name', 'Tag'}.issubset(df.columns):
        return "**Error:** Excel file must contain 'URL', 'Company Name', and 'Tag'.", None, None, gr.update(visible=False), gr.update(visible=False)
    
    # Prepare news data
    news_data = [{'URL': row['URL'], 'Company Name': row['Company Name'], 'Tag': row.get('Tag', '')} for _, row in df.iterrows()]
    N = len(df)
    account_ids = open(account_ids_file.name).read().splitlines()
    
    # Validate set and user inputs
    num_sets = int(num_sets)
    num_users_per_set = int(num_users_per_set)
    if num_sets <= 0 or num_users_per_set <= 0:
        return "**Error:** Number of sets and users per set must be positive.", None, None, gr.update(visible=False), gr.update(visible=False)
    if len(account_ids) < num_users_per_set:
        return "**Error:** Not enough users to assign to sets.", None, None, gr.update(visible=False), gr.update(visible=False)
    
    # Divide rows into sets
    indices = list(range(N))
    # random.shuffle(indices)  # Uncomment if random row assignment is desired
    sets = [indices[i::num_sets] for i in range(num_sets)]
    
    # Assign sets to users
    set_to_users = {}
    for set_idx in range(num_sets):
        assigned_users = random.sample(account_ids, num_users_per_set)
        set_to_users[set_idx] = assigned_users
    
    # Compute user to row mapping
    user_to_sets = {account_id: [] for account_id in account_ids}
    for set_idx, users in set_to_users.items():
        for user in users:
            user_to_sets[user].append(set_idx)
    user_to_rows = {}
    for account_id in account_ids:
        assigned_sets = user_to_sets[account_id]
        rows = sum([sets[set_idx] for set_idx in assigned_sets], [])
        user_to_rows[account_id] = sorted(rows)  # Sort for consistent order
    
    # Generate credentials
    passwords = [secrets.token_urlsafe(8) for _ in account_ids]
    credentials_hidden = pd.DataFrame({
        'account_id': account_ids,
        'password': ['[Hidden]' for _ in account_ids]
    })
    credentials_full = pd.DataFrame({
        'account_id': account_ids,
        'password': passwords
    })
    credentials_full.to_csv(credentials_file, index=False)
    df.to_csv(output_file, index=False)  # Initial save of tagged results
    
    return "**Files uploaded, sets assigned, and credentials created successfully!**", credentials_hidden, credentials_full, gr.update(visible=True), gr.update(visible=True)

def toggle_passwords(show_passwords, hidden_df, full_df):
    return full_df if show_passwords else hidden_df

# User authentication
def authenticate(account_id, password):
    if not os.path.exists(credentials_file):
        return False
    credentials = pd.read_csv(credentials_file)
    user = credentials[(credentials['account_id'] == account_id) & (credentials['password'] == password)]
    return not user.empty

def user_login(account_id, password):
    global news_data
    if authenticate(account_id, password):
        assigned_rows = user_to_rows.get(account_id, [])
        if not assigned_rows:
            return ("**No rows assigned to this user.**", gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), 
                    gr.update(visible=False), gr.update(visible=False), [], -1, gr.update(visible=False), gr.update(visible=False))
        if news_data:
            first_row_idx = assigned_rows[0]
            news_url = news_data[first_row_idx]['URL']
            company_name = news_data[first_row_idx]['Company Name']
            embed_code = f'<iframe src="{news_url}" width="100%" height="500px"></iframe>'
            return ("**Authenticated ✅**", gr.update(visible=False), gr.update(visible=False), gr.update(value=news_url, visible=True), 
                    gr.update(value=company_name, visible=True), gr.update(value=embed_code, visible=True), assigned_rows, 0, 
                    gr.update(visible=True), gr.update(interactive=False, visible=True))
        else:
            return ("**No news data found.**", gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), 
                    gr.update(visible=False), gr.update(visible=False), [], -1, gr.update(visible=False), gr.update(visible=False))
    else:
        return ("**Authentication failed.**", gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), 
                gr.update(visible=False), gr.update(visible=False), [], -1, gr.update(visible=False), gr.update(visible=False))

def submit_tag(account_id, password, user_assigned_rows, user_current_idx, tag):
    global news_data
    if not authenticate(account_id, password):
        return "**Authentication failed.**", "", "", user_current_idx
    if not user_assigned_rows or user_current_idx >= len(user_assigned_rows):
        return "**All assigned records tagged.**", "", "", user_current_idx
    row_idx = user_assigned_rows[user_current_idx]
    if 0 <= row_idx < len(news_data):
        news_data[row_idx]['Tag'] = tag
        pd.DataFrame(news_data).to_csv(output_file, index=False)
    user_current_idx += 1
    if user_current_idx < len(user_assigned_rows):
        next_row_idx = user_assigned_rows[user_current_idx]
        next_url = news_data[next_row_idx]['URL']
        next_company = news_data[next_row_idx]['Company Name']
        next_embed = f'<iframe src="{next_url}" width="100%" height="500px"></iframe>'
        return next_url, next_company, next_embed, user_current_idx
    else:
        return "**All assigned records tagged.**", "", "", user_current_idx

def show_summary(password):
    if password != admin_password:
        return gr.update(visible=False), gr.update(visible=False)
    if not os.path.exists(output_file):
        return gr.update(value=pd.DataFrame({"Error": ["No tagging data found."]}), visible=True), gr.update(visible=False)
    df = pd.read_csv(output_file)
    yes_count = df[df['Tag'] == 'Yes'].shape[0]
    no_count = df[df['Tag'] == 'No'].shape[0]
    summary_df = pd.DataFrame({"Tag": ["Yes", "No"], "Count": [yes_count, no_count]})
    assignment_data = [{"Set Index": set_idx, "Number of Rows": len(sets[set_idx]), "Assigned Users": ", ".join(set_to_users[set_idx])} 
                      for set_idx in range(len(sets))]
    assignment_df = pd.DataFrame(assignment_data)
    return gr.update(value=summary_df, visible=True), gr.update(value=assignment_df, visible=True)

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
            num_sets_input = gr.Number(label="Number of Sets", value=1, precision=0)
            num_users_per_set_input = gr.Number(label="Number of Users per Set", value=1, precision=0)
            upload_btn = gr.Button("Upload", variant="primary")
            upload_status = gr.Markdown()
            credentials_table = gr.DataFrame(visible=False)
            show_passwords = gr.Checkbox(label="Show Passwords", value=False, visible=False)
            hidden_credentials = gr.State(None)
            full_credentials = gr.State(None)

            upload_btn.click(
                upload_excel,
                [excel_file, account_ids_file, admin_pwd, num_sets_input, num_users_per_set_input],
                [upload_status, credentials_table, full_credentials, credentials_table, show_passwords]
            ).then(
                lambda df: df,
                inputs=[credentials_table],
                outputs=[hidden_credentials]
            )

            show_passwords.change(
                toggle_passwords,
                inputs=[show_passwords, hidden_credentials, full_credentials],
                outputs=[credentials_table]
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
            user_assigned_rows = gr.State()
            user_current_idx = gr.State()
            tag_input = gr.Radio(["Yes", "No"], label="Related?", visible=False)
            tag_btn = gr.Button("Submit", interactive=False, visible=False, variant="primary")

            login_btn.click(
                user_login,
                [user_id, user_pwd],
                [user_account_display, user_id, user_pwd, url_display, company_display, preview, user_assigned_rows, user_current_idx, tag_input, tag_btn]
            ).then(
                lambda account_id: gr.update(value=f'**Logged in as:** {account_id}', visible=True),
                inputs=[user_id],
                outputs=[user_account_display]
            ).then(
                lambda _: gr.update(visible=False),
                inputs=[user_id],
                outputs=[login_btn]
            )

            tag_input.change(
                lambda choice: gr.update(interactive=True),
                inputs=[tag_input],
                outputs=[tag_btn]
            )

            tag_btn.click(
                submit_tag,
                inputs=[user_id, user_pwd, user_assigned_rows, user_current_idx, tag_input],
                outputs=[url_display, company_display, preview, user_current_idx]
            ).then(
                lambda idx, rows: gr.update(interactive=False) if idx >= len(rows) else gr.update(interactive=True),
                inputs=[user_current_idx, user_assigned_rows],
                outputs=[tag_btn]
            )

        with gr.Tab("Summary"):
            summary_pwd = gr.Textbox(label="Admin Password", type="password")
            summary_btn = gr.Button("Show Summary", variant="primary")
            summary_output = gr.DataFrame(visible=False)
            assignment_summary = gr.DataFrame(visible=False)

            summary_btn.click(
                show_summary,
                [summary_pwd],
                [summary_output, assignment_summary]
            )

    app.launch(share=args.share, server_port=args.port)

if __name__ == "__main__":
    main()
