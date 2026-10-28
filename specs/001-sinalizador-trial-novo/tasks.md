# Tarefas — 001 sinalizador de trial novo

Um commit só (mudança pequena e coesa). Ordem: testes primeiro.

1. [ ] **Testes (devem falhar pelo motivo certo):** `backend/tests/test_admin_lead_trial.py` cobrindo A1, A2, A5, A6, A7
   (padrão de `test_ia_descritivo.py`: usuário superadmin descartável, limpeza no fim).
2. [ ] **Migration 0047** + campo no modelo `Empresa`.
3. [ ] **API:** `EmpresaOut.lead_tratado_em`, `EmpresaUpdate.lead_tratado`, `criar_empresa` já tratada.
4. [ ] Rodar migration `upgrade → downgrade → upgrade` local e conferir A3 por consulta (nenhuma empresa com campo nulo).
5. [ ] **Frontend:** bolinha, botão alternar, contador na aba (A4, A8).
6. [ ] Verificar no navegador com conta descartável (A8) e rodar a suíte completa (A10) + build do frontend.
7. [ ] Marcar na `spec.md` quais critérios passaram e com qual teste; documentar no CLAUDE.md e na memória.
8. [ ] **Commit / push: etapas separadas, só com autorização explícita.**
