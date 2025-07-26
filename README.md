# Brasil ISPB Database 🏦

[![Update Data](https://github.com/seu-usuario/brasil-ispb-database/actions/workflows/update-data.yml/badge.svg)](https://github.com/seu-usuario/brasil-ispb-database/actions/workflows/update-data.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Lista completa e atualizada diariamente de todas as instituições financeiras do Brasil que possuem ISPB (Identificador do Sistema de Pagamentos Brasileiros)**

## 📋 Sobre

Este projeto mantém uma base de dados sempre atualizada de todas as instituições financeiras brasileiras que possuem ISPB, consolidando informações de:

- **Lista de Participantes do PIX** (Banco Central do Brasil)
- **Lista de Participantes do STR** (Sistema de Transferência de Reservas)

## ✨ Funcionalidades

- 🔄 **Atualização automática diária** via GitHub Actions
- 🏦 **Lista consolidada** sem duplicatas por ISPB
- 🔍 **API simples** para consultas por ISPB ou lista completa
- 📊 **Dados em JSON** para fácil integração
- 🌐 **Totalmente gratuito** e open source

## 📊 Dados Disponíveis

Para cada instituição, você encontra:

- **ISPB** (Identificador único)
- **Nome da Instituição**
- **CNPJ**
- **Tipo de Instituição**
- **Status de Autorização pelo BCB**
- **Tipo de Participação no SPI/PIX**
- **Status Operacional**

## 🚀 Como Usar

### API Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar servidor local
python app.py

# Acessar endpoints
curl http://localhost:8000/api/ispbs                    # Lista completa
curl http://localhost:8000/api/ispb/00000000           # Busca por ISPB específico
```

### Dados Diretos

Os dados estão sempre disponíveis no arquivo [`data/ispbs.json`](data/ispbs.json)

```python
import json
import requests

# Carregar dados diretamente do GitHub
url = "https://raw.githubusercontent.com/seu-usuario/brasil-ispb-database/main/data/ispbs.json"
response = requests.get(url)
ispbs = response.json()

# Buscar por ISPB específico
ispb_procurado = "00000000"
instituicao = next((item for item in ispbs if item["ispb"] == ispb_procurado), None)
```

## 🏗️ Estrutura do Projeto

```
brasil-ispb-database/
├── app.py                 # API Flask para consultas
├── scripts/
│   └── update_data.py     # Script de atualização dos dados
├── data/
│   ├── ispbs.json         # Base de dados consolidada
│   └── last_update.json   # Informações da última atualização
├── .github/
│   └── workflows/
│       └── update-data.yml # GitHub Actions para automação
└── requirements.txt       # Dependências Python
```

## 📅 Cronograma de Atualização

- **Dias úteis**: Execução às 09:00 BRT (dados do PIX são atualizados)
- **Fins de semana**: Execução às 09:00 BRT (apenas dados do STR, se necessário)

## 🔧 Executar Localmente

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/brasil-ispb-database.git
cd brasil-ispb-database

# Instalar dependências
pip install -r requirements.txt

# Atualizar dados manualmente
python scripts/update_data.py

# Executar API
python app.py
```

## 🌐 Hospedagem Gratuita

### Opção 1: GitHub Pages + GitHub Actions (Recomendado)
- ✅ Totalmente gratuito
- ✅ Dados sempre atualizados
- ✅ CDN global
- ❌ Apenas arquivos estáticos (sem API)

### Opção 2: Railway
- ✅ API completa
- ✅ $5/mês de crédito gratuito
- ✅ Deploy automático

### Opção 3: Render
- ✅ API completa
- ✅ Tier gratuito disponível
- ❌ Hiberna após inatividade

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ⚖️ Aviso Legal

Os dados são obtidos diretamente do Banco Central do Brasil e são de domínio público. Este projeto não tem afiliação oficial com o BCB.

## 🏷️ Tags

`ispb` `banco-central` `pix` `str` `instituicoes-financeiras` `brasil` `bcb` `sistema-pagamentos` `open-source` `api` `json`

---

⭐ **Se este projeto foi útil para você, considere dar uma estrela!** 