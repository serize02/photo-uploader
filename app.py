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