# Brasil ISPB Database 🏦

[![Update Data](https://github.com/antoniopaolillo/brasil-ispb-database/actions/workflows/update-data.yml/badge.svg)](https://github.com/antoniopaolillo/brasil-ispb-database/actions/workflows/update-data.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Lista completa e atualizada diariamente de todas as instituições financeiras do Brasil que possuem ISPB (Identificador do Sistema de Pagamentos Brasileiros)**

## 📊 **DADOS SEMPRE ATUALIZADOS - ACESSO DIRETO**

### 🔗 **Links dos Dados (GitHub Pages)**

| Formato | Link Direto | Descrição |
|---------|-------------|-----------|
| **📋 CSV** | [`https://antoniopaolillo.github.io/brasil-ispb-database/data/ispbs.csv`](https://antoniopaolillo.github.io/brasil-ispb-database/data/ispbs.csv) | Ideal para Excel, Google Sheets, análises |
| **📄 JSON** | [`https://antoniopaolillo.github.io/brasil-ispb-database/data/ispbs.json`](https://antoniopaolillo.github.io/brasil-ispb-database/data/ispbs.json) | Ideal para APIs, desenvolvimento, integração |
| **📈 Metadados** | [`https://antoniopaolillo.github.io/brasil-ispb-database/data/last_update.json`](https://antoniopaolillo.github.io/brasil-ispb-database/data/last_update.json) | Info sobre última atualização |

> ⚡ **Dados atualizados automaticamente todos os dias úteis às 9:00 BRT**
## 📊 Estrutura dos Dados (Normalizada)

**Cada instituição possui os mesmos campos padronizados:**

### 🏷️ **Identificação**
- **`ispb`** - Código ISPB único (8 dígitos)
- **`nome_completo`** - Nome completo da instituição
- **`nome_reduzido`** - Nome reduzido/fantasia
- **`cnpj`** - CNPJ da instituição (quando disponível)

### 🏛️ **Classificação**
- **`tipo_instituicao`** - Tipo (Banco, Instituição de Pagamento, etc.)
- **`autorizada_bcb`** - Autorizada pelo Banco Central (Sim/Não)

### 🔗 **Participação em Sistemas**
- **`participa_pix`** - Participa do PIX (Sim/Não)
- **`participa_str`** - Participa do STR (Sim/Não)
- **`participa_compe`** - Participa da COMPE (Sim/Não)

### 📈 **Status e Operação**
- **`status_operacional`** - Status atual da operação
- **`data_inicio_operacao`** - Data de início das operações
- **`acesso_principal`** - Tipo de acesso ao sistema

### 🎯 **Específicos do PIX**
- **`modalidade_pix`** - Modalidade de participação no PIX
- **`iniciacao_pagamento`** - Permite iniciação de pagamento (Sim/Não)
- **`facilitador_saque`** - É facilitador de saque e troco (Sim/Não)

### 📍 **Metadados**
- **`fonte_dados`** - Origem dos dados (PIX, STR, ou PIX+STR)
---

## 📋 Sobre

Este projeto mantém uma base de dados sempre atualizada de todas as instituições financeiras brasileiras que possuem ISPB, consolidando informações de:

- **Lista de Participantes do PIX** (Banco Central do Brasil)
- **Lista de Participantes do STR** (Sistema de Transferência de Reservas)

## ✨ Funcionalidades

- 🔄 **Atualização automática diária** via GitHub Actions
- 🏦 **Lista consolidada** sem duplicatas por ISPB
- 🔍 **API simples** para consultas por ISPB ou lista completa
- 📊 **Múltiplos formatos**: JSON e CSV
- 📋 **CSV para análises** em Excel, Google Sheets, Power BI
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

Os dados estão sempre disponíveis em múltiplos formatos:

#### 📄 **JSON (Para APIs e Desenvolvimento)**
```python
import requests

# Carregar dados diretamente do GitHub Pages
url = "https://antoniopaolillo.github.io/brasil-ispb-database/data/ispbs.json"
response = requests.get(url)
ispbs = response.json()

# Buscar por ISPB específico
ispb_procurado = "24313102"  # 99PAY IP S.A.
instituicao = next((item for item in ispbs if item["ispb"] == ispb_procurado), None)
print(f"Encontrado: {instituicao['nome']}")
```

#### 📋 **CSV (Para Análises em Excel/Google Sheets)**
```python
import pandas as pd

# Carregar CSV diretamente
url = "https://antoniopaolillo.github.io/brasil-ispb-database/data/ispbs.csv"
df = pd.read_csv(url)

# Análises possíveis com a estrutura normalizada
print(f"Total de instituições: {len(df)}")

# Instituições que participam tanto do PIX quanto do STR
pix_e_str = df[(df['participa_pix'] == 'Sim') & (df['participa_str'] == 'Sim')]
print(f"PIX + STR: {len(pix_e_str)} instituições")

# Bancos por tipo
tipos = df['tipo_instituicao'].value_counts()
print("Tipos de instituição:", tipos.head())

# Exportar para Excel local
df.to_excel("ispbs_brasil.xlsx", index=False)
```

#### 🔗 **Links Diretos (Clique para Download)**
- **CSV**: [ispbs.csv](https://antoniopaolillo.github.io/brasil-ispb-database/data/ispbs.csv)
- **JSON**: [ispbs.json](https://antoniopaolillo.github.io/brasil-ispb-database/data/ispbs.json)

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
git clone https://github.com/antoniopaolillo/brasil-ispb-database.git
cd brasil-ispb-database

# Instalar dependências
pip install -r requirements.txt

# Atualizar dados manualmente
python scripts/update_data.py

# Executar API
python app.py
```

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