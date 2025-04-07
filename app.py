import io
import json
import streamlit as st
from PIL import Image
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Configuración
SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = 'TU_FOLDER_ID'  # Reemplaza con tu ID de carpeta

@st.cache_resource
def get_drive_service():
    try:
        if 'SERVICE_ACCOUNT_JSON' not in st.secrets:
            st.error("No se encontró SERVICE_ACCOUNT_JSON en los secrets")
            return None
        
        # Debug: Verifica qué estamos recibiendo exactamente
        st.write("Tipo de dato recibido:", type(st.secrets["SERVICE_ACCOUNT_JSON"]))
        
        # Asegurarnos de que siempre sea un diccionario
        if isinstance(st.secrets["SERVICE_ACCOUNT_JSON"], str):
            try:
                creds_info = json.loads(st.secrets["SERVICE_ACCOUNT_JSON"])
            except json.JSONDecodeError:
                st.error("El contenido no es un JSON válido")
                st.text("Contenido recibido:")
                st.text(st.secrets["SERVICE_ACCOUNT_JSON"])
                return None
        else:
            creds_info = st.secrets["SERVICE_ACCOUNT_JSON"]
        
        # Verificación adicional
        if not isinstance(creds_info, dict):
            st.error(f"Se esperaba un diccionario pero se recibió: {type(creds_info)}")
            return None
            
        if "client_email" not in creds_info:
            st.error("El JSON no contiene client_email (formato incorrecto)")
            return None
        
        creds = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=SCOPES
        )
        return build('drive', 'v3', credentials=creds)
        
    except Exception as e:
        st.error(f"Error detallado: {str(e)}", icon="🚨")
        return None

def upload_to_drive(file_bytes, filename):
    """Sube archivos sin mostrar detalles técnicos"""
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
        st.error("Error al subir el archivo")
        return None

def main():
    """Interfaz limpia sin detalles técnicos"""
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
                    st.success("¡Foto subida con éxito!")
                    st.markdown(f"[Abrir en Drive]({link})")
                else:
                    st.error("Error al subir la foto")

if __name__ == "__main__":
    main()