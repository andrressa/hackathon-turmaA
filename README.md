# Laboratório API — DATA CRISIS 2026

## Fluxo
1. POST /equipes
2. GET /fase/1
3. POST /fase/1/checkpoint
4. GET /fase/2
5. POST /fase/2/checkpoint
6. GET /fase/3
7. POST /fase/3/checkpoint
8. GET /fase/4
9. POST /fase/4/checkpoint
10. GET /fase/5
11. POST /final/submeter

## Respostas internas da professora
- Fase 1: duplicatas = 120; coluna com mais ausentes = vibracao
- Fase 2: maior aumento proporcional = TRANSITO
- Fase 3: remover = temperatura
- Fase 4: coluna = carga_sistema; fator ≈100; afetados ≈18.0%

## Deploy
Build: `pip install -r requirements.txt`
Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
