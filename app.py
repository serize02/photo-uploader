import io
import json
import streamlit as st
from PIL import Image
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Configuración (se carga desde Secrets)
SCOPES = ['https://www.googleapis.com/auth/drive.file']  # Permiso restringido
FOLDER_ID = '13W4bQZt9p4-v01Q2reeg4fA_MwUAc4yk'  # Reemplaza con tu ID de carpeta

@st.cache_resource  # Cachea la conexión para mejorar rendimiento
def get_drive_service():
    """Carga las credenciales de forma segura desde Streamlit Secrets"""
    try:
        # Opción 1: Desde Secrets de Streamlit (producción)
        if 'SERVICE_ACCOUNT_JSON' in st.secrets:
            creds = service_account.Credentials.from_service_account_info(
                st.secrets["SERVICE_ACCOUNT_JSON"],
                scopes=SCOPES
            )
        # Opción 2: Desde variable de entorno (desarrollo local)
        else:
            import os
            from dotenv import load_dotenv
            load_dotenv()  # Carga .env si existe
            creds = service_account.Credentials.from_service_account_info(
                json.loads(os.getenv("SERVICE_ACCOUNT_JSON")),
                scopes=SCOPES
            )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Error cargando credenciales: {str(e)}")
        return None

def upload_to_drive(file_bytes, filename):
    """Sube un archivo a Google Drive de forma segura"""
    try:
        service = get_drive_service()
        if not service:
            return None
            
        file_metadata = {
            'name': filename,
            'parents': [FOLDER_ID]
        }
        media = MediaIoBaseUpload(file_bytes, mimetype='image/jpeg')
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='webViewLink'
        ).execute()
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Error subiendo archivo: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="📤 Subidor Seguro a Drive", layout="centered")
    st.title("📤 Sube fotos a Drive (Seguro)")
    
    # Verificación de credenciales
    if not get_drive_service():
        st.error("⚠️ Configuración incompleta. Contacta al administrador.")
        return
    
    uploaded_file = st.file_uploader("Selecciona una imagen (JPEG/PNG)", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Vista previa", width=300)
        
        if st.button("Subir a Drive ⬆️"):
            with st.spinner("Subiendo de forma segura..."):
                img_bytes = io.BytesIO()
                image.save(img_bytes, format="JPEG")
                img_bytes.seek(0)
                
                link = upload_to_drive(img_bytes, uploaded_file.name)
                if link:
                    st.success("✅ ¡Foto subida con éxito!")
                    st.markdown(f"[Ver en Drive]({link})")
                    st.balloons()
                else:
                    st.error("❌ Error al subir. Revisa los logs.")

if __name__ == "__main__":
    main()