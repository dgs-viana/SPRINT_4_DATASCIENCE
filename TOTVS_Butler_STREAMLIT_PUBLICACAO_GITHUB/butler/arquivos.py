"""Leitura resiliente de arquivos CSV (vírgula/;), TXT e JSON/JSONL."""
from __future__ import annotations
import io
import json
from pathlib import Path
import pandas as pd

TEXT_KEYS=['transcricao','texto','ANON_TRANSCRICAO','anon_transcricao','transcript','conteudo','evidencia']
ID_KEYS=['ID_MEETING','id_meeting','id','reuniao','reuniao_id']

def detectar_coluna(df):
    normalized={str(c).casefold():c for c in df.columns}
    for c in TEXT_KEYS:
        if c.casefold() in normalized:return normalized[c.casefold()]
    return None

def ler_dataframe_csv(blob:bytes)->pd.DataFrame:
    try:txt=blob.decode('utf-8-sig')
    except UnicodeDecodeError:txt=blob.decode('cp1252',errors='replace')
    return pd.read_csv(io.StringIO(txt),sep=None,engine='python',dtype=str).fillna('')

def _flatten(item):
    if isinstance(item,dict):
        if detectar_coluna(pd.DataFrame([item])):return [item]
        result=[]
        for v in item.values():
            if isinstance(v,(list,dict)):result.extend(_flatten(v))
        return result
    if isinstance(item,list):
        result=[]
        for v in item:result.extend(_flatten(v))
        return result
    return []

def ler_registros(nome:str,blob:bytes,max_registros=80)->list[dict]:
    ext=Path(nome).suffix.lower()
    if ext=='.txt':
        text=blob.decode('utf-8-sig',errors='replace').strip()
        return [{'id':'1','transcricao':text}] if text else []
    if ext=='.csv':df=ler_dataframe_csv(blob)
    elif ext in ('.json','.jsonl'):
        text=blob.decode('utf-8-sig',errors='replace')
        try: obj=json.loads(text)
        except json.JSONDecodeError:obj=[json.loads(line) for line in text.splitlines() if line.strip()]
        rows=_flatten(obj)
        if not rows:raise ValueError('JSON sem campo reconhecido de transcrição. Esperado: ANON_TRANSCRICAO ou texto.')
        df=pd.DataFrame(rows).fillna('')
    else:raise ValueError('Formato não suportado. Utilize CSV, JSON, JSONL ou TXT.')
    col=detectar_coluna(df)
    if not col:raise ValueError('Falta coluna de texto. Use texto, transcricao ou ANON_TRANSCRICAO.')
    id_col=next((x for x in ID_KEYS if x in df.columns),None)
    rows=[]
    for i,(_,row) in enumerate(df.iterrows(),start=1):
        tx=str(row[col]).strip()
        if tx:
            rows.append({'id':str(row[id_col]) if id_col else str(i),'transcricao':tx})
        if len(rows)>=max_registros:break
    return rows
