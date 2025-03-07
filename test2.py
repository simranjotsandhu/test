import argparse
import gradio as gr
import pandas as pd
import os
import secrets
import random
import json
import shutil

# Determine the script's directory for consistent file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define global file paths using absolute paths
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "tagged_results.csv")
ADMIN_PASSWORD = "adminpass"  # Change to a secure password in production
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "user_credentials.csv")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "user_progress.csv")
ADMIN_STATE_FILE = os.path.join(SCRIPT_DIR, "admin_state.json")
UPLOADS_DIR = os.path.join(SCRIPT_DIR, "uploads")
USER_ASSIGNMENTS_FILE = os.path.join(SCRIPT_DIR, "user_assignments.json")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Global variables for data (placeholders until populated)
news_data = []
user_to_rows = {}
sets = []
set_to_users = {}

# Load admin state from file
def load_admin_state():
    """Load the admin state from admin_state.json, or initialize if not present."""
    if os.path.exists(ADMIN_STATE_FILE):
        with open(ADMIN_STATE_FILE, "r") as f:
            return json.load(f)
    return {"logged_in": False, "excel_file": None, "account_ids_file": None, "num_sets": 1, "num_users_per_set": 1}

# Save admin state to file
def save_admin_state(state):
    """Save the admin state to admin_state.json."""
    with open(ADMIN_STATE_FILE, "w") as f:
        json.dump(state, f)

# Load hidden credentials for display
def load_hidden_credentials():
    """Load credentials from user_credentials.csv with hidden passwords."""
    if os.path.exists(CREDENTIALS_FILE):
        credentials = pd.read_csv(CREDENTIALS_FILE)
        if not credentials.empty:
            return pd.DataFrame({
                'account_id': credentials['account_id'],
                'password': ['[Hidden]' for _ in credentials['account_id']]
            })
    return pd.DataFrame(columns=['account_id', 'password'])

# Load full credentials (for showing passwords)
def load_full_credentials():
    """Load full credentials from user_credentials.csv."""
    if os.path.exists(CREDENTIALS_FILE):
        return pd.read_csv(CREDENTIALS_FILE)
    return pd.DataFrame(columns=['account_id', 'password'])

# Admin login function
def admin_login(username, password):
    """Handle admin login, updating the interface with saved state."""
    if username == "admin" and password == ADMIN_PASSWORD:
        state = load_admin_state()
        state["logged_in"] = True
        save_admin_state(state)
        hidden_credentials = load_hidden_credentials()
        return (
            gr.update(visible=False),  # Hide login column
            gr.update(visible=True),   # Show upload column
            gr.update(value=state.get("excel_file", "No file uploaded")),
            gr.update(value=state.get("account_ids_file", "No file uploaded")),
            gr.update(value=state.get("num_sets", 1)),
            gr.update(value=state.get("num_users_per_set", 1)),
            gr.update(value="Login successful!"),
            gr.update(value=hidden_credentials)  # Update credentials table
        )
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(value=""),
        gr.update(value=""),
        gr.update(value=1),
        gr.update(value=1),
        gr.update(value="Incorrect credentials"),
        gr.update(value=None)
    )

# Admin logout function
def admin_logout():
    """Handle admin logout, resetting visibility and clearing state."""
    state = load_admin_state()
    state["logged_in"] = False
    save_admin_state(state)
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(value=""),
        gr.update(value=""),
        gr.update(value=1),
        gr.update(value=1),
        gr.update(value="Logged out"),
        gr.update(value=None)
    )

# Admin reset function
def admin_reset():
    """Reset the app state by removing saved files and state."""
    for file in [ADMIN_STATE_FILE, CREDENTIALS_FILE, PROGRESS_FILE, USER_ASSIGNMENTS_FILE, OUTPUT_FILE]:
        if os.path.exists(file):
            os.remove(file)
    for file in ["news_data.xlsx", "account_ids.txt"]:
        file_path = os.path.join(UPLOADS_DIR, file)
        if os.path.exists(file_path):
            os.remove(file_path)
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(value=""),
        gr.update(value=""),
        gr.update(value=1),
        gr.update(value=1),
        gr.update(value="State reset"),
        gr.update(value=None)
    )

