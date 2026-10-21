"""Pipeline de inferência do TOTVS Butler — classificação de trechos + regras transparentes.
Os scores NÃO são probabilidades calibradas de churn/venda real.
"""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
from pathlib import Path
import re
import unicodedata
import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / 'modelos'
RISK_THRESHOLD = 0.50
OPP_THRESHOLD = 0.50
PRODUCTS = {
    'Protheus': r'\bprotheus\b',
    'RM': r'\brm\b',
    'Fluig': r'\bfluig\b',
    'Datasul': r'\bdatasul\b',
    'Logix': r'\blogix\b',
    'Meu RH': r'\bmeu\s+rh\b',
    'Carol': r'\bcarol\b',
    'TOTVS': r'\btotvs\b',
}
KEY_TERMS = {
    'expansão': r'\b(expans[aã]o|expandir|ampliar|filiais|unidades novas)\b',
    'licenças': r'\b(licen[cç]as?|usu[aá]rios adicionais|novos acessos)\b',
    'orçamento': r'\b(or[cç]amento|proposta|cota[cç][aã]o|pre[cç]os?)\b',
    'upgrade': r'\b(upgrade|migra[cç][aã]o|nova vers[aã]o)\b',
    'contratação': r'\b(contratar|contrata[cç][aã]o|comprar|aquisi[cç][aã]o)\b',
    'insatisfação': r'\b(insatisfeit[oa]s?|insatisfa[cç][aã]o|frustrad[oa]s?|reclama[cç][oõ]es)\b',
    'cancelamento': r'\b(cancelar|cancelamento|rescindir|rescis[aã]o|n[aã]o renovar)\b',
    'concorrência': r'\b(concorrente|trocar de fornecedor|mudar de fornecedor|alternativa)\b',
    'suporte': r'\b(suporte|atendimento|chamados?)\b',
    'falhas': r'\b(falhas?|erros?|bugs?|indispon[ií]vel|instabilidade|trava|lento|lentid[aã]o)\b',
    'prazos': r'\b(atrasos?|demora|prazo|sla)\b',
}
POSITIVE = ('satisfeito','excelente','otimo','bom atendimento','aprovado','gostamos','funcionando','bem recebido','sucesso','resolvido')
NEGATIVE = ('insatisfeito','problema','falha','erro','atraso','cancelar','reclamacao','frustrad','grave','demora','nao funciona','prejuizo','instabilidade','preocup')
STOP = set('a o as os de da do das dos e em no na nos nas um uma para por com ao aos que se nossa nosso nossas nossos sua seu essa esse isso voces voce quando foi sera esta estao temos podem vamos aqui sobre muito mais entre pelo pela seus suas ele ela eles elas hoje ontem amanha bem todos todas onde qual quais como nao sim ate ou ja ter fazer temos e'.split())


