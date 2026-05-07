import os
import base64
import logging
from datetime import datetime
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES      = ['https://www.googleapis.com/auth/gmail.readonly']
CREDS_FILE  = Path(__file__).resolve().parent.parent / 'gmail_credentials.json'
TOKEN_FILE  = Path(__file__).resolve().parent.parent / 'gmail_token.json'


def _get_service():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def buscar_respuestas(asunto_original: str, desde_fecha: datetime) -> list[dict]:
    """
    Busca en Gmail correos que sean respuestas al asunto del escalamiento.
    Retorna lista de dicts con remitente, fecha y cuerpo.
    """
    try:
        service  = _get_service()
        # Buscar por asunto — Gmail agrupa el hilo automáticamente
        query    = f'subject:"Re: {asunto_original}"'
        desde_ts = int(desde_fecha.timestamp())
        query   += f' after:{desde_ts}'

        results  = service.users().messages().list(
            userId='me', q=query, maxResults=20
        ).execute()

        mensajes = results.get('messages', [])
        respuestas = []

        for msg in mensajes:
            detalle = service.users().messages().get(
                userId='me', id=msg['id'], format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in detalle['payload']['headers']}
            cuerpo  = _extraer_cuerpo(detalle['payload'])
            fecha   = datetime.fromtimestamp(int(detalle['internalDate']) / 1000)

            respuestas.append({
                'mensaje_id': msg['id'],   # ← es el ID único de Gmail
                'remitente':  headers.get('From', 'Desconocido'),
                'fecha':      fecha.strftime('%d/%m/%Y %H:%M'),
                'asunto':     headers.get('Subject', ''),
                'cuerpo':     cuerpo[:1000],
            })

        return respuestas

    except Exception as e:
        logger.error(f'Error leyendo Gmail: {e}')
        return []


def _extraer_cuerpo(payload) -> str:
    """Extrae el texto plano del cuerpo del correo."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    data = payload.get('body', {}).get('data', '')
    if data:
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return ''