# Admin upload function
def admin_upload(excel_file, account_ids_file, num_sets, num_users_per_set):
    """Handle file uploads, process data, and generate credentials."""
    global news_data, user_to_rows, sets, set_to_users
    state = load_admin_state()

    # Save new files if uploaded
    if excel_file:
        excel_path = os.path.join(UPLOADS_DIR, "news_data.xlsx")
        shutil.copy(excel_file, excel_path)
        state["excel_file"] = excel_path
    if account_ids_file:
        account_ids_path = os.path.join(UPLOADS_DIR, "account_ids.txt")
        shutil.copy(account_ids_file, account_ids_path)
        state["account_ids_file"] = account_ids_path

    state["num_sets"] = int(num_sets)
    state["num_users_per_set"] = int(num_users_per_set)
    save_admin_state(state)

    excel_file_path = state.get("excel_file")
    account_ids_file_path = state.get("account_ids_file")
    if not excel_file_path or not account_ids_file_path or not os.path.exists(excel_file_path) or not os.path.exists(account_ids_file_path):
        return (
            gr.update(value="**Error:** Files not uploaded."),
            None,
            gr.update(value=state.get("excel_file", "No file uploaded")),
            gr.update(value=state.get("account_ids_file", "No file uploaded"))
        )

    # Process Excel file
    df = pd.read_excel(excel_file_path)
    required_columns = {'URL', 'Company Name', 'Tag'}
    if not required_columns.issubset(df.columns):
        return (
            gr.update(value="**Error:** Excel file must contain 'URL', 'Company Name', and 'Tag'."),
            None,
            gr.update(value=state.get("excel_file")),
            gr.update(value=state.get("account_ids_file"))
        )

    news_data = [{'URL': row['URL'], 'Company Name': row['Company Name'], 'Tag': row.get('Tag', '')} for _, row in df.iterrows()]
    N = len(df)
    with open(account_ids_file_path, "r") as f:
        account_ids = f.read().splitlines()
    M = len(account_ids)

    num_sets = int(num_sets)
    num_users_per_set = int(num_users_per_set)
    if num_sets <= 0 or num_users_per_set <= 0:
        return (
            gr.update(value="**Error:** Number of sets and users per set must be positive."),
            None,
            gr.update(value=state.get("excel_file")),
            gr.update(value=state.get("account_ids_file"))
        )

    # Divide rows into sets
    indices = list(range(N))
    sets = [indices[i::num_sets] for i in range(num_sets)]

    # Distribute users across sets
    base_users_per_set = M // num_sets
    extra_users = M % num_sets
    set_to_users = {}
    shuffled_users = account_ids.copy()
    random.shuffle(shuffled_users)
    user_idx = 0
    for set_idx in range(num_sets):
        num_users = base_users_per_set + (1 if set_idx < extra_users else 0)
        assigned_users = shuffled_users[user_idx:user_idx + num_users]
        set_to_users[set_idx] = assigned_users
        user_idx += num_users

    # Compute user to row mapping
    user_to_sets = {account_id: [] for account_id in account_ids}
    for set_idx, users in set_to_users.items():
        for user in users:
            user_to_sets[user].append(set_idx)
    user_to_rows = {}
    for account_id in account_ids:
        assigned_sets = user_to_sets[account_id]
        rows = sum([sets[set_idx] for set_idx in assigned_sets], [])
        user_to_rows[account_id] = sorted(rows)

    # Save user assignments
    with open(USER_ASSIGNMENTS_FILE, "w") as f:
        json.dump(user_to_rows, f)

    # Generate credentials
    passwords = [secrets.token_urlsafe(8) for _ in account_ids]
    credentials_hidden = pd.DataFrame({'account_id': account_ids, 'password': ['[Hidden]' for _ in account_ids]})
    credentials_full = pd.DataFrame({'account_id': account_ids, 'password': passwords})
    credentials_full.to_csv(CREDENTIALS_FILE, index=False)
    df.to_csv(OUTPUT_FILE, index=False)

    # Initialize user progress
    progress_df = pd.DataFrame({'account_id': account_ids, 'current_idx': [0] * len(account_ids)})
    progress_df.to_csv(PROGRESS_FILE, index=False)

    return (
        gr.update(value="**Files uploaded, sets assigned, and credentials created successfully!**"),
        credentials_hidden,
        gr.update(value=state["excel_file"]),
        gr.update(value=state["account_ids_file"])
    )

