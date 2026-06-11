"""
Copia dados da producao para o banco local usando COPY — suporta todos os tipos (JSON, UUID, etc).
"""
import asyncio, selectors, io, sys
sys.path.insert(0, ".")
import psycopg

PROD  = "postgresql://projetista:fKj2l1HQWXav2x26wMFLFrxnbTqgguVY@dpg-d8iovfrtqb8s73bdolf0-a.oregon-postgres.render.com/projetista_v2_wchd?sslmode=require"
LOCAL = "postgresql://projetista:projetista@localhost:5432/projetista_v2"

TABELAS = [
    "unidade_medida",
    "categoria",
    "fabricante",
    "equipamento",
    "performance_equipamento",
    "componente_tecnico",
    "performance_componente",
    "painel_frigorifico",
    "isolamento_tubulacao",
    "porta_frigoriifica",
    "tipo_produto_termico",
    "perfil_produto_termico",
    "usuario",
]

async def copiar():
    print("Conectando...")
    prod  = await psycopg.AsyncConnection.connect(PROD)
    local = await psycopg.AsyncConnection.connect(LOCAL)

    # Limpar local na ordem inversa (filhos antes dos pais)
    for tabela in reversed(TABELAS):
        await local.execute(f"DELETE FROM {tabela}")
    await local.commit()

    for tabela in TABELAS:
        # Contar registros na producao
        cur = await prod.execute(f"SELECT COUNT(*) FROM {tabela}")
        total = (await cur.fetchone())[0]

        if total > 0:
            # Exportar da producao via COPY
            buf = io.BytesIO()
            async with prod.cursor() as cur_prod:
                async with cur_prod.copy(f"COPY {tabela} TO STDOUT (FORMAT BINARY)") as copy_out:
                    async for chunk in copy_out:
                        buf.write(chunk)

            # Importar no local via COPY
            buf.seek(0)
            async with local.cursor() as cur_local:
                async with cur_local.copy(f"COPY {tabela} FROM STDIN (FORMAT BINARY)") as copy_in:
                    while chunk := buf.read(65536):
                        await copy_in.write(chunk)

        # Resetar sequence se tiver id inteiro
        await local.execute(f"""
            DO $$ BEGIN
                PERFORM setval(
                    pg_get_serial_sequence('{tabela}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {tabela}), 1)
                );
            EXCEPTION WHEN others THEN NULL;
            END $$
        """)

        print(f"  {tabela:30s} {total:>5} registros")

    await local.commit()
    await prod.close()
    await local.close()
    print("\nConcluido!")

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(copiar())
