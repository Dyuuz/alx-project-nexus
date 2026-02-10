from celery import shared_task
from django.conf import settings
import httpx

EMAIL_HOST_USER = settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD
MAIL_API_URL = settings.MAIL_API_URL

@shared_task
async def send_mail_helper(message, mail_recipient):
    
    url = MAIL_API_URL
    
    html_message = f"{message}"
    
    payload = {
        "SUBJECT": "New User Registration",
        "MESSAGE": "Hello",
        "SENDER_EMAIL": EMAIL_HOST_USER,
        "SENDER_PASSWORD": EMAIL_HOST_PASSWORD,
        "RECEIVER_EMAIL": mail_recipient,
        "HTML_MESSAGE": html_message,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result

    except httpx.ConnectError as e:
        print(f"[Mail Error] Connection failed: {str(e)}")
        
        return {"error": "ConnectionError", "message": str(e)}

    except httpx.TimeoutException as e:
        print(f"[Mail Error] Request timed out: {str(e)}")
        
        return {"error": "Timeout", "message": str(e)}

    except httpx.HTTPStatusError as e:
        print(f"[Mail Error] HTTP error: {str(e)}")
        
        return {"error": "HTTPError", "message": str(e)}

    except Exception as e:
        print(f"[Mail Error] Unexpected exception: {str(e)}")
        
        return {"error": "UnknownError", "message": str(e)}
