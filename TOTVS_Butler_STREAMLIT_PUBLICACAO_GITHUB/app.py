
"""Aplicação Streamlit: análise individual, lote e transparência dos modelos."""
from __future__ import annotations
import io
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from butler.arquivos import ler_registros
from butler.pipeline import analisar
from butler.relatorio import html_relatorio

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='TOTVS Butler | Inteligência Comercial',page_icon='🧠',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
.stApp{background:#f5f7fb;color:#102236}.block-container{padding-top:1.4rem;max-width:1450px}
[data-testid="stSidebar"]{background:#112942}[data-testid="stSidebar"] *{color:#f0f6fc!important}
.hero{background:linear-gradient(110deg,#112c46 10%,#125a67 95%);border-radius:19px;color:white;padding:29px 34px;margin:6px 0 18px;box-shadow:0 7px 16px #0e233b16}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:.18em;color:#9bf4e9}.hero h1{font-size:36px;letter-spacing:-.04em;margin:8px 0 4px;color:white}.hero p{color:#d5e9ee;font-size:15px;margin:0}
.totvs-box{background:white;border:1px solid #e4e9ef;border-radius:12px;padding:18px;margin:9px 0}.totvs-box h3{font-size:15px;color:#142f45;margin:0 0 7px}.totvs-box p{font-size:14px;margin:0;color:#516477}
.stMetric{background:white;border:1px solid #e2e7ed;border-radius:12px;padding:12px 15px}.stMetric label{font-weight:600!important}
[data-testid="stTabs"] button{font-weight:700}div[data-testid="stAlert"]{border-radius:10px}
footer{visibility:hidden}


/* ABAS DO STREAMLIT - CORRECAO DEFINITIVA */

[data-testid="stTabs"] button[role="tab"] {
    background-color: transparent !important;
    color: #19344d !important;
    -webkit-text-fill-color: #19344d !important;
    opacity: 1 !important;
    font-weight: 700 !important;
}

/* Texto e elementos internos das abas */
[data-testid="stTabs"] button[role="tab"] *,
[data-testid="stTabs"] button[role="tab"] p,
[data-testid="stTabs"] button[role="tab"] span {
    color: #19344d !important;
    -webkit-text-fill-color: #19344d !important;
    opacity: 1 !important;
}

/* Aba selecionada */
[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] * {
    color: #e63946 !important;
    -webkit-text-fill-color: #e63946 !important;
    background-color: transparent !important;
    opacity: 1 !important;
}

/* Efeito ao passar o mouse */
[data-testid="stTabs"] button[role="tab"]:hover {
    background-color: #e8edf3 !important;
}

/* Mantem o destaque vermelho */
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: #e63946 !important;
}

/* Botões */
div.stButton>button,div.stDownloadButton>button {background:#112942!important;color:white!important;border:1px solid #112942!important;border-radius:10px!important}
div.stButton>button *,div.stDownloadButton>button * {color:white!important;opacity:1!important}
div.stButton>button:hover,div.stDownloadButton>button:hover {background:#174566!important;color:white!important;border-color:#174566!important}
div.stButton>button[kind="primary"] {background:#ee454e!important;color:white!important;border-color:#ee454e!important}

/* Texto da transcrição */
[data-testid="stTextArea"] textarea {background:#242833!important;color:#fff!important;-webkit-text-fill-color:#fff!important;caret-color:#fff!important;border:1px solid #576375!important}
[data-testid="stTextArea"] textarea::placeholder {color:#d1d9e3!important}
[data-testid="stTextArea"] label,[data-testid="stFileUploader"] label {color:#112942!important;font-weight:600!important}

/* Upload */
[data-testid="stFileUploaderDropzone"] {background:#242833!important;border:1px dashed #64748b!important}
[data-testid="stFileUploaderDropzone"] * {color:#fff!important;opacity:1!important}
[data-testid="stFileUploaderDropzone"] button {background:#112942!important;color:#fff!important;border:1px solid #728398!important}

/* Métricas e legendas */
[data-testid="stMetricValue"] {color:#112942!important}
[data-testid="stMetricLabel"] {color:#475569!important}
</style>''',unsafe_allow_html=True)

st.markdown('''<div class="hero"><div class="eyebrow">CHALLENGE TOTVS 2026 · SPRINT 4 · DATA SCIENCE</div><h1>◈ TOTVS Butler</h1><p>Transforme transcrições em sinais de retenção, oportunidades e próximos passos para o time comercial.</p></div>''',unsafe_allow_html=True)

with st.sidebar:
    st.markdown('### ◈ TOTVS Butler')
    st.caption('Protótipo acadêmico · Data Science')
    st.divider()
    st.markdown('**Como usar**')
    st.markdown('1. Cole ou carregue uma transcrição.\n2. Clique em **Analisar**.\n3. Confira os trechos e exporte o relatório.')
    st.divider()
    st.markdown('**Modelos embarcados**')
    _info=json.loads((ROOT/'modelos'/'metricas.json').read_text(encoding='utf-8')) if (ROOT/'modelos'/'metricas.json').exists() else {}
    for task,label in [('oportunidade','Oportunidade'),('risco','Risco')]:
        nome=_info.get('tarefas',{}).get(task,{}).get('modelo_final','não carregado')
        st.caption(f'{label}: {nome} + TF-IDF')
    st.divider()
    st.caption('Os índices são sinais de triagem, não probabilidades comprovadas de cancelamento ou compra.')
    st.warning('Demonstração acadêmica na nuvem: não insira dados pessoais ou transcrições sigilosas.')

@st.cache_resource(show_spinner=False)
def _check_models():
    from butler.pipeline import carregar_modelos
    return carregar_modelos()

try:_check_models()
except Exception as exc:
    st.error(f'Modelos indisponíveis: {exc}');st.info('Execute no terminal: python treinar_modelos.py');st.stop()

sample=(ROOT/'dados'/'transcricao_exemplo.txt').read_text(encoding='utf-8')

def table_from_result(result):
    df=pd.DataFrame(result['trechos'])
    return df.rename(columns={'trecho':'Trecho','evidencia':'Evidência textual','risco':'Risco','score_risco':'Índice risco (0–100)',
                              'oportunidade':'Oportunidade','score_oportunidade':'Índice oportunidade (0–100)','sentimento':'Sentimento',
                              'produtos':'Produtos','termos':'Termos','recomendacao':'Ação sugerida'})

def display_result(result,meeting='Reunião'):
    r=result['resumo']
    a,b,c,d=st.columns(4)
    a.metric('Trechos analisados',r['trechos_analisados'])
    b.metric('Sinais de risco',r['alertas_risco'])
    c.metric('Oportunidades',r['oportunidades'])
    d.metric('Sentimento predominante',r['sentimento_predominante'])
    st.markdown('#### Plano de ação comercial')
    st.info(r['recomendacao'])
    if r['aviso']:st.warning(r['aviso'])
    col1,col2=st.columns(2)
    with col1:
        st.markdown('**Produtos mencionados**')
        st.write(' · '.join(r['produtos']) if r['produtos'] else 'Nenhum produto identificado')
    with col2:
        st.markdown('**Temas relevantes**')
        st.write(' · '.join(t['termo'] for t in r['termos_relevantes']) if r['termos_relevantes'] else 'Sem termos relevantes destacados')
    st.markdown('#### Evidências e indicadores por trecho')
    df=table_from_result(result)
    st.dataframe(df,use_container_width=True,hide_index=True,height=min(470,90+len(df)*38),column_config={
        'Índice risco (0–100)':st.column_config.ProgressColumn('Índice risco (0–100)',min_value=0,max_value=100,format='%.1f'),
        'Índice oportunidade (0–100)':st.column_config.ProgressColumn('Índice oportunidade (0–100)',min_value=0,max_value=100,format='%.1f')})
    st.caption('Leitura recomendada: considere o trecho original antes de executar qualquer ação. Índices refletem o classificador de prova de conceito.')
    c1,c2,c3=st.columns(3)
    c1.download_button('⬇ Relatório visual (.html)',html_relatorio(result,meeting).encode('utf-8'),file_name='totvs_butler_relatorio.html',mime='text/html',use_container_width=True)
    c2.download_button('⬇ Evidências (.csv)',df.to_csv(index=False,sep=';').encode('utf-8-sig'),file_name='totvs_butler_evidencias.csv',mime='text/csv',use_container_width=True)
    c3.download_button('⬇ Análise completa (.json)',json.dumps(result,ensure_ascii=False,indent=2).encode('utf-8'),file_name='totvs_butler_analise.json',mime='application/json',use_container_width=True)

an_tab,batch_tab,validation_tab,about_tab=st.tabs(['🔎 Analisar reunião','📚 Análise em lote','📈 Validação dos modelos','ℹ️ Metodologia'])

with an_tab:
    st.markdown('### Nova transcrição')
    st.caption('Cole um texto de reunião ou carregue um arquivo TXT. A análise roda no servidor Streamlit; não precisa de chave de API. Use apenas exemplos fictícios ou conteúdo autorizado.')
    if 'texto_principal' not in st.session_state:st.session_state['texto_principal']=sample
    c1,c2=st.columns([1,3])
    with c1:
        if st.button('Usar demonstração',use_container_width=True):
            st.session_state['texto_principal']=sample
            st.rerun()
        upload=st.file_uploader('Ou escolha um arquivo .txt',type=['txt'],key='file_one')
        if upload and st.button('Carregar TXT',use_container_width=True):
            st.session_state['texto_principal']=upload.getvalue().decode('utf-8-sig',errors='replace')
            st.rerun()
    with c2:
        st.text_area('Texto da reunião',key='texto_principal',height=210,help='Pode conter [LOCUTOR n]: ou Cliente:/Analista:')
    if st.button('◈ Analisar transcrição',type='primary',use_container_width=True):
        try:
            with st.spinner('Analisando transcrição...'):
                st.session_state['resultado_unico']=analisar(st.session_state['texto_principal'])
        except Exception as exc:st.error(f'Não foi possível analisar: {exc}')
    if 'resultado_unico' in st.session_state:
        st.divider();display_result(st.session_state['resultado_unico'])

with batch_tab:
    st.markdown('### Processamento de várias reuniões')
    st.caption('Suporta TXT, CSV, JSON e JSONL; lê a coluna `ANON_TRANSCRICAO`, `transcricao` ou `texto`. Até 80 reuniões por arquivo na interface.')
    batch=st.file_uploader('Carregue a base de reuniões',type=['txt','csv','json','jsonl'],key='file_batch')
    if batch and st.button('Processar arquivo',type='primary'):
        if batch.size>12*1024*1024:st.error('Limite de 12 MB no protótipo web. Para arquivos grandes, use a CLI local.')
        else:
            try:
                regs=ler_registros(batch.name,batch.getvalue(),max_registros=80)
                if not regs:raise ValueError('Arquivo sem transcrições reconhecidas.')
                done=[];detail=[]
                prog=st.progress(0)
                for i,reg in enumerate(regs):
                    res=analisar(reg['transcricao'],max_trechos=450)
                    s=res['resumo']
                    done.append({'Reunião':reg['id'],'Trechos':s['trechos_analisados'],'Alertas de risco':s['alertas_risco'],'Oportunidades':s['oportunidades'],
                                'Sentimento':s['sentimento_predominante'],'Produtos':', '.join(s['produtos']),'Recomendação':s['recomendacao']})
                    detail.extend([{'Reunião':reg['id'],**item} for item in res['trechos']]);prog.progress((i+1)/len(regs))
                st.session_state['batch_results']=(done,detail)
            except Exception as exc:st.error(f'Erro ao processar arquivo: {exc}')
    if 'batch_results' in st.session_state:
        done,detail=st.session_state['batch_results'];df=pd.DataFrame(done)
        a,b,c=st.columns(3)
        a.metric('Reuniões',len(df));b.metric('Sinais de risco',int(df['Alertas de risco'].sum()));c.metric('Oportunidades',int(df['Oportunidades'].sum()))
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button('⬇ Resumo em CSV',df.to_csv(index=False,sep=';').encode('utf-8-sig'),file_name='totvs_butler_resumo_lote.csv',mime='text/csv')
        st.download_button('⬇ Evidências em CSV',pd.DataFrame(detail).to_csv(index=False,sep=';').encode('utf-8-sig'),file_name='totvs_butler_evidencias_lote.csv',mime='text/csv')

with validation_tab:
    st.markdown('### Avaliação com transcrições oficiais TOTVS')
    st.info('Dados: ANON_transcricao.json (TOTVS/FIAP). Treino com rótulos fracos da Sprint 3. A validação revisada foi rotulada por IA, **sem conferência humana**; métricas são exploratórias.')
    mfile=ROOT/'modelos'/'metricas.json'
    if mfile.exists():
        m=json.loads(mfile.read_text(encoding='utf-8'))
        est=m.get('estatisticas',{})
        st.caption(f"Base: {est.get('linhas_base_bruta','—')} reuniões brutas, {est.get('reunioes_unicas_transcricao','—')} transcrições únicas; {est.get('trechos_com_20_a_400_palavras','—')} trechos após filtro. Validação: {est.get('trechos_avaliacao_revisada_ia','—')} trechos em {est.get('reunioes_avaliacao_revisada_ia','—')} reuniões.")
        for task,info in m['tarefas'].items():
            st.markdown('#### '+ ('Oportunidade comercial' if task=='oportunidade' else 'Risco de retenção'))
            st.write(f"**Modelo escolhido:** {info['modelo_final']}")
            st.caption(info['criterio_escolha'])
            st.markdown('**Comparação de candidatos (CV com separação por reunião)**')
            tabela=pd.DataFrame(info['comparacao_cv'])
            st.dataframe(tabela[['modelo','accuracy','precision','recall','f1']].rename(columns={'modelo':'Algoritmo','accuracy':'Accuracy','precision':'Precision','recall':'Recall','f1':'F1'}),hide_index=True,use_container_width=True)
            a=info['validacao_revisada_ia']
            st.markdown('**Resultados na amostra revisada por IA (119 trechos)**')
            st.dataframe(pd.DataFrame([{'Accuracy':a['accuracy'],'Precision':a['precision'],'Recall':a['recall'],'F1':a['f1'],'Falsos positivos':a['matriz_confusao'][0][1],'Falsos negativos':a['matriz_confusao'][1][0]}]),hide_index=True,use_container_width=True)
            with st.expander('Matriz de confusão — rótulos IA'):
                st.dataframe(pd.DataFrame(a['matriz_confusao'],columns=['Previsto: Não','Previsto: Sim'],index=['Rótulo IA: Não','Rótulo IA: Sim']))
            st.caption(f"{info['reunioes_treino']} reuniões de treinamento; {info['ids_sobrepostos_na_validacao']} reuniões em comum com a validação.")
        st.warning('Amostra de validação pequena e rotulada por IA, não por pessoas. Não utilizar esses números como precisão comprovada de previsão de churn ou conversão.')
    else:st.error('Arquivo de métricas não encontrado. Execute python treinar_modelos.py.')

with about_tab:
    st.markdown('### Como a solução funciona')
    st.markdown('''**Fluxo:** transcrição oficial → limpeza → blocos de quatro falas → máscara dos termos usados na rotulagem → TF-IDF → modelos supervisionados → índices de triagem, produtos, termos e recomendações.

**Dados:** reuniões reais anonimizadas do Challenge TOTVS/FIAP. Os rótulos de treinamento são **fracos**, obtidos com regras textuais e metadados (tipo de recurso/NPS) herdados da Sprint 3. A amostra de avaliação foi revisada por IA, não validada por humanos.

**Proteção contra vazamento:** nenhuma reunião usada para avaliar é incluída no treinamento; a validação cruzada também separa as reuniões entre treinamento e teste.

**Sentimento e produtos:** identificados por regras, não por modelos supervisionados. Os índices são saídas dos classificadores, não probabilidades reais de churn/venda.

**Limitações:** rótulos fracos podem ser imprecisos, a validação por IA pode errar, baixa representatividade de certos segmentos, mudança de vocabulário e erros nas transcrições. Sem integração em tempo real com CRM ou Teams. Revisão humana antes de ações comerciais.

**Próximos passos:** construir rótulos revisados por especialistas, ampliar validação prospectiva, calibrar indicadores e integrar sistemas com autorização de privacidade.''')
    st.markdown('**Equipe**')
    st.caption('Felipe Viana · RM 565341 | Felipe Bonilha · RM 562356 | Joan Ferreira · RM 562913 | Levi de Jesus · RM 563279 | Luigi Borghi · RM 563096')
