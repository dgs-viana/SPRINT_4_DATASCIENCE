"""Gerador de relatório HTML standalone: visual em navegador/impressão, sem bibliotecas externas."""
from __future__ import annotations
from html import escape
from datetime import datetime

def html_relatorio(resultado:dict,nome='Reunião analisada')->str:
    r=resultado['resumo']
    cards=[('Trechos analisados',r['trechos_analisados']),('Sinais de risco',r['alertas_risco']),('Oportunidades',r['oportunidades']),('Sentimento',r['sentimento_predominante'])]
    cards_html=''.join(f'<div class="metric"><small>{escape(str(k))}</small><strong>{escape(str(v))}</strong></div>' for k,v in cards)
    rows=''
    for t in resultado['trechos']:
        risk='warn' if t['risco']=='Sim' else 'muted'
        opp='good' if t['oportunidade']=='Sim' else 'muted'
        rows+=f'<tr><td>{t["trecho"]}</td><td>{escape(t["evidencia"])}</td><td><span class="pill {risk}">{escape(t["risco"])} · {t["score_risco"]:.1f}</span></td><td><span class="pill {opp}">{escape(t["oportunidade"])} · {t["score_oportunidade"]:.1f}</span></td><td>{escape(t["sentimento"])}</td><td>{escape(t["produtos"])}</td><td>{escape(t["recomendacao"])}</td></tr>'
    products=', '.join(r['produtos']) or 'Não identificados'
    terms=', '.join(f'{x["termo"]} ({x["ocorrencias"]})' for x in r['termos_relevantes']) or 'Sem destaque'
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Relatório TOTVS Butler</title><style>
    :root{{--ink:#182439;--muted:#5b687d;--line:#e3e8ee;--navy:#0e233a;--teal:#0b8f91;--bg:#f6f8fb}}
    *{{box-sizing:border-box}}body{{font:14px/1.5 Inter,'Segoe UI',Arial,sans-serif;color:var(--ink);background:var(--bg);margin:0}}.wrap{{max-width:1240px;margin:0 auto;padding:32px}}
    header{{background:linear-gradient(120deg,#0e233a,#174761);color:white;padding:30px 36px;border-radius:16px}}
    header b{{font-size:13px;letter-spacing:.15em;color:#98eeee}}h1{{font-size:30px;letter-spacing:-.04em;margin:7px 0 0}}header p{{color:#e4eef5;margin:5px 0 0}}
    .metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:20px 0}}.metric{{background:#fff;border:1px solid var(--line);padding:20px;border-radius:12px}}.metric small{{display:block;color:var(--muted)}}.metric strong{{display:block;font-size:26px;margin-top:5px}}
    section{{background:white;border:1px solid var(--line);padding:21px 25px;margin:14px 0;border-radius:12px}}h2{{font-size:17px;margin:0 0 12px}}.description{{color:var(--muted)}}.table-wrap{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;min-width:1100px}}th{{background:#eff3f7;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}th,td{{padding:11px;vertical-align:top;border-bottom:1px solid var(--line)}}td:nth-child(2){{min-width:310px}}.pill{{border-radius:50px;padding:4px 9px;white-space:nowrap;font-size:12px}}.warn{{background:#ffebe7;color:#a4432e}}.good{{background:#e4f7f2;color:#08765b}}.muted{{background:#edf1f5;color:#576477}}footer{{color:var(--muted);font-size:12px;margin:22px 0}}@media print{{body{{background:#fff}}.wrap{{padding:0}}section,header,.metric{{break-inside:avoid}}.table-wrap{{overflow:visible}}table{{font-size:10px;min-width:0}}}}
    @media (max-width:760px){{.metrics{{grid-template-columns:1fr 1fr}}.wrap{{padding:15px}}}}
    </style></head><body><div class="wrap"><header><b>CHALLENGE TOTVS 2026 · SPRINT 4</b><h1>TOTVS Butler</h1><p>Relatório de inteligência comercial · {escape(nome)}</p></header>
    <div class="metrics">{cards_html}</div>
    <section><h2>Recomendação principal</h2><p>{escape(r['recomendacao'])}</p><p class="description"><b>Produtos citados:</b> {escape(products)}<br><b>Temas relevantes:</b> {escape(terms)}</p></section>
    <section><h2>Evidências por trecho</h2><div class="table-wrap"><table><thead><tr><th>Nº</th><th>Trecho da reunião</th><th>Risco / índice</th><th>Oportunidade / índice</th><th>Sentimento</th><th>Produtos</th><th>Próxima ação</th></tr></thead><tbody>{rows}</tbody></table></div></section>
    <footer>Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} · Demonstração acadêmica. {escape(r['nota_metodologica'])} {escape(r['aviso'])}</footer></div></body></html>'''
