def descrever_dispositivo(user_agent: str | None) -> str:
    """Leitura best-effort do User-Agent pra exibir algo legível na lista de sessões
    ativas (ex: "Chrome · Windows") — não precisa ser exata, só identificável pelo
    usuário na hora de decidir qual sessão encerrar."""
    if not user_agent:
        return "Dispositivo desconhecido"
    ua = user_agent.lower()

    if "iphone" in ua:
        aparelho = "iPhone"
    elif "ipad" in ua:
        aparelho = "iPad"
    elif "android" in ua:
        aparelho = "Android"
    elif "macintosh" in ua:
        aparelho = "Mac"
    elif "windows" in ua:
        aparelho = "Windows"
    else:
        aparelho = "Dispositivo"

    if "edg/" in ua:
        navegador = "Edge"
    elif "firefox" in ua:
        navegador = "Firefox"
    elif "chrome" in ua:
        navegador = "Chrome"
    elif "safari" in ua:
        navegador = "Safari"
    else:
        navegador = "Navegador"

    return f"{navegador} · {aparelho}"
