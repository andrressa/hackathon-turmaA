# DATA CRISIS 2026 — Laboratório Visual de Nova Aurora

Projeto completo FastAPI com:

- portal visual da cidade;
- página da Central Integrada de Operações;
- criação de equipes com token;
- cinco fases desbloqueáveis;
- checkpoints automáticos;
- arquivos de dados progressivos;
- desafio oculto de qualidade de dados;
- submissão final com avaliação automática;
- Swagger em `/docs`.

## Rotas principais

- `/` — portal visual de Nova Aurora
- `/laboratorio` — painel visual das fases
- `/docs` — API interativa
- `POST /equipes` — cria uma equipe
- `GET /progresso` — consulta o progresso
- `/fase/1` ... `/fase/5` — conteúdo de cada fase
- `POST /final/submeter` — avaliação das previsões

## Deploy no Render

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

## Imagens

As imagens ficam em `static/images/`:

- `nova_aurora.svg`
- `central_operacoes.svg`
- `infraestrutura.svg`

## Respostas internas da professora

Consulte `secret/config.json` e o README original para o gabarito dos checkpoints.
Não compartilhe a pasta `secret` com os alunos fora do servidor.