# Authenticate user
def authenticate(account_id, password):
    """Authenticate a user based on account ID and password."""
    if not os.path.exists(CREDENTIALS_FILE):
        return False, "No credentials found. Please upload files first."
    credentials = pd.read_csv(CREDENTIALS_FILE)
    if account_id in credentials['account_id'].values:
        stored_password = credentials[credentials['account_id'] == account_id]['password'].values[0]
        if stored_password == password:
            return True, "Login successful!"
        return False, "Incorrect password."
    return False, "Account ID not found."

# Tag news function
def tag_news(account_id, password, tag):
    """Handle tagging of news items for authenticated users."""
    success, message = authenticate(account_id, password)
    if not success:
        return message, "Please log in to tag news items."

    # Load user assignments
    if not os.path.exists(USER_ASSIGNMENTS_FILE):
        return "Assignments not found. Please ensure files are uploaded.", ""
    with open(USER_ASSIGNMENTS_FILE, "r") as f:
        user_to_rows = json.load(f)

    if account_id not in user_to_rows:
        return "No rows assigned to this user.", ""

    assigned_rows = user_to_rows[account_id]

    # Load user progress
    if not os.path.exists(PROGRESS_FILE):
        return "Progress file not found. Please ensure files are uploaded.", ""
    progress_df = pd.read_csv(PROGRESS_FILE)
    if account_id not in progress_df['account_id'].values:
        return "User not found in progress file.", ""

    current_idx = progress_df[progress_df['account_id'] == account_id]['current_idx'].values[0]

    if current_idx >= len(assigned_rows):
        return "All assigned rows tagged!", "All items tagged."

    row_idx = assigned_rows[current_idx]

    # Load tagged data
    if not os.path.exists(OUTPUT_FILE):
        return "Tagged data file not found. Please ensure files are uploaded.", ""
    tagged_df = pd.read_csv(OUTPUT_FILE)

    # Update the tag
    tagged_df.at[row_idx, 'Tag'] = tag
    tagged_df.to_csv(OUTPUT_FILE, index=False)

    # Update progress
    progress_df.loc[progress_df['account_id'] == account_id, 'current_idx'] = current_idx + 1
    progress_df.to_csv(PROGRESS_FILE, index=False)

    # Get next item if available
    next_idx = current_idx + 1
    if next_idx < len(assigned_rows):
        next_row = tagged_df.iloc[assigned_rows[next_idx]]
        next_item = f"Next item: {next_row['Company Name']} - {next_row['URL']}"
    else:
        next_item = "All items tagged."

    return f"Tagged row {current_idx + 1}/{len(assigned_rows)}.", next_item

# View summary function
def view_summary():
    """Generate a summary of tagged news items."""
    if not os.path.exists(OUTPUT_FILE):
        return "No data tagged yet."
    df = pd.read_csv(OUTPUT_FILE)
    tagged = df[df['Tag'].notna() & (df['Tag'] != '')]
    if tagged.empty:
        return "No tags have been assigned yet."
    summary = tagged['Tag'].value_counts().to_dict()
    return "\n".join([f"{tag}: {count}" for tag, count in summary.items()])

