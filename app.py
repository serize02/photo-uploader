import io
import json
import traceback
import streamlit as st
from PIL import Image
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

# Configuración
SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = 'TU_FOLDER_ID'  # Reemplaza con tu ID real

def get_drive_service():
    """Obtiene el servicio de Drive con manejo de errores mejorado"""
    try:
        if 'SERVICE_ACCOUNT_JSON' not in st.secrets:
            st.session_state.error = "Configuración incompleta"
            return None
            
        creds_info = (
            json.loads(st.secrets["SERVICE_ACCOUNT_JSON"]) 
            if isinstance(st.secrets["SERVICE_ACCOUNT_JSON"], str)
            else st.secrets["SERVICE_ACCOUNT_JSON"]
        )
        
        creds = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=SCOPES
        )
        return build('drive', 'v3', credentials=creds)
        
    except Exception as e:
        st.session_state.error = f"Error de conexión: {type(e).__name__}"
        return None

def upload_to_drive(file_bytes, filename):
    """Función mejorada con registro de errores oculto"""
    try:
        service = get_drive_service()
        if not service:
            return None
            
        file_metadata = {
            'name': filename,
            'parents': [FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(
            file_bytes, 
            mimetype='image/jpeg',
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='webViewLink'
        ).execute()
        
        return file.get('webViewLink')
        
    except HttpError as e:
        error_details = {
            "code": e.resp.status,
            "message": json.loads(e.content.decode())['error']['message'],
            "reason": json.loads(e.content.decode())['error']['errors'][0]['reason']
        }
        st.session_state.error_details = error_details
        return None
        
    except Exception as e:
        st.session_state.error_details = {
            "type": type(e).__name__,
            "message": str(e)
        }
        return None

def show_error_modal():
    """Muestra un modal con opción para ver detalles técnicos (ocultos por defecto)"""
    if hasattr(st.session_state, 'error_details'):
        with st.expander("⚠️ Ver detalles técnicos (solo para administradores)"):
            st.json(st.session_state.error_details)
            st.code(traceback.format_exc())
        st.session_state.error_details = None  # Limpia después de mostrar

def main():
    st.set_page_config(page_title="Subidor de Fotos", layout="centered")
    st.title("📤 Sube tus fotos")
    
    uploaded_file = st.file_uploader("Selecciona una imagen", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Vista previa", use_column_width=True)
        
        if st.button("Subir a Drive"):
            with st.spinner("Subiendo..."):
                img_bytes = io.BytesIO()
                image.save(img_bytes, format="JPEG")
                img_bytes.seek(0)
                
                link = upload_to_drive(img_bytes, uploaded_file.name)
                if link:
                    st.success("✅ ¡Foto subida con éxito!")
                    st.markdown(f"[Abrir en Drive]({link})")
                    st.balloons()
                else:
                    st.error("❌ Error al subir la foto")
                    show_error_modal()

if __name__ == "__main__":
    main()