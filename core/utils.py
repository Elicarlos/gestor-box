import requests
from django.conf import settings

def acionar_lampada(box_id, acao):
    """
    Envia comando para o Raspberry Pi acionar a lâmpada do box.
    Sempre printa o resultado (sucesso ou erro).
    """
    url = getattr(settings, "RASPBERRY_PI_URL", "http://127.0.0.1:5000/acionar")
    payload = {'box': box_id, 'acao': acao}
    try:
        resp = requests.post(url, json=payload, timeout=2)
        print(f"[REAL] POST para {url} | payload={payload} | status={resp.status_code} | resp={resp.text}")
    except Exception as e:
        print(f"[ERRO] Falha ao enviar comando para Raspberry Pi: box={box_id}, acao={acao} | erro={e}") 