# 🌐 Guia de Hospedagem - Brasil ISPB Database

Este documento detalha como hospedar a aplicação Brasil ISPB Database de forma gratuita ou com custo muito baixo.

## 📋 Resumo das Opções

| Opção | Custo | API | Dados sempre atualizados | Facilidade |
|-------|--------|-----|-------------------------|------------|
| **GitHub Pages** | Gratuito | ❌ | ✅ | ⭐⭐⭐⭐⭐ |
| **Railway** | $5/mês grátis | ✅ | ✅ | ⭐⭐⭐⭐ |
| **Render** | Gratuito (limitado) | ✅ | ✅ | ⭐⭐⭐⭐ |
| **Vercel** | Gratuito | ✅ | ✅ | ⭐⭐⭐ |
| **Heroku** | $5/mês | ✅ | ✅ | ⭐⭐⭐ |

## 🥇 Opção 1: GitHub Pages (Recomendado para dados estáticos)

### Vantagens
- ✅ **Totalmente gratuito**
- ✅ **CDN global** 
- ✅ **SSL automático**
- ✅ **Dados sempre atualizados** via GitHub Actions
- ✅ **Extremamente confiável**

### Desvantagens
- ❌ **Sem API dinâmica** (apenas arquivos estáticos)

### Como Configurar

1. **Subir para GitHub:**
   ```bash
   git init
   git add .
   git commit -m "🚀 Initial commit"
   git branch -M main
   git remote add origin https://github.com/SEU-USUARIO/brasil-ispb-database.git
   git push -u origin main
   ```

2. **Ativar GitHub Pages:**
   - Vá nas Settings do repositório
   - Seção "Pages" 
   - Source: "Deploy from a branch"
   - Branch: "main"
   - Folder: "/ (root)"

3. **Dados disponíveis em:**
   - `https://SEU-USUARIO.github.io/brasil-ispb-database/data/ispbs.json`
   - `https://SEU-USUARIO.github.io/brasil-ispb-database/data/last_update.json`

### Exemplo de Uso
```python
import requests

# Dados sempre atualizados diretamente do GitHub
url = "https://SEU-USUARIO.github.io/brasil-ispb-database/data/ispbs.json"
response = requests.get(url)
ispbs = response.json()

# Buscar ISPB específico
ispb_procurado = "00000000"
instituicao = next((item for item in ispbs if item["ispb"] == ispb_procurado), None)
```

---

## 🥈 Opção 2: Railway (Recomendado para API completa)

### Vantagens
- ✅ **$5/mês de crédito gratuito**
- ✅ **API completa funcionando**
- ✅ **Deploy automático** via Git
- ✅ **SSL automático**
- ✅ **Logs em tempo real**

### Como Configurar

1. **Criar conta:** [railway.app](https://railway.app)

2. **Conectar GitHub:** 
   - "New Project" → "Deploy from GitHub repo"
   - Selecionar seu repositório

3. **Configurar Deploy:**
   ```toml
   # Criar arquivo railway.toml na raiz
   [build]
   builder = "NIXPACKS"
   
   [deploy]
   startCommand = "python app.py"
   
   [env]
   PORT = "8000"
   ```

4. **Deploy automático:**
   - Railway detecta Python automaticamente
   - Instala dependências do `requirements.txt`
   - Executa `python app.py`

5. **Configurar domínio:**
   - Railway fornece URL automática: `https://seu-app.railway.app`
   - Opcionalmente, adicionar domínio customizado

### URLs da API
- `https://seu-app.railway.app/` - Página inicial
- `https://seu-app.railway.app/api/ispbs` - Lista completa
- `https://seu-app.railway.app/api/ispb/00000000` - ISPB específico

---

## 🥉 Opção 3: Render

### Vantagens
- ✅ **Tier gratuito disponível**
- ✅ **API completa**
- ✅ **Deploy via Git**

### Desvantagens
- ❌ **Hiberna após 15min** de inatividade
- ❌ **750h/mês grátis** (suficiente para a maioria dos casos)

### Como Configurar

1. **Criar conta:** [render.com](https://render.com)

2. **Criar Web Service:**
   - "New" → "Web Service"
   - Conectar repositório GitHub
   
3. **Configurações:**
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
   - **Port:** 8000

4. **Variáveis de ambiente:**
   ```
   PORT=8000
   FLASK_ENV=production
   ```

---

## 🏗️ Opção 4: Vercel (Para aplicações serverless)

### Configuração Especial Necessária

1. **Criar `vercel.json`:**
   ```json
   {
     "functions": {
       "app.py": {
         "runtime": "python3.9"
       }
     },
     "routes": [
       {
         "src": "/(.*)",
         "dest": "/app.py"
       }
     ]
   }
   ```

2. **Modificar `app.py`:**
   ```python
   # Adicionar no final do app.py
   if __name__ != '__main__':
       # Para Vercel
       app = app
   ```

---

## 📊 Monitoramento e Logs

### GitHub Actions
- Visualizar execuções: `https://github.com/SEU-USUARIO/brasil-ispb-database/actions`
- Logs detalhados de cada atualização
- Notificações por email em caso de falha

### Railway/Render
- Dashboard com métricas em tempo real
- Logs de aplicação
- Alertas personalizados

---

## 🔧 Configurações Avançadas

### 1. Domínio Personalizado

**Para GitHub Pages:**
```
# Criar arquivo CNAME na raiz
ispb.meudominio.com
```

**Para Railway/Render:**
- Configurar no dashboard da plataforma
- Adicionar registros DNS no seu provedor

### 2. Rate Limiting

```python
# Adicionar no app.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/ispbs')
@limiter.limit("10 per minute")
def get_all_ispbs():
    # ... código existente
```

### 3. Cache Headers

```python
# Adicionar no app.py
from flask import make_response

@app.route('/api/ispbs')
def get_all_ispbs():
    response = make_response(jsonify(data))
    response.headers['Cache-Control'] = 'public, max-age=3600'  # 1 hora
    return response
```

### 4. Analytics

```python
# Adicionar Google Analytics ou similar
@app.before_request
def track_usage():
    # Registrar métricas de uso
    pass
```

---

## 🚀 Deploy Rápido (Copy & Paste)

### Railway
```bash
# 1. Instalar Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Deploy
railway project:create
railway up
```

### Render
```bash
# Apenas conectar GitHub no dashboard
# Deploy automático ao fazer push
```

---

## 💡 Dicas Importantes

1. **Backup dos dados:** O GitHub já serve como backup
2. **Monitoramento:** Configure alertas para falhas no GitHub Actions
3. **Performance:** Para > 10k requisições/dia, considere Railway ou Render
4. **SEO:** GitHub Pages é melhor indexado que plataformas de PaaS
5. **Custo:** GitHub Pages é gratuito para sempre

---

## ❓ Problemas Comuns

### GitHub Actions não executa
- Verificar permissões do repositório
- Verificar se o repositório é público
- Revisar sintaxe do YAML

### Railway/Render não inicia
- Verificar logs de build
- Verificar variáveis de ambiente
- Verificar porta (usar `os.environ.get('PORT', 8000)`)

### Dados não atualizam
- Verificar logs do GitHub Actions
- Verificar se o BCB mudou a estrutura dos CSVs
- Testar script localmente

---

**🎯 Recomendação Final:** Use **GitHub Pages** para máxima confiabilidade e custo zero, ou **Railway** se precisar da API completa. 