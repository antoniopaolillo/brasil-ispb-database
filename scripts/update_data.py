#!/usr/bin/env python3
"""
Script para atualizar os dados de ISPBs do Banco Central do Brasil.

Este script baixa e consolida dados de duas fontes:
1. Lista de Participantes do PIX (URL com data variável)
2. Lista de Participantes do STR (URL fixa)

Remove duplicatas e salva os dados consolidados em JSON.
"""

import os
import json
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URLs base
PIX_URL_TEMPLATE = "https://www.bcb.gov.br/content/estabilidadefinanceira/participantes_pix/lista-participantes-instituicoes-em-adesao-pix-{date}.csv"
STR_URL = "https://www.bcb.gov.br/content/estabilidadefinanceira/str1/ParticipantesSTR.csv"

# Diretórios
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

class ISPBDataUpdater:
    """Classe para atualizar dados de ISPB do BCB."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; Brasil-ISPB-Database/1.0)'
        })
    
    def _get_business_dates(self, days_back: int = 10) -> List[str]:
        """
        Gera lista de datas em formato YYYYMMDD para tentar baixar o CSV do PIX.
        Prioriza dias úteis (segunda a sexta).
        """
        dates = []
        current_date = datetime.now()
        
        for i in range(days_back):
            check_date = current_date - timedelta(days=i)
            date_str = check_date.strftime("%Y%m%d")
            dates.append(date_str)
        
        # Ordenar priorizando dias úteis (segunda=0, domingo=6)
        dates.sort(key=lambda d: (
            datetime.strptime(d, "%Y%m%d").weekday() >= 5,  # Fim de semana por último
            -int(d)  # Mais recente primeiro
        ))
        
        return dates
    
    def _download_csv(self, url: str, description: str) -> Optional[pd.DataFrame]:
        """Baixa e carrega um CSV, retornando DataFrame ou None em caso de erro."""
        try:
            logger.info(f"Baixando {description}: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Tentar diferentes encodings para caracteres acentuados
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            csv_content = None
            
            for encoding in encodings_to_try:
                try:
                    csv_content = response.content.decode(encoding)
                    # Verificar se há caracteres estranhos
                    if '�' not in csv_content and 'Ã§' not in csv_content:
                        logger.info(f"Encoding detectado: {encoding}")
                        break
                except UnicodeDecodeError:
                    continue
            
            # Se não conseguiu com nenhum encoding, usar latin-1 com replace
            if csv_content is None or '�' in csv_content:
                csv_content = response.content.decode('latin-1', errors='replace')
                logger.warning("Usando latin-1 com fallback para caracteres especiais")
            
            # Ler CSV
            from io import StringIO
            
            # Tratamento específico para cada tipo de CSV
            if 'pix' in url.lower():
                # Para o CSV do PIX, pular a primeira linha (título)
                lines = csv_content.split('\n')
                if lines and 'Lista de participantes' in lines[0]:
                    csv_content = '\n'.join(lines[1:])
                df = pd.read_csv(StringIO(csv_content), sep=';', dtype=str)
                
                # Remover primeira coluna se estiver vazia (numeração)
                if df.columns[0] == '' or df.columns[0].strip() == '':
                    df = df.iloc[:, 1:]
                    
            elif 'str' in url.lower():
                # Para o CSV do STR, tentar diferentes separadores
                df = pd.read_csv(StringIO(csv_content), sep=',', dtype=str)
                if len(df.columns) == 1:
                    # Se não funcionou com vírgula, tentar ponto e vírgula
                    df = pd.read_csv(StringIO(csv_content), sep=';', dtype=str)
                    if len(df.columns) == 1:
                        # Se ainda não funcionou, tentar tab
                        df = pd.read_csv(StringIO(csv_content), sep='\t', dtype=str)
            else:
                df = pd.read_csv(StringIO(csv_content), sep=';', dtype=str)
            
            # Limpar nomes das colunas
            df.columns = df.columns.str.strip()
            
            # Remover colunas completamente vazias
            df = df.dropna(axis=1, how='all')
            
            logger.info(f"✅ {description} baixado com sucesso: {len(df)} linhas")
            logger.info(f"Colunas encontradas: {list(df.columns)[:5]}...")  # Mostrar só as 5 primeiras
            return df
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"❌ Erro ao baixar {description}: {e}")
            return None
        except Exception as e:
            logger.warning(f"❌ Erro ao processar {description}: {e}")
            logger.error(f"Detalhes do erro: {str(e)}")
            return None
    
    def download_pix_data(self) -> Optional[pd.DataFrame]:
        """Baixa dados do PIX tentando várias datas."""
        dates_to_try = self._get_business_dates()
        
        for date_str in dates_to_try:
            url = PIX_URL_TEMPLATE.format(date=date_str)
            df = self._download_csv(url, f"Lista PIX ({date_str})")
            
            if df is not None:
                return df
        
        logger.error("❌ Não foi possível baixar dados do PIX para nenhuma data testada")
        return None
    
    def download_str_data(self) -> Optional[pd.DataFrame]:
        """Baixa dados do STR."""
        return self._download_csv(STR_URL, "Lista STR")
    
    def _standardize_column_names(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Padroniza nomes das colunas."""
        # Mapear colunas conhecidas para nomes padrão
        column_mapping = {
            # PIX
            'Nome Reduzido': 'nome',
            'ISPB': 'ispb',
            'CNPJ': 'cnpj',
            'Tipo de Instituição': 'tipo_instituicao',
            'Autorizada pelo BCB': 'autorizada_bcb',
            'Tipo de Participação no SPI': 'tipo_participacao_spi',
            'Tipo de Participação no Pix': 'tipo_participacao_pix',
            'Modalidade de Participação no Pix': 'modalidade_pix',
            'Status em produção': 'status_producao',
            'Iniciação de Transação de Pagamento': 'iniciacao_pagamento',
            'Facilitador de serviço de Saque e Troco (FSS)': 'facilitador_saque',
            
            # STR (adaptar conforme necessário)
            'NomeReduzido': 'nome',
            'Nome': 'nome',
            'CNPJ_Principal': 'cnpj',
            'TipoInstituicao': 'tipo_instituicao',
            'Situacao': 'status_producao',
        }
        
        # Renomear colunas
        df = df.rename(columns=column_mapping)
        
        # Adicionar fonte
        df['fonte'] = source
        
        return df
    
    def _clean_and_validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa e valida os dados."""
        # Limpar ISPB
        if 'ispb' in df.columns:
            df['ispb'] = df['ispb'].astype(str).str.strip()
            df['ispb'] = df['ispb'].str.replace(r'[^\d]', '', regex=True)
            
            # Filtrar ISPBs válidos (8 dígitos)
            df = df[df['ispb'].str.len() == 8]
            df = df[df['ispb'].str.isdigit()]
        
        # Limpar CNPJ
        if 'cnpj' in df.columns:
            df['cnpj'] = df['cnpj'].astype(str).str.strip()
            df['cnpj'] = df['cnpj'].str.replace(r'[^\d]', '', regex=True)
        
        # Limpar nome
        if 'nome' in df.columns:
            df['nome'] = df['nome'].astype(str).str.strip()
            df = df[df['nome'] != '']
            df = df[df['nome'] != 'nan']
        
        # Remover linhas sem ISPB
        df = df.dropna(subset=['ispb'])
        
        return df
    
    def consolidate_data(self, pix_df: Optional[pd.DataFrame], str_df: Optional[pd.DataFrame]) -> List[Dict]:
        """Consolida dados do PIX e STR, removendo duplicatas."""
        all_data = []
        
        # Processar dados do PIX
        if pix_df is not None:
            logger.info("Processando dados do PIX...")
            pix_clean = self._standardize_column_names(pix_df, 'PIX')
            pix_clean = self._clean_and_validate_data(pix_clean)
            
            for _, row in pix_clean.iterrows():
                all_data.append(row.to_dict())
        
        # Processar dados do STR
        if str_df is not None:
            logger.info("Processando dados do STR...")
            str_clean = self._standardize_column_names(str_df, 'STR')
            str_clean = self._clean_and_validate_data(str_clean)
            
            for _, row in str_clean.iterrows():
                all_data.append(row.to_dict())
        
        # Remover duplicatas por ISPB (mantém o primeiro encontrado)
        seen_ispbs = set()
        unique_data = []
        
        for item in all_data:
            ispb = item.get('ispb')
            if ispb and ispb not in seen_ispbs:
                seen_ispbs.add(ispb)
                unique_data.append(item)
        
        logger.info(f"Dados consolidados: {len(unique_data)} instituições únicas")
        return unique_data
    
    def _clean_data_for_json(self, data: List[Dict]) -> List[Dict]:
        """Limpa dados para evitar problemas no JSON (NaN, etc)."""
        clean_data = []
        
        for item in data:
            clean_item = {}
            for key, value in item.items():
                # Tratar valores NaN, None, ou inválidos
                if pd.isna(value) or value is None:
                    clean_item[key] = ""
                elif isinstance(value, str):
                    # Limpar strings vazias ou com apenas espaços
                    cleaned_str = str(value).strip()
                    if cleaned_str.lower() in ['nan', 'none', 'null', '']:
                        clean_item[key] = ""
                    else:
                        clean_item[key] = cleaned_str
                else:
                    clean_item[key] = str(value).strip() if value else ""
            
            clean_data.append(clean_item)
        
        return clean_data
    
    def save_data(self, data: List[Dict]) -> None:
        """Salva dados consolidados em JSON e CSV."""
        # Limpar dados para JSON (remover NaN, etc)
        clean_data = self._clean_data_for_json(data)
        
        # Salvar dados em JSON
        json_file = DATA_DIR / "ispbs.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Dados JSON salvos em: {json_file}")
        
        # Salvar dados em CSV
        if data:
            csv_file = DATA_DIR / "ispbs.csv"
            df = pd.DataFrame(data)
            
            # Substituir NaN por strings vazias no CSV também
            df = df.fillna('')
            
            # Reordenar colunas para ter as principais primeiro
            cols_order = ['ispb', 'nome', 'cnpj', 'tipo_instituicao', 'fonte']
            other_cols = [col for col in df.columns if col not in cols_order]
            final_cols = [col for col in cols_order if col in df.columns] + other_cols
            
            df = df[final_cols]
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"✅ Dados CSV salvos em: {csv_file}")
        
        # Salvar metadados da atualização
        metadata = {
            "last_update": datetime.now().isoformat(),
            "total_institutions": len(clean_data),
            "sources": list(set(item.get('fonte', 'unknown') for item in clean_data if item.get('fonte'))),
            "update_script_version": "1.2",
            "formats_available": ["json", "csv"]
        }
        
        metadata_file = DATA_DIR / "last_update.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Metadados salvos em: {metadata_file}")
    
    def run(self) -> bool:
        """Executa o processo completo de atualização."""
        logger.info("🚀 Iniciando atualização dos dados de ISPB...")
        
        try:
            # Baixar dados
            pix_data = self.download_pix_data()
            str_data = self.download_str_data()
            
            if pix_data is None and str_data is None:
                logger.error("❌ Não foi possível baixar nenhum dado!")
                return False
            
            # Consolidar e salvar
            consolidated_data = self.consolidate_data(pix_data, str_data)
            
            if not consolidated_data:
                logger.error("❌ Nenhum dado válido foi processado!")
                return False
            
            self.save_data(consolidated_data)
            
            logger.info("✅ Atualização concluída com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro durante a atualização: {e}")
            return False

def main():
    """Função principal."""
    updater = ISPBDataUpdater()
    success = updater.run()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 