"""Testa de ponta a ponta a jornada: trial (1 projeto) -> admin promove pra plano
pago -> trava se abre. HTTP puro, contas descartáveis criadas a cada execução.

Uso (local, padrão):
    cd backend
    ..\\.venv\\Scripts\\python.exe scripts\\testar_jornada_trial.py

Contra produção, passando um superadmin já existente (nunca colar a senha aqui
no arquivo nem no chat — só como variável de ambiente no seu terminal):
    $env:JORNADA_API_BASE = "https://projetista-v2-api-alt.onrender.com"
    $env:JORNADA_SUPERADMIN_USER = "..."
    $env:JORNADA_SUPERADMIN_SENHA = "..."
    ..\\.venv\\Scripts\\python.exe scripts\\testar_jornada_trial.py

Sem superadmin definido, só valida o comportamento do trial puro (1 projeto
ok, 2º bloqueado) — não testa a promoção de plano pelo admin.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

API_BASE = os.environ.get("JORNADA_API_BASE", "http://localhost:8000")
TIMEOUT = 15


def _req(method, path, payload=None, token=None):
    headers = {}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{API_BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
            return resp.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"detail": body.decode(errors="replace")}


def checar(nome, ok):
    print(f"[{'OK' if ok else 'FALHOU'}] {nome}")
    return ok


def main() -> int:
    tudo_ok = True
    marca = int(time.time())
    username = f"jornada_teste_{marca}"
    senha = "senha123456"

    status, _ = _req("POST", "/api/auth/register/", {
        "username": username, "email": f"{username}@example.com", "password": senha,
    })
    tudo_ok &= checar(f"Cadastro de '{username}'", status == 201)

    status, tok = _req("POST", "/api/auth/token/", {"username": username, "password": senha})
    tudo_ok &= checar("Login do trial novo", status == 200)
    token = tok.get("access")

    status, me = _req("GET", "/api/auth/me/", token=token)
    empresa_id = me.get("empresa_id")
    tudo_ok &= checar(
        f"/me mostra plano={me.get('empresa_plano')} status={me.get('empresa_status')}",
        me.get("empresa_plano") == "trial",
    )

    status, p1 = _req("POST", "/api/v1/projetos", {"nome": "Projeto A", "dados_completos": {}}, token=token)
    tudo_ok &= checar("1º projeto criado (esperado no trial)", status == 201)

    status, p2 = _req("POST", "/api/v1/projetos", {"nome": "Projeto B", "dados_completos": {}}, token=token)
    tudo_ok &= checar("2º projeto BLOQUEADO no trial (esperado)", status == 403)

    admin_user = os.environ.get("JORNADA_SUPERADMIN_USER")
    admin_senha = os.environ.get("JORNADA_SUPERADMIN_SENHA")
    if not (admin_user and admin_senha):
        print("[--] JORNADA_SUPERADMIN_USER/SENHA não definidos — pulando teste de promoção de plano.")
        print()
        print("TUDO OK (só trial)" if tudo_ok else "ALGO FALHOU — ver acima")
        return 0 if tudo_ok else 1

    status, tokAdmin = _req("POST", "/api/auth/token/", {"username": admin_user, "password": admin_senha})
    tudo_ok &= checar("Login do superadmin", status == 200)
    admin_token = tokAdmin.get("access")

    status, patched = _req("PATCH", f"/api/v1/admin/empresas/{empresa_id}",
                            {"nome": username, "cnpj": None, "plano": "tecnico", "status_assinatura": "ativa"},
                            token=admin_token)
    tudo_ok &= checar(f"Admin promove empresa pra plano='{patched.get('plano')}'", patched.get("plano") == "tecnico")

    status, tok2 = _req("POST", "/api/auth/token/", {"username": username, "password": senha})
    token2 = tok2.get("access")
    status, me2 = _req("GET", "/api/auth/me/", token=token2)
    tudo_ok &= checar(
        f"/me após promoção: plano={me2.get('empresa_plano')} trial_expirado={me2.get('empresa_trial_expirado')}",
        me2.get("empresa_plano") == "tecnico",
    )

    status, p3 = _req("POST", "/api/v1/projetos", {"nome": "Projeto B", "dados_completos": {}}, token=token2)
    tudo_ok &= checar("2º projeto criado após promoção pra plano pago (esperado)", status == 201)

    print()
    print("TUDO OK — jornada completa" if tudo_ok else "ALGO FALHOU — ver acima")
    return 0 if tudo_ok else 1


if __name__ == "__main__":
    sys.exit(main())
