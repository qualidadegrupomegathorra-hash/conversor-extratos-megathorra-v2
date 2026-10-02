# Publicação por link — Streamlit Community Cloud

## Recomendação
Use um repositório GitHub **privado** e mantenha o app **privado**, liberando acesso somente aos e-mails da equipe de Conciliação Bancária.

## Arquivos já preparados
- `app.py` — aplicação
- `requirements.txt` — dependências Python
- `packages.txt` — instala Tesseract OCR e idioma português no Linux
- `.streamlit/config.toml` — tema do app
- `assets/logo_megathorra.jpg` — identidade visual

## Passo a passo
1. Crie um repositório privado no GitHub, por exemplo `megathorra-conversor-cigam`.
2. Envie todo o conteúdo desta pasta para a raiz do repositório.
3. Acesse `share.streamlit.io` e entre com GitHub.
4. Autorize o Streamlit a acessar o repositório privado.
5. Clique em **Create app** e escolha:
   - Repository: `megathorra-conversor-cigam`
   - Branch: `main`
   - Main file path: `app.py`
6. Em **Advanced settings**, use Python 3.12.
7. Clique em **Deploy**.
8. Em **App settings > Sharing**, escolha **Only specific people can view this app**.
9. Adicione os e-mails corporativos autorizados da Conciliação Bancária.
10. Compartilhe a URL final `https://<nome>.streamlit.app` somente com os usuários autorizados.

## Importante
Não torne o aplicativo público. Os arquivos processados são extratos bancários e devem ser tratados como informação financeira interna.
