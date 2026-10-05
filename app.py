from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from pathlib import Path
from fastapi.staticfiles import StaticFiles
import pandas as pd
import sqlite3, secrets, json, os
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
SECRET = BASE / "secret"
DB = BASE / "lab.db"
STATIC = BASE / "static"
TEMPLATES = BASE / "templates"

app = FastAPI(
    title="Laboratório API — DATA CRISIS 2026",
    version="1.0.0",
    description="Laboratório progressivo de Data Science na cidade fictícia de Nova Aurora."
)

def db():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS equipes(
            token TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            fase INTEGER NOT NULL DEFAULT 1,
            tentativas_final INTEGER NOT NULL DEFAULT 0
        )
    """)
    con.commit()
    return con

def cfg():
    return json.loads((SECRET/"config.json").read_text(encoding="utf-8"))

def auth(token: str | None):
    if not token:
        raise HTTPException(401, "Informe o token da equipe no cabeçalho X-Team-Token.")
    con = db()
    row = con.execute("SELECT token,nome,fase,tentativas_final FROM equipes WHERE token=?", (token,)).fetchone()
    con.close()
    if not row:
        raise HTTPException(401, "Token de equipe inválido.")
    return {"token":row[0],"nome":row[1],"fase":row[2],"tentativas_final":row[3]}

def set_fase(token: str, fase: int):
    con = db()
    con.execute("UPDATE equipes SET fase=? WHERE token=?", (fase, token))
    con.commit(); con.close()

def require(team, fase):
    if team["fase"] < fase:
        raise HTTPException(403, f"Fase {fase} bloqueada. Conclua a fase anterior.")

class NovaEquipe(BaseModel):
    nome: str = Field(min_length=2, max_length=80)

class RespFase1(BaseModel):
    duplicatas: int
    coluna_mais_ausente: str

class RespFase2(BaseModel):
    setor_maior_aumento: str

class RespFase3(BaseModel):
    coluna_descartar: str

class RespFase4(BaseModel):
    coluna_alterada: str
    fator_correcao: float
    percentual_afetado_aprox: float | None = None

app.mount("/static", StaticFiles(directory=STATIC), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse((TEMPLATES/"index.html").read_text(encoding="utf-8"))

@app.get("/laboratorio", response_class=HTMLResponse)
def laboratorio():
    return HTMLResponse((TEMPLATES/"laboratorio.html").read_text(encoding="utf-8"))

@app.post("/equipes")
def criar_equipe(payload: NovaEquipe):
    token = secrets.token_hex(8)
    con = db()
    con.execute("INSERT INTO equipes(token,nome,fase,tentativas_final) VALUES(?,?,1,0)",
                (token,payload.nome))
    con.commit(); con.close()
    return {
        "equipe": payload.nome,
        "token": token,
        "instrucao": "Use este valor em X-Team-Token nos próximos endpoints.",
        "fase_atual": 1
    }

@app.get("/progresso")
def progresso(x_team_token: str | None = Header(default=None)):
    t = auth(x_team_token)
    return {
        "equipe": t["nome"],
        "fase_atual": t["fase"],
        "fases_concluidas": list(range(1,t["fase"])),
        "tentativas_final": t["tentativas_final"]
    }

@app.get("/fase/1")
def fase1(x_team_token: str | None = Header(default=None)):
    t = auth(x_team_token); require(t,1)
    return {
        "fase": 1,
        "titulo": "Diagnóstico inicial",
        "cenario": "A Central entrega a primeira base histórica da cidade.",
        "arquivo": "/dados/iniciais.csv",
        "missao": [
            "Inspecione estrutura, tipos e distribuição dos dados.",
            "Identifique registros duplicados.",
            "Identifique qual coluna possui a maior quantidade de valores ausentes.",
            "Faça pelo menos uma análise exploratória antes da modelagem."
        ],
        "checkpoint": "Envie as duas descobertas em POST /fase/1/checkpoint."
    }

@app.get("/dados/iniciais.csv")
def iniciais(x_team_token: str | None = Header(default=None)):
    t=auth(x_team_token); require(t,1)
    return FileResponse(DATA/"dados_iniciais.csv",filename="dados_iniciais.csv",media_type="text/csv")

@app.post("/fase/1/checkpoint")
def checkpoint1(payload: RespFase1, x_team_token: str | None = Header(default=None)):
    t=auth(x_team_token); require(t,1)
    c=cfg()["fase1"]
    ok_dup = payload.duplicatas == c["duplicatas"]
    ok_missing = payload.coluna_mais_ausente.strip().lower() == c["coluna_mais_ausente"].lower()
    if not (ok_dup and ok_missing):
        return {
            "aprovado": False,
            "feedback": {
                "duplicatas": "correto" if ok_dup else "revise como está contando duplicatas exatas",
                "ausentes": "correto" if ok_missing else "compare a quantidade de NaN por coluna"
            }
        }
    set_fase(t["token"],2)
    return {"aprovado":True,"mensagem":"Fase 2 liberada.","proximo":"/fase/2"}

@app.get("/fase/2")
def fase2(x_team_token: str | None = Header(default=None)):
    t=auth(x_team_token); require(t,2)
    return {
        "fase":2,
        "titulo":"Nova remessa de dados",
        "comunicado":(
            "A Central informa que uma nova remessa de dados operacionais foi recebida. "
            "Os novos registros deverão ser analisados e considerados na continuidade da investigação."
        ),
        "arquivo":"/dados/novos.csv",
        "missao":[
            "Compare a composição da nova remessa com a base histórica.",
            "Não concatene automaticamente antes de investigar.",
            "Descubra qual setor teve o maior aumento proporcional na nova remessa."
        ],
        "checkpoint":"POST /fase/2/checkpoint"
    }

@app.get("/dados/novos.csv")
def novos(x_team_token: str | None = Header(default=None)):
    t=auth(x_team_token); require(t,2)
    return FileResponse(DATA/"novos_dados.csv",filename="novos_dados.csv",media_type="text/csv")

@app.post("/fase/2/checkpoint")
def checkpoint2(payload: RespFase2, x_team_token: str | None = Header(default=None)):
    t=auth(x_team_token); require(t,2)
    esperado=cfg()["fase2"]["setor_maior_aumento"]
    ok=payload.setor_maior_aumento.strip().upper()==esperado.upper()
    if not ok:
        return {
            "aprovado":False,
            "feedback":"Compare proporções por setor, e não apenas contagens absolutas."
        }
    set_fase(t["token"],3)
    return {"aprovado":True,"mensagem":"Fase 3 liberada.","proximo":"/fase/3"}

@app.get("/fase/3")
def fase3(x_team_token: str | None = Header(default=None)):
    t=auth(x_team_token); require(t,3)
    return {
        "fase":3,
        "titulo":"Variável comprometida",
        "comunicado":(
            "Após verificação técnica, foi confirmado um problema no processo de coleta da variável temperatura. "
            "Os valores dessa coluna não podem mais ser considerados confiáveis."
        ),
        "missao":[
            "Revise o pipeline.",
            "Desconsidere a variável comprometida.",
            "Reavalie as análises e o modelo sem essa informação."
        ],
        "checkpoint":"Informe a coluna que deve sair do pipeline em POST /fase/3/checkpoint."
    }

@app.post("/fase/3/checkpoint")
def checkpoint3(payload: RespFase3, x_team_token: str | None = Header(default=None)):
    t=auth(x_team_token); require(t,3)
    esperado=cfg()["fase3"]["coluna_descartar"]
    ok=payload.coluna_descartar.strip().lower()==esperado.lower()
    if not ok:
        return {"aprovado":False,"feedback":"Releia o comunicado técnico."}
    set_fase(t["token"],4)
    return {"aprovado":True,"mensagem":"Fase 4 liberada.","proximo":"/fase/4"}

@app.get("/fase/4")
def fase4(x_team_token: str | None = Header(default=None)):
    t=auth(x_team_token); require(t,4)
    return {
        "fase":4,
        "titulo":"Inconsistência oculta",
        "comunicado":(
            "A equipe de campo confirmou que parte dos controladores da nova remessa foi substituída. "
            "Há indícios de que pelo menos uma grandeza numérica passou a ser transmitida em escala diferente "
            "do padrão histórico. Não existe lista das unidades afetadas e a Central ainda não identificou o campo."
        ),
        "missao":[
            "Investigue as distribuições numéricas da base histórica e da nova remessa.",
            "Identifique qual variável apresenta duas escalas incompatíveis.",
            "Estime aproximadamente quantos registros foram afetados.",
            "Proponha a transformação necessária para recuperar a escala histórica."
        ],
        "checkpoint":"POST /fase/4/checkpoint"
    }

@app.post("/fase/4/checkpoint")
def checkpoint4(payload: RespFase4, x_team_token: str | None = Header(default=None)):
    t=auth(x_team_token); require(t,4)
    c=cfg()["fase4"]
    ok_col = payload.coluna_alterada.strip().lower()==c["coluna_escala"].lower()
    ok_fator = 90 <= payload.fator_correcao <= 110
    ok_pct = True
    if payload.percentual_afetado_aprox is not None:
        # aceita percentual como 18 ou 0.18
        p=payload.percentual_afetado_aprox
        if p <= 1:
            p*=100
        ok_pct = 12 <= p <= 24
    if not (ok_col and ok_fator and ok_pct):
        pistas=[]
        if not ok_col: pistas.append("compare mínimos, quartis e histogramas entre histórico e nova remessa")
        if not ok_fator: pistas.append("procure uma relação simples de escala entre os dois grupos")
        if not ok_pct: pistas.append("a fração afetada está na ordem de dezenas de porcento, não na maioria da base")
        return {"aprovado":False,"feedback":pistas}
    set_fase(t["token"],5)
    return {"aprovado":True,"mensagem":"Investigação concluída. Desafio final liberado.","proximo":"/fase/5"}

@app.get("/fase/5")
def fase5(x_team_token: str | None = Header(default=None)):
    t=auth(x_team_token); require(t,5)
    return {
        "fase":5,
        "titulo":"Operação real",
        "arquivo":"/dados/operacao-final.csv",
        "missao":[
            "Treine sua solução final usando apenas dados e variáveis que você considera confiáveis.",
            "Gere um CSV com unidade_id e classe_prevista.",
            "Opcionalmente inclua probabilidade_falha.",
            "Você tem no máximo 3 submissões."
        ],
        "formato_csv":"unidade_id,classe_prevista[,probabilidade_falha]",
        "submissao":"POST /final/submeter"
    }

@app.get("/dados/operacao-final.csv")
def operacao_final(x_team_token: str | None = Header(default=None)):
    t=auth(x_team_token); require(t,5)
    return FileResponse(DATA/"operacao_final.csv",filename="operacao_final.csv",media_type="text/csv")

@app.post("/final/submeter")
async def final_submeter(
    arquivo: UploadFile = File(...),
    x_team_token: str | None = Header(default=None)
):
    t=auth(x_team_token); require(t,5)
    if t["tentativas_final"] >= 3:
        raise HTTPException(403,"Limite de 3 submissões atingido.")

    pred = pd.read_csv(arquivo.file)
    obrig={"unidade_id","classe_prevista"}
    if not obrig.issubset(pred.columns):
        raise HTTPException(400,"CSV deve conter unidade_id e classe_prevista.")

    gab=pd.read_csv(SECRET/"gabarito_final.csv")
    m=gab.merge(pred[["unidade_id","classe_prevista"]],on="unidade_id",how="left")
    if m["classe_prevista"].isna().any():
        raise HTTPException(400,"Existem unidades sem previsão.")
    y=m["falha"].astype(int)
    p=m["classe_prevista"].astype(int)

    con=db()
    con.execute("UPDATE equipes SET tentativas_final=tentativas_final+1 WHERE token=?",(t["token"],))
    con.commit(); con.close()

    return {
        "submissao": t["tentativas_final"]+1,
        "accuracy": round(float(accuracy_score(y,p)),4),
        "precision": round(float(precision_score(y,p,zero_division=0)),4),
        "recall": round(float(recall_score(y,p,zero_division=0)),4),
        "f1": round(float(f1_score(y,p,zero_division=0)),4),
        "mensagem":"Use as métricas para justificar a versão final da equipe."
    }
