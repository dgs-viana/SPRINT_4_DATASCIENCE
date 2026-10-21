"""Verificação local rápida dos arquivos mínimos do deploy."""
from pathlib import Path
import json
import ast
r=Path(__file__).resolve().parent
required=['app.py','requirements.txt','butler/pipeline.py','butler/arquivos.py','butler/dados_oficiais.py','butler/relatorio.py','modelos/modelo_oportunidade.joblib','modelos/modelo_risco.joblib','modelos/metricas.json','dados/transcricao_exemplo.txt']
for file in required:
    assert (r/file).is_file(),f'Faltando {file}'
for file in ['app.py']+ [str(p.relative_to(r)) for p in (r/'butler').glob('*.py')]:
    ast.parse((r/file).read_text(encoding='utf-8'))
json.loads((r/'modelos/metricas.json').read_text(encoding='utf-8'))
assert not (r/'dados/ANON_transcricao.json').exists()
print('Arquivos de deploy verificados. Base bruta ausente.')