def simplify(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', str(text).lower()) if not unicodedata.combining(c))


def _slices(text: str, max_length: int = 420) -> list[str]:
    """Mantém frases curtas; quebra texto longo em fronteiras de sentença/palavra."""
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= max_length: return [text] if len(text) >= 12 else []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    out=[]; current=''
    for sentence in sentences:
        words=sentence.split()
        parts=[]; frag=''
        for word in words:
            if len(frag)+len(word)+1 > max_length and frag:
                parts.append(frag); frag=''
            frag=(frag+' '+word).strip()
        if frag: parts.append(frag)
        for part in parts:
            if len(current)+len(part)+1 <= max_length: current=(current+' '+part).strip()
            else:
                if len(current)>=12:out.append(current)
                current=part
    if len(current)>=12:out.append(current)
    return out


def dividir_transcricao(texto: str, max_trechos: int = 450) -> list[str]:
    """Aceita texto corrido, falas Cliente:/Analista: e [LOCUTOR n]:.
    Reuniões no formato oficial são agrupadas em blocos de até quatro falas,
    em concordância com a construção de trechos da Sprint 3.
    """
    if not isinstance(texto,str) or not texto.strip(): return []
    chunks=[]
    txt=texto.strip().replace('\r\n','\n')
    # A inferência deve reproduzir os blocos de quatro falas do treino.
    if re.search(r'\[LOCUTOR\s*\d+\]\s*:',txt,re.I):
        from butler.dados_oficiais import trechos_reuniao
        blocos=trechos_reuniao(txt,4)
        # Não descartamos conteúdos curtos no uso comercial; o corte de palavras
        # se aplica apenas à preparação da base para treinamento.
        return blocos[:max_trechos]
    txt=re.sub(r'(?<!\n)(\[LOCUTOR\s*\d+\]\s*:)',r'\n\1',txt,flags=re.I)
    lines=[x.strip() for x in txt.split('\n') if x.strip()]
    if len(lines)==1 and len(lines[0])>420:
        lines=re.split(r'(?<=[.!?])\s+',lines[0])
    for line in lines:
        line=re.sub(r'^\s*(?:\[LOCUTOR\s*\d+\]|(?:cliente|analista|vendedor|consultor|participante)\s*\d*)\s*:\s*','',line,flags=re.I).strip()
        chunks.extend(_slices(line))
        if len(chunks)>=max_trechos:break
    return chunks[:max_trechos]


def identificar_produtos(texto: str) -> list[str]:
    return [k for k,v in PRODUCTS.items() if re.search(v,texto,flags=re.I)]


def identificar_termos(texto: str) -> list[str]:
    return [k for k,v in KEY_TERMS.items() if re.search(v,texto,flags=re.I)]


def sentimento_heuristico(texto: str) -> str:
    t=simplify(texto)
    pos=sum(t.count(x) for x in POSITIVE)
    neg=sum(t.count(x) for x in NEGATIVE)
    for phrase in ('nao ha reclamacoes','nao temos problema','nao existe falha','sem atrasos','nao pretendemos cancelar','sem problemas'):
        if phrase in t:neg=max(0,neg-2);pos+=1
    if pos>neg:return 'Positivo'
    if neg>pos:return 'Negativo'
    return 'Neutro'


def _negative_intent(texto: str, tipo: str) -> bool:
    """Salvaguarda explícita para alguns falsos positivos de negação."""
    t=simplify(texto)
    if tipo=='risco':
        return any(x in t for x in ('nao ha reclamacoes','sem reclamacoes','nao pretendemos cancelar','nao ha problemas','sem atrasos','nao temos problemas','nao existe intencao de mudar'))
    return any(x in t for x in ('nao temos interesse em contratar','nao precisamos ampliar','nao ha previsao de adquirir','nao existe previsao de compra','nao havera compra','nao temos previsao de ampliar'))

@lru_cache(maxsize=1)
def carregar_modelos() -> tuple:
    a=MODEL_DIR/'modelo_oportunidade.joblib'; b=MODEL_DIR/'modelo_risco.joblib'
    if not a.exists() or not b.exists():
        raise FileNotFoundError('Modelos não encontrados. Execute: python treinar_modelos.py')
    return joblib.load(a),joblib.load(b)


def _probs(model, texts):
    scores=model.predict_proba(texts)[:,1]
    return [float(np.clip(x,0,1)) for x in scores]


def analisar(texto: str, *, max_trechos:int=450) -> dict:
    chunks=dividir_transcricao(texto,max_trechos=max_trechos)
    if not chunks:
        raise ValueError('Informe uma transcrição com pelo menos 12 caracteres em um trecho.')
    mod_opp,mod_risk=carregar_modelos()
    scores_opp=_probs(mod_opp,chunks)
    scores_risk=_probs(mod_risk,chunks)
    fragments=[]
    for i,(frag,opp,risk) in enumerate(zip(chunks,scores_opp,scores_risk),start=1):
        if _negative_intent(frag,'oportunidade'):opp=min(opp,0.15)
        if _negative_intent(frag,'risco'):risk=min(risk,0.15)
        p=identificar_produtos(frag); terms=identificar_termos(frag)
        opp_flag=opp>=OPP_THRESHOLD
        risk_flag=risk>=RISK_THRESHOLD
        action=('Priorizar contato de CS e verificar causa da insatisfação.' if risk_flag else '')
        if opp_flag:action=(action+' ' if action else '')+'Encaminhar para qualificação comercial.'
        if not action:action='Acompanhar normalmente; sem alerta neste trecho.'
        fragments.append({'trecho':i,'evidencia':frag,'oportunidade': 'Sim' if opp_flag else 'Não','score_oportunidade':round(opp*100,1),
                          'risco':'Sim' if risk_flag else 'Não','score_risco':round(risk*100,1),
                          'sentimento':sentimento_heuristico(frag),'produtos':', '.join(p) or 'Não identificado',
                          'termos':', '.join(terms) or '—','recomendacao':action})
    all_prod=sorted(set(x for t in chunks for x in identificar_produtos(t)))
    all_terms=Counter(x for t in chunks for x in identificar_termos(t))
    n_opp=sum(v['oportunidade']=='Sim' for v in fragments)
    n_risk=sum(v['risco']=='Sim' for v in fragments)
    neg=sum(v['sentimento']=='Negativo' for v in fragments)
    pos=sum(v['sentimento']=='Positivo' for v in fragments)
    if n_risk and n_opp:
        recommendation='Abrir ação de retenção com Customer Success e qualificar oportunidades separadamente, sem ignorar o contexto de insatisfação.'
    elif n_risk:
        recommendation='Solicitar análise humana do histórico, priorizar contato de Customer Success e registrar um plano de ação.'
    elif n_opp:
        recommendation='Encaminhar trechos ao executivo comercial para qualificar interesse, orçamento e próximos passos.'
    else:
        recommendation='Manter acompanhamento da conta e revisar manualmente temas relevantes da reunião.'
    if len(chunks)>=max_trechos: warning='Limite de trechos alcançado. O restante da transcrição pode não ter sido analisado.'
    else:warning=''
    return {
        'resumo':{'trechos_analisados':len(chunks),'alertas_risco':n_risk,'oportunidades':n_opp,
                  'sentimento_predominante': 'Negativo' if neg>pos else 'Positivo' if pos>neg else 'Neutro',
                  'produtos':all_prod,'termos_relevantes':[{'termo':k,'ocorrencias':v} for k,v in all_terms.most_common(8)],
                  'recomendacao':recommendation,'aviso':warning,
                  'nota_metodologica':'Modelos treinados com transcrições oficiais TOTVS e rótulos semiautomáticos (Sprint 3). Scores do modelo NÃO são probabilidades verificadas de cancelamento ou venda. Validação independente possui rótulos revisados por IA, não por humanos.'},
        'trechos':fragments,
    }
