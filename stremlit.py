import streamlit as st
import pandas as pd
from io import BytesIO

categories = ['Politics', 'Sports', 'Entertainment', 'Technology', 'Business', 'Health', 'Other']

st.title("News URL Classification Tool")

uploaded_file = st.file_uploader("Upload an Excel file with news URLs", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    if 'URL' not in df.columns:
        st.error("The uploaded Excel file must contain a 'URL' column.")
    else:
        df['Category'] = ''
        df['Comments'] = ''
        
        st.write("Classify the news URLs:")
        for index, row in df.iterrows():
            st.markdown(f"### {row['URL']}")
            
            category = st.selectbox(f"Select category for URL {index + 1}", categories, key=f"category_{index}")
            df.at[index, 'Category'] = category
            
            comment = st.text_area(f"Additional comments for URL {index + 1}", key=f"comment_{index}")
            df.at[index, 'Comments'] = comment
            
        if st.button("Export Classified Data to Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Classified URLs')
            output.seek(0)
            st.download_button(
                label="Download Classified Data",
                data=output,
                file_name="classified_urls.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
