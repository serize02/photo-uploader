import io
import json
import streamlit as st
from PIL import Image
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = '13W4bQZt9p4-v01Q2reeg4fA_MwUAc4yk'

@st.cache_resource
def get_drive_service():
    try:
        if 'SERVICE_ACCOUNT_JSON' not in st.secrets:
            st.error('This page is not available anymore...')
            return None
            
        creds_info = (
            json.loads(st.secrets['SERVICE_ACCOUNT_JSON']) 
            if isinstance(st.secrets['SERVICE_ACCOUNT_JSON'], str)
            else st.secrets['SERVICE_ACCOUNT_JSON']
        )
        
        return build('drive', 'v3', 
                   credentials=service_account.Credentials.from_service_account_info(
                       creds_info,
                       scopes=SCOPES
                   ))
    except Exception:
        st.error('Cloud Storage Error')
        return None

def upload_to_drive(file_bytes, filename):
    try:
        service = get_drive_service()
        if not service:
            return None
            
        file_metadata = {'name': filename, 'parents': [FOLDER_ID]}
        media = MediaIoBaseUpload(file_bytes, mimetype='image/jpeg')
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='webViewLink'
        ).execute()
        return file.get('webViewLink')
    except Exception:
        st.error('Upload error, try again')
        return None

def main():
    st.set_page_config(page_title='Photo Uploader', layout="centered")
    st.title("📤 Upload a photo")
    
    uploaded_file = st.file_uploader('Select an image', type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='preview', use_column_width=True)
        
        if st.button('Upload to cloud'):
            with st.spinner('Uploading'):
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='JPEG')
                img_bytes.seek(0)
                
                link = upload_to_drive(img_bytes, uploaded_file.name)
                if link:
                    st.success('Process completed...')
                    st.markdown(f"[Open link]({link})")
                else:
                    st.error('An error occurred while trying to upload the photo')

if __name__ == "__main__":
    main()