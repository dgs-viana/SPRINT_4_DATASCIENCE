# TOTVS Butler — Sprint 4 | Aplicação Streamlit

**Versão para publicação no Streamlit Community Cloud.** Contém apenas código, modelos treinados, resultados agregados e transcrição de demonstração *fictícia*.

## Importante: proteção dos dados

A base `ANON_transcricao.json`, a validação individual `validacao_revisada.csv` e o notebook da Sprint 3 **não estão neste pacote**, deliberadamente. As transcrições foram cedidas para o Challenge TOTVS/FIAP; não publicar o ZIP de entrega acadêmica em um repositório público. **Os arquivos `.joblib` e o vocabulário do modelo foram derivados da base oficial**, então dê preferência a um repositório **privado** e só publique ou compartilhe com autorização da instituição.

O aplicativo permite que usuários colem transcrições. No servidor em nuvem, cole apenas dados fictícios ou autorizados. Conteúdo enviado será processado na infraestrutura de hospedagem, não no computador local.

## Passo a passo — criar URL de apresentação

1. Entre em [GitHub](https://github.com/new). Crie um repositório chamado `totvs-butler-streamlit` e escolha **Private**. Confirme com **Create repository**.
2. No repositório, clique em **Add file → Upload files**. Extraia este ZIP no computador e envie **os arquivos e pastas extraídos**, não o arquivo `.zip` inteiro. Verifique se estão na raiz: `app.py`, `requirements.txt`, pastas `butler/`, `dados/`, `modelos/` e `.streamlit/`. Se a pasta `.streamlit` estiver oculta no Windows, o deploy funciona mesmo sem ela.
3. Clique em **Commit changes**.
4. Abra [share.streamlit.io](https://share.streamlit.io) e entre com **GitHub**.
5. Clique em **Create app → Yup, I have an app** e selecione o repositório criado. Configure **Branch: main**, **Main file path: app.py** e escolha um endereço no campo **App URL** (se disponível).
6. Em **Advanced settings**, selecione **Python 3.12**; confirme e clique em **Deploy**.
7. Acesse a URL `https://...streamlit.app` gerada pela plataforma. Verifique **Usar demonstração → Analisar transcrição → Relatório**, além da aba de Validação.
8. Se o repositório estiver privado, o aplicativo poderá iniciar como privado também. Para permitir que o professor visualize, convide o e-mail dele como viewer em **App settings → Sharing**, ou configure acesso público na interface do Streamlit apenas com autorização para compartilhar os modelos derivados da base oficial.

**Atenção:** GitHub é usado como origem do código para o Streamlit Cloud, mas o enunciado de Data Science da Sprint 4 não exige GitHub como critério explícito.

## Arquivos obrigatórios

- `app.py` — ponto de entrada
- `requirements.txt` — bibliotecas necessárias
- `butler/` — módulos de classificação e relatórios
- `modelos/` — modelos pré-treinados e métricas agregadas
- `dados/transcricao_exemplo.txt` — conteúdo inteiramente fictício para demonstração

## Execução local

No terminal, dentro da pasta: `python -m pip install -r requirements.txt` e `python -m streamlit run app.py`.

## Resultados e limitações

Modelos de oportunidade e risco treinados na base oficial de reuniões anonimizadas, com rótulos fracos semiautomáticos. Avaliação revisada por IA, não por especialistas humanos. Scores são **índices exploratórios**, não probabilidades comprovadas de compra ou churn. Recomendações requerem revisão humana. Os dados brutos **não são necessários** para inferência, pois os modelos já estão treinados.
