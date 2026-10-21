"""Preparação reprodutível da base oficial da TOTVS e rótulos fracos da Sprint 3.

Os rótulos de treinamento NÃO são anotações humanas; são heurísticas
construídas a partir de metadados e expressões textuais. A validação
revisada também foi produzida por IA e exige conferência humana externa.
"""
import re
import pandas as pd

PADROES_OPP = [r'\bproposta\w*',r'\bor[çc]amento\w*',r'\bpre[çc]o\w*',r'\bcontrat\w*',
    r'\bcompr\w*',r'\badquir\w*',r'\bimplant\w*',r'\bintegra\w*',r'\bdemonstra\w*',
    r'\bdemo\b',r'\binteress\w*',r'\bnegoci\w*',r'\bfech\w*',r'\bupgrade\b',
    r'\bcross[- ]?sell\w*',r'\bup[- ]?sell\w*',r'\bnecessidade\w*',r'\bprecisamos\b',
    r'\bgostaria\b',r'\bqueremos\b']
PADROES_RISCO = [r'\bcancel\w*',r'\bchurn\b',r'\binsatis\w*',r'\breclam\w*',
    r'\bproblema\w*',r'\berro\w*',r'\bfalha\w*',r'\binstabil\w*',r'\bdemora\w*',
    r'\bconcorrent\w*',r'\bsubstitu\w*',r'\btrocar\b',r'\btroca\b',
    r'\bn[aã]o atende\b',r'\bn[aã]o funciona\b',r'\bparou de funcionar\b']
REGEX_OPP = [re.compile(x,re.IGNORECASE) for x in PADROES_OPP]
REGEX_RISCO = [re.compile(x,re.IGNORECASE) for x in PADROES_RISCO]
REGEX_MASCARA = [re.compile(x,re.IGNORECASE) for x in PADROES_OPP+PADROES_RISCO]
REGEX_FALAS=re.compile(r'\[(LOCUTOR\s+\d+)\]:\s*(.*?)(?=\n\[LOCUTOR\s+\d+\]:|\Z)',re.I|re.S)


def limpar(texto):
    if not isinstance(texto,str): return ''
    return '\n'.join(re.sub(r'[ \t]+',' ',l.strip()) for l in texto.splitlines() if l.strip())


def falas(texto):
    return [f'[{loc.upper()}]: {re.sub(r"\\s+", " ", conteudo).strip()}' for loc,conteudo in REGEX_FALAS.findall(texto) if conteudo.strip()]


def trechos_reuniao(texto, tamanho=4):
    f=falas(limpar(texto))
    return [' '.join(f[i:i+tamanho]) for i in range(0,len(f),tamanho) if f[i:i+tamanho]]


def mascara_rotulagem(texto):
    s=str(texto)
    for p in REGEX_MASCARA: s=p.sub(' ',s)
    return re.sub(r'\s+',' ',s).strip()


def transformar_textos(textos):
    return [mascara_rotulagem(s) for s in textos]


def carregar_oficial(arquivo):
    base=pd.read_json(arquivo,lines=True)
    essenciais={'ID_MEETING','ANON_TRANSCRICAO'}
    if not essenciais.issubset(base.columns):raise ValueError('JSON não contém ID_MEETING e ANON_TRANSCRICAO.')
    base['texto_limpo']=base.ANON_TRANSCRICAO.apply(limpar)
    base=base[base.texto_limpo.str.len()>0].drop_duplicates('texto_limpo').copy()
    base['ID_MEETING']=base.ID_MEETING.astype(str)
    if 'TP_RECURSO' not in base:base['TP_RECURSO']=None
    if 'NOTA_NPS' not in base:base['NOTA_NPS']=None
    base['TP_RECURSO']=base.TP_RECURSO.astype('string').str.lower()
    base['NOTA_NPS']=pd.to_numeric(base.NOTA_NPS,errors='coerce')
    return base


def criar_trechos(base):
    linhas=[]
    for meeting,text,role,nps in base[['ID_MEETING','texto_limpo','TP_RECURSO','NOTA_NPS']].itertuples(index=False,name=None):
        for i,txt in enumerate(trechos_reuniao(text),1):
            words=len(txt.split())
            if not 20<=words<=400:continue
            linhas.append((meeting,i,txt,role,nps,sum(bool(p.search(txt)) for p in REGEX_OPP),sum(bool(p.search(txt)) for p in REGEX_RISCO)))
    return pd.DataFrame(linhas,columns=['ID_MEETING','TRECHO_ID','TRECHO','TP_RECURSO','NOTA_NPS','SCORE_OPP_ROTULO','SCORE_RISCO_ROTULO'])


def base_fraca(trechos,ids_validacao, tarefa, max_por_reuniao=5):
    dados=trechos[~trechos.ID_MEETING.astype(str).isin(set(map(str,ids_validacao)))].copy()
    if tarefa=='oportunidade':
        pos=dados[(dados.TP_RECURSO=='lead')&(dados.SCORE_OPP_ROTULO>=2)]
        neg=dados[(dados.TP_RECURSO=='lead')&(dados.SCORE_OPP_ROTULO==0)]
    else:
        pos=dados[(dados.NOTA_NPS<=6)&(dados.SCORE_RISCO_ROTULO>=1)]
        neg=dados[(dados.NOTA_NPS>=9)&(dados.SCORE_RISCO_ROTULO==0)]
    def sample(df):
        return df.sample(frac=1,random_state=42).groupby('ID_MEETING',sort=False).head(max_por_reuniao)
    pos=sample(pos); neg=sample(neg)
    n=min(len(pos),len(neg))
    if n<15:raise ValueError(f'Base supervisionada insuficiente para {tarefa}: {n} por classe.')
    pos=pos.sample(n=n,random_state=42).assign(ALVO=1)
    neg=neg.sample(n=n,random_state=42).assign(ALVO=0)
    return pd.concat([pos,neg],ignore_index=True).sample(frac=1,random_state=42).reset_index(drop=True)
