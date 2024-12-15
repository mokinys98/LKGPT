import base64
import markdown2

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils import extract_email


#Markdown template of user bill
def create_bill_email(debt):
    markdown_body = f"""
# API Atsakymo Informacija

- **Isiskolinimas**: {debt:.5f}
- **Limitas**: ${'0.50€'}
---
    """
    # Konvertuojame Markdown į HTML
    return markdown2.markdown(markdown_body, extras=["fenced-code-blocks"])

#Markdown template for a new user greeting
def create_greeting_email():

    #Read info from .md file
    with open("Md files/Greeting.md", "r", encoding="utf-8") as file:
        markdown_body = file.read()

    # Konvertuojame Markdown į HTML
    return markdown2.markdown(markdown_body, extras=["fenced-code-blocks"])

# Funkcija sukurti el. laiško turinį Markdown formatu ir konvertuoti į HTML
def create_markdown_email_body(total_tokens, approx_cost_usd, response):
    #print(f"Sukuria el. laiško turinį Markdown formatu, konvertuoja jį į HTML.")

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
    return markdown2.markdown(markdown_body, extras=["fenced-code-blocks"])

# Funkcija siųsti HTML el. laišką
def send_html_email(service, sender, recipient, subject, html_content, thread_id=None, in_reply_to=None, references=None):
    print(f"Sending email...")
    """
    Siunčia HTML formatu paruoštą el. laišką per Gmail API, su threading laukais.

    Args:
        service: Autorizuotas Gmail API paslaugų objektas.
        sender (str): Siuntėjo el. pašto adresas.
        recipient (str): Gavėjo el. pašto adresas.
        subject (str): Laiško tema.
        html_content (str): Laiško turinys HTML formatu.
        thread_id (str): Esamo Gmail thread ID (jei norite susieti su esamu pokalbiu).
        in_reply_to (str): Pradinio laiško Message-ID (jei tai atsakymas).
        references (str): References laukelis (nurodo visų ankstesnių laiškų ID).

    Returns:
        dict: Gmail API atsakymas.
    """

    # Sukurkite MIMEText objektą su HTML turiniu
    message = MIMEText(html_content, "html")
    message["to"] = extract_email(recipient)
    message["from"] = sender
    message["subject"] = subject

     # Pridėkite threading laukus, jei jie pateikti
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
    if references:
        message["References"] = references

    # Kodavimas į Base64, kaip reikalauja Gmail API
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    body = {
        "raw": raw_message,
    }

    # Jei thread_id pateiktas, pridėkite jį į kūną
    if thread_id:
        body["threadId"] = thread_id

    try:
        # Siųskite el. laišką
        sent_message = service.users().messages().send(userId="me", body=body).execute()
        print(f"El. laiškas sėkmingai išsiųstas! Žinutės ID: {sent_message['id']}, siuntėjas: {sender}, gavėjas: {extract_email(recipient)}, tema: {subject}")
        return sent_message
    except Exception as e:
        print(f"Klaida siunčiant el. laišką: {e}")
        return Exception
         

if __name__ == '__main__':
    #html = create_markdown_email_body(339, 0.01017, "testas")
    html = create_greeting_email()
    print(html)

    