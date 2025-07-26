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
    
    def _normalize_institution_data(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Normaliza dados de instituições para estrutura única."""
        
        # Definir estrutura padrão para TODAS as instituições
        standard_structure = {
            'ispb': '',
            'nome_completo': '',
            'nome_reduzido': '',
            'cnpj': '',
            'tipo_instituicao': '',
            'autorizada_bcb': '',
            'participa_pix': 'Não',
            'participa_str': 'Não',
            'status_operacional': '',
            'data_inicio_operacao': '',
            'acesso_principal': '',
            'participa_compe': '',
            'modalidade_pix': '',
            'iniciacao_pagamento': 'Não',
            'facilitador_saque': 'Não',
            'fonte_dados': source
        }
        
        # Criar DataFrame normalizado
        normalized_data = []
        
        for _, row in df.iterrows():
            normalized_row = standard_structure.copy()
            
            if source == 'PIX':
                # Mapeamento específico para dados do PIX
                normalized_row.update({
                    'ispb': str(row.get('ISPB', '')).strip(),
                    'nome_completo': str(row.get('Nome Reduzido', '')).strip(),
                    'nome_reduzido': str(row.get('Nome Reduzido', '')).strip(),
                    'cnpj': str(row.get('CNPJ', '')).strip(),
                    'tipo_instituicao': str(row.get('Tipo de Instituição', '')).strip(),
                    'autorizada_bcb': str(row.get('Autorizada pelo BCB', '')).strip(),
                    'participa_pix': 'Sim',
                    'status_operacional': str(row.get('Status em produção', '')).strip(),
                    'modalidade_pix': str(row.get('Modalidade de Participação no Pix', '')).strip(),
                    'iniciacao_pagamento': str(row.get('Iniciação de Transação de Pagamento', 'Não')).strip(),
                    'facilitador_saque': str(row.get('Facilitador de serviço de Saque e Troco (FSS)', 'Não')).strip(),
                })
                
            elif source == 'STR':
                # Mapeamento específico para dados do STR
                nome_extenso = str(row.get('Nome_Extenso', '')).strip()
                nome_reduzido = str(row.get('Nome_Reduzido', '')).strip()
                
                normalized_row.update({
                    'ispb': str(row.get('ISPB', '')).strip(),
                    'nome_completo': nome_extenso if nome_extenso else nome_reduzido,
                    'nome_reduzido': nome_reduzido,
                    'cnpj': '',  # STR não tem CNPJ
                    'tipo_instituicao': 'Instituição Financeira',  # Genérico para STR
                    'autorizada_bcb': 'Sim',  # Todas do STR são autorizadas
                    'participa_str': 'Sim',
                    'status_operacional': 'Ativo',  # Assumir ativo se está no STR
                    'data_inicio_operacao': str(row.get('Início_da_Operação', '')).strip(),
                    'acesso_principal': str(row.get('Acesso_Principal', '')).strip(),
                    'participa_compe': str(row.get('Participa_da_Compe', '')).strip(),
                })
            
            normalized_data.append(normalized_row)
        
        return pd.DataFrame(normalized_data)
    
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
        """Consolida dados do PIX e STR com estrutura única."""
        consolidated_institutions = {}
        
        # Processar dados do PIX
        if pix_df is not None:
            logger.info("Normalizando dados do PIX...")
            pix_normalized = self._normalize_institution_data(pix_df, 'PIX')
            pix_clean = self._clean_and_validate_data(pix_normalized)
            
            for _, row in pix_clean.iterrows():
                ispb = row['ispb']
                if ispb and ispb.isdigit() and len(ispb) == 8:
                    consolidated_institutions[ispb] = row.to_dict()
        
        # Processar dados do STR
        if str_df is not None:
            logger.info("Normalizando dados do STR...")
            str_normalized = self._normalize_institution_data(str_df, 'STR')
            str_clean = self._clean_and_validate_data(str_normalized)
            
            for _, row in str_clean.iterrows():
                ispb = row['ispb']
                if ispb and ispb.isdigit() and len(ispb) == 8:
                    if ispb in consolidated_institutions:
                        # Instituição já existe (vem do PIX), merge dados do STR
                        existing = consolidated_institutions[ispb]
                        
                        # Usar nome mais completo se disponível
                        if not existing['nome_completo'] and row['nome_completo']:
                            existing['nome_completo'] = row['nome_completo']
                        
                        # Manter melhor tipo de instituição (PIX é mais específico)
                        if existing['tipo_instituicao'] == 'Instituição Financeira' and row['tipo_instituicao']:
                            existing['tipo_instituicao'] = row['tipo_instituicao']
                        
                        # Adicionar informações exclusivas do STR
                        existing['participa_str'] = 'Sim'
                        existing['data_inicio_operacao'] = row['data_inicio_operacao']
                        existing['acesso_principal'] = row['acesso_principal']
                        existing['participa_compe'] = row['participa_compe']
                        
                        # Indicar que tem dados de ambas as fontes
                        existing['fonte_dados'] = 'PIX+STR'
                        
                    else:
                        # Instituição só existe no STR
                        consolidated_institutions[ispb] = row.to_dict()
        
        # Converter para lista e ordenar por ISPB
        unique_data = list(consolidated_institutions.values())
        unique_data.sort(key=lambda x: x['ispb'])
        
        # Estatísticas para log
        pix_only = sum(1 for item in unique_data if item['fonte_dados'] == 'PIX')
        str_only = sum(1 for item in unique_data if item['fonte_dados'] == 'STR')
        both = sum(1 for item in unique_data if item['fonte_dados'] == 'PIX+STR')
        
        logger.info(f"Dados consolidados: {len(unique_data)} instituições únicas")
        logger.info(f"  - Apenas PIX: {pix_only}")
        logger.info(f"  - Apenas STR: {str_only}")
        logger.info(f"  - PIX+STR: {both}")
        
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
            
            # Ordenar colunas de forma lógica (informações principais primeiro)
            cols_order = [
                'ispb', 
                'nome_completo', 
                'nome_reduzido',
                'cnpj', 
                'tipo_instituicao',
                'autorizada_bcb',
                'participa_pix',
                'participa_str',
                'status_operacional',
                'fonte_dados',
                'modalidade_pix',
                'iniciacao_pagamento',
                'facilitador_saque',
                'data_inicio_operacao',
                'acesso_principal',
                'participa_compe'
            ]
            
            # Garantir que todas as colunas existam
            final_cols = [col for col in cols_order if col in df.columns]
            
            df = df[final_cols]
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"✅ Dados CSV salvos em: {csv_file}")
        
        # Salvar metadados da atualização
        metadata = {
            "last_update": datetime.now().isoformat(),
            "total_institutions": len(clean_data),
            "sources": list(set(item.get('fonte_dados', 'unknown') for item in clean_data if item.get('fonte_dados'))),
            "update_script_version": "2.0",
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