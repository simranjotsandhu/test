import argparse
import gradio as gr
import pandas as pd
import os
from fastapi import FastAPI, UploadFile, Form
from starlette.responses import JSONResponse

app = FastAPI()

# Global variable to store tagging results
output_file = "tagged_results.csv"
admin_password = "securepassword"  # Change this to a secure password

@app.post("/upload")
async def upload_excel(file: UploadFile, password: str = Form(...)):
    """Handles file upload and validates the format, protected by a password."""
    if password != admin_password:
        return JSONResponse(content={"error": "Unauthorized: Incorrect password."}, status_code=403)
    df = pd.read_excel(file.file)
    if not {'URL', 'Company Name', 'Tag'}.issubset(df.columns):
        return JSONResponse(content={"error": "The Excel file must contain 'URL', 'Company Name', and 'Tag' columns."}, status_code=400)
    df.to_csv(output_file, index=False)
    return {"message": "File uploaded and saved successfully."}

@app.post("/tag")
async def tag_news(url: str = Form(...), company_name: str = Form(...), tag: str = Form(...)):
    """Handles tagging of news items."""
    if not os.path.exists(output_file):
        return JSONResponse(content={"error": "No uploaded data found. Please upload a file first."}, status_code=400)
    df = pd.read_csv(output_file)
    new_entry = pd.DataFrame({'URL': [url], 'Company Name': [company_name], 'Tag': [tag]})
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(output_file, index=False)
    return {"message": f"Saved tag: {tag} for URL: {url}"}

@app.get("/summary")
async def show_summary():
    """Displays summary of tagging results."""
    if not os.path.exists(output_file):
        return JSONResponse(content={"error": "No tagging data found."}, status_code=400)
    df = pd.read_csv(output_file)
    total = len(df)
    yes_count = len(df[df['Tag'] == 'Yes'])
    no_count = len(df[df['Tag'] == 'No'])
    return {"Total URLs": total, "Related to Company (Yes)": yes_count, "Not Related to Company (No)": no_count}

def main():
    parser = argparse.ArgumentParser(description="Run the FastAPI News Tagging App")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the app on (default: 7860)")
    args = parser.parse_args()
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
