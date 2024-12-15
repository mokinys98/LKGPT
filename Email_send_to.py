import base64
import markdown2
from email.mime.text import MIMEText
from utils import extract_email


# Funkcija sukurti el. laiško turinį Markdown formatu ir konvertuoti į HTML
def create_markdown_email_body(total_tokens, approx_cost_usd, response):
    print(f"Sukuria el. laiško turinį Markdown formatu, konvertuoja jį į HTML.")
    """
    Sukuria el. laiško turinį Markdown formatu, konvertuoja jį į HTML.
    Args:
        total_tokens (int): Naudotų tokenų skaičius.
        approx_cost_usd (float): Apskaičiuota kaina USD.
        response (str): API sugeneruotas atsakymas.

    Returns:
        str: HTML turinys paruoštas siuntimui.
    """
    # Markdown turinys
    markdown_body = f"""
    # API Atsakymo Informacija

    - **Naudoti tokenai**: {total_tokens}
    - **Apskaičiuota kaina**: ${approx_cost_usd:.5f}

    ---

    ## Atsakymas

    {response}
    """
    # Konvertuojame Markdown į HTML
    return markdown2.markdown(markdown_body)

# Funkcija siųsti HTML el. laišką
def send_html_email(service, sender, recipient, subject, html_content):
    print(f"Sending email...")
    """
    Siunčia HTML formatu paruoštą el. laišką per Gmail API.

    Args:
        service: Autorizuotas Gmail API paslaugų objektas.
        sender (str): Siuntėjo el. pašto adresas.
        recipient (str): Gavėjo el. pašto adresas.
        subject (str): Laiško tema.
        html_content (str): Laiško turinys HTML formatu.

    Returns:
        dict: Gmail API atsakymas.
    """
    # Sukurkite MIMEText objektą su HTML turiniu
    message = MIMEText(html_content, "html")
    message["to"] = extract_email(recipient)
    message["from"] = sender
    message["subject"] = subject

    # Kodavimas į Base64, kaip reikalauja Gmail API
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    body = {"raw": raw_message}

    try:
        # Siųskite el. laišką
        sent_message = service.users().messages().send(userId="me", body=body).execute()
        print(f"El. laiškas sėkmingai išsiųstas! Žinutės ID: {sent_message['id']}, siuntėjas: {sender}, gavėjas: {extract_email(recipient)}, tema: {subject}")
        return sent_message
    except Exception as e:
        print(f"Klaida siunčiant el. laišką: {e}")
        return None
         