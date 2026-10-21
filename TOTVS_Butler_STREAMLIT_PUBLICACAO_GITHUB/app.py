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
/* TOTVS BUTLER — TEMA DE ALTO CONTRASTE (CLARO + AZUL + VERMELHO) */
.stApp {
    background-color: #f5f7fb;
    color: #102236;
}
.block-container {
    padding-top: 1.4rem;
    max-width: 1450px;
}

/* Barra lateral: texto claro sobre fundo azul-escuro */
[data-testid="stSidebar"] {
    background: #112942;
}
[data-testid="stSidebar"] * {
    color: #f0f6fc !important;
}

/* Cabeçalho */
.hero {
    background: linear-gradient(110deg, #112c46 10%, #125a67 95%);
    border-radius: 19px;
    color: white;
    padding: 29px 34px;
    margin: 6px 0 18px;
    box-shadow: 0 7px 16px #0e233b16;
}
.eyebrow {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .18em;
    color: #9bf4e9;
}
.hero h1 {
    font-size: 36px;
    letter-spacing: -.04em;
    margin: 8px 0 4px;
    color: #fff;
}
.hero p {
    color: #d5e9ee;
    font-size: 15px;
    margin: 0;
}

/* Cartões e indicadores */
.totvs-box {
    background: white;
    border: 1px solid #e4e9ef;
    border-radius: 12px;
    padding: 18px;
    margin: 9px 0;
}
.totvs-box h3 {
    font-size: 15px;
    color: #142f45;
    margin: 0 0 7px;
}
.totvs-box p {
    font-size: 14px;
    margin: 0;
    color: #516477;
}
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e2e7ed;
    border-radius: 12px;
    padding: 12px 15px;
}
[data-testid="stMetric"] label {
    color: #3e5268 !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: #102236 !important;
}

/* Abas: visíveis tanto selecionadas como não selecionadas */
[data-testid="stTabs"] button[role="tab"] {
    font-weight: 700 !important;
    color: #40546a !important;
}
