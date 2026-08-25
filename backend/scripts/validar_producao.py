"""Smoke test de produção (só leitura, HTTP puro — não toca no banco). Roda antes
de reuniões/deploys importantes pra confirmar que API, app e site institucional
estão de pé e servindo o código esperado.

Uso:
    cd backend
    ..\\.venv\\Scripts\\python.exe scripts\\validar_producao.py

Pra checar também se um deploy de backend específico está mesmo no ar (não só
que o processo responde — confirma que o schema novo do /me foi publicado),
passe uma conta de teste via variáveis de ambiente (nunca colar credencial
aqui no arquivo nem no chat):
    $env:VALIDAR_PROD_USER = "..."
    $env:VALIDAR_PROD_SENHA = "..."
    ..\\.venv\\Scripts\\python.exe scripts\\validar_producao.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

API_BASE = "https://projetista-v2-api-alt.onrender.com"
APP_BASE = "https://camara-fria.icenexus.com.br"
SITE_BASE = "https://www.icenexus.com.br"
SITE_ROTAS = ("/", "/projeto-camara-fria", "/academia", "/acessar")

TIMEOUT = 15


def _request(url, payload=None, headers=None):
    headers = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # DNS, timeout, conexão recusada etc.
        return None, str(e).encode()


def checar(nome, status, ok_esperado=200):
    ok = status == ok_esperado
    print(f"[{'OK' if ok else 'FALHOU'}] {nome} -> HTTP {status}")
    return ok


def main() -> int:
    tudo_ok = True

    status, _ = _request(f"{API_BASE}/health")
    tudo_ok &= checar("Backend /health", status)

    status, _ = _request(APP_BASE)
    tudo_ok &= checar("Frontend app (camara-fria.icenexus.com.br)", status)

    for rota in SITE_ROTAS:
        status, _ = _request(f"{SITE_BASE}{rota}")
        tudo_ok &= checar(f"Site institucional {rota or '/'}", status)

    usuario = os.environ.get("VALIDAR_PROD_USER")
    senha = os.environ.get("VALIDAR_PROD_SENHA")
    if usuario and senha:
        status, body = _request(f"{API_BASE}/api/auth/token/", payload={"username": usuario, "password": senha})
        if status == 200:
            token = json.loads(body)["access"]
            status2, body2 = _request(f"{API_BASE}/api/auth/me/", headers={"Authorization": f"Bearer {token}"})
            campos = json.loads(body2) if status2 == 200 else {}
            schema_novo = "empresa_assinatura_fim" in campos and "empresa_trial_expirado" in campos
            print(f"[{'OK' if schema_novo else 'FALHOU'}] /api/auth/me/ com campos de trial (empresa_assinatura_fim, empresa_trial_expirado)")
            tudo_ok &= schema_novo
        else:
            print(f"[FALHOU] login da conta de teste -> HTTP {status}")
            tudo_ok = False
    else:
        print("[--] Login pulado (defina VALIDAR_PROD_USER/VALIDAR_PROD_SENHA pra checar o schema autenticado).")

    print()
    print("TUDO OK" if tudo_ok else "ALGO FALHOU — ver acima")
    return 0 if tudo_ok else 1


if __name__ == "__main__":
    sys.exit(main())