# Toggle passwords visibility
def toggle_passwords(show):
    """Toggle between showing full or hidden passwords."""
    return load_full_credentials() if show else load_hidden_credentials()

# Main application function
def main():
    parser = argparse.ArgumentParser(description="Gradio News Tagging App")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    state = load_admin_state()
    admin_logged_in = state["logged_in"]

    with gr.Blocks(theme=gr.themes.Ocean()) as app:
        gr.Markdown("# News Tagging Application")

        # Upload File Tab
        with gr.Tab("Upload File"):
            with gr.Column(visible=not admin_logged_in) as login_col:
                admin_username = gr.Textbox(label="Admin Username")
                admin_password_input = gr.Textbox(label="Admin Password", type="password")
                admin_login_btn = gr.Button("Login")
                admin_auth_status = gr.Markdown()

            with gr.Column(visible=admin_logged_in) as upload_col:
                current_excel_label = gr.Textbox(label="Current Excel File", value=state.get("excel_file", "No file uploaded"), interactive=False)
                current_account_ids_label = gr.Textbox(label="Current Account IDs File", value=state.get("account_ids_file", "No file uploaded"), interactive=False)
                excel_file = gr.File(label="Excel File (.xlsx)", type="filepath")
                account_ids_file = gr.File(label="Account IDs (.txt)", type="filepath")
                num_sets_input = gr.Number(label="Number of Sets", value=state.get("num_sets", 1), precision=0)
                num_users_per_set_input = gr.Number(label="Number of Users per Set", value=state.get("num_users_per_set", 1), precision=0)
                upload_btn = gr.Button("Upload", variant="primary")
                logout_btn = gr.Button("Logout", variant="secondary")
                reset_btn = gr.Button("Reset", variant="secondary")
                upload_status = gr.Markdown()
                credentials_table = gr.DataFrame(
                    value=load_hidden_credentials() if admin_logged_in else None,
                    headers=['account_id', 'password'],
                    label="User Credentials"
                )
                show_passwords = gr.Checkbox(label="Show Passwords", value=False)

            admin_login_btn.click(
                fn=admin_login,
                inputs=[admin_username, admin_password_input],
                outputs=[login_col, upload_col, current_excel_label, current_account_ids_label, num_sets_input, num_users_per_set_input, admin_auth_status, credentials_table]
            )
            logout_btn.click(fn=admin_logout, outputs=[login_col, upload_col, current_excel_label, current_account_ids_label, num_sets_input, num_users_per_set_input, admin_auth_status, credentials_table])
            reset_btn.click(fn=admin_reset, outputs=[login_col, upload_col, current_excel_label, current_account_ids_label, num_sets_input, num_users_per_set_input, admin_auth_status, credentials_table])
            upload_btn.click(fn=admin_upload, inputs=[excel_file, account_ids_file, num_sets_input, num_users_per_set_input], outputs=[upload_status, credentials_table, current_excel_label, current_account_ids_label])
            show_passwords.change(fn=toggle_passwords, inputs=[show_passwords], outputs=[credentials_table])

        # Tag News Tab
        with gr.Tab("Tag News"):
            account_id_input = gr.Textbox(label="Account ID")
            password_input = gr.Textbox(label="Password", type="password")
            tag_input = gr.Textbox(label="Tag")
            submit_tag_btn = gr.Button("Submit Tag")
            tag_status = gr.Markdown()
            next_item = gr.Markdown()

            submit_tag_btn.click(
                fn=tag_news,
                inputs=[account_id_input, password_input, tag_input],
                outputs=[tag_status, next_item]
            )

        # Summary Tab
        with gr.Tab("Summary"):
            summary_btn = gr.Button("View Summary")
            summary_output = gr.Textbox(label="Tag Summary")
            summary_btn.click(fn=view_summary, outputs=[summary_output])

    app.launch(share=args.share, server_port=args.port)

if __name__ == "__main__":
    main()
