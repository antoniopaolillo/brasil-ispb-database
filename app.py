#!/usr/bin/env python3
"""
API Flask para consultar dados de ISPB do Brasil.

Endpoints:
- GET /api/ispbs - Lista todas as instituições
- GET /api/ispb/<ispb> - Busca instituição por ISPB
- GET /api/stats - Estatísticas dos dados
- GET / - Página inicial com documentação
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from flask import Flask, jsonify, render_template_string, request
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar Flask
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Diretórios
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"

class ISPBService:
    """Serviço para consultar dados de ISPB."""
    
    def __init__(self):
        self.data_file = DATA_DIR / "ispbs.json"
        self.metadata_file = DATA_DIR / "last_update.json"
        self._data = None
        self._metadata = None
        self._load_data()
    
    def _load_data(self) -> None:
        """Carrega dados do arquivo JSON."""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                logger.info(f"Dados carregados: {len(self._data)} instituições")
            else:
                logger.warning("Arquivo de dados não encontrado")
                self._data = []
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            self._data = []
        
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
            else:
                self._metadata = {"last_update": "Nunca", "total_institutions": 0}
        except Exception as e:
            logger.error(f"Erro ao carregar metadados: {e}")
            self._metadata = {"last_update": "Erro", "total_institutions": 0}
    
    def get_all_ispbs(self) -> List[Dict]:
        """Retorna todas as instituições."""
        return self._data or []
    
    def get_ispb(self, ispb: str) -> Optional[Dict]:
        """Busca instituição por ISPB."""
        ispb_clean = str(ispb).strip().zfill(8)
        
        for institution in self._data or []:
            if institution.get('ispb') == ispb_clean:
                return institution
        
        return None
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas dos dados."""
        data = self._data or []
        
        # Contar por tipo de instituição
        tipos = {}
        fontes = {}
        status = {}
        
        for inst in data:
            # Tipos de instituição
            tipo = inst.get('tipo_instituicao', 'Não informado')
            tipos[tipo] = tipos.get(tipo, 0) + 1
            
            # Fontes
            fonte = inst.get('fonte', 'Desconhecida')
            fontes[fonte] = fontes.get(fonte, 0) + 1
            
            # Status
            stat = inst.get('status_producao', 'Não informado')
            status[stat] = status.get(stat, 0) + 1
        
        return {
            "total_institutions": len(data),
            "last_update": self._metadata.get('last_update', 'Nunca'),
            "sources": fontes,
            "institution_types": tipos,
            "status_distribution": status,
            "data_freshness": self._calculate_freshness()
        }
    
    def _calculate_freshness(self) -> str:
        """Calcula há quanto tempo os dados foram atualizados."""
        try:
            last_update = self._metadata.get('last_update')
            if not last_update or last_update in ['Nunca', 'Erro']:
                return "Dados nunca foram atualizados"
            
            update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            now = datetime.now(update_time.tzinfo)
            diff = now - update_time
            
            if diff.days > 0:
                return f"Dados de {diff.days} dia(s) atrás"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"Dados de {hours} hora(s) atrás"
            else:
                minutes = diff.seconds // 60
                return f"Dados de {minutes} minuto(s) atrás"
                
        except Exception as e:
            logger.error(f"Erro ao calcular freshness: {e}")
            return "Não foi possível calcular"

# Inicializar serviço
service = ISPBService()

# Templates HTML
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brasil ISPB Database - API</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }
        .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
        .method { background: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }
        .stats { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .example { background: #f1f1f1; padding: 10px; border-radius: 3px; font-family: monospace; margin: 10px 0; }
        .search-box { margin: 20px 0; }
        .search-box input { padding: 10px; width: 200px; border: 1px solid #ddd; border-radius: 4px; }
        .search-box button { padding: 10px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏦 Brasil ISPB Database</h1>
        <p>API para consulta de ISPBs de instituições financeiras brasileiras</p>
    </div>
    
    <div class="stats">
        <h3>📊 Estatísticas dos Dados</h3>
        <p><strong>Total de instituições:</strong> {{ stats.total_institutions }}</p>
        <p><strong>Última atualização:</strong> {{ stats.data_freshness }}</p>
        <p><strong>Fontes:</strong> {{ stats.sources.keys() | join(', ') }}</p>
    </div>
    
    <div class="search-box">
        <h3>🔍 Buscar ISPB</h3>
        <input type="text" id="ispbSearch" placeholder="Digite o ISPB (ex: 00000000)" maxlength="8">
        <button onclick="searchISPB()">Buscar</button>
        <div id="searchResult" style="margin-top: 10px;"></div>
    </div>
    
    <h2>📡 Endpoints Disponíveis</h2>
    
    <div class="endpoint">
        <h3><span class="method">GET</span> /api/ispbs</h3>
        <p>Retorna lista completa de todas as instituições com ISPB.</p>
        <div class="example">
            <strong>Exemplo:</strong><br>
            curl {{ request.url_root }}api/ispbs
        </div>
    </div>
    
    <div class="endpoint">
        <h3><span class="method">GET</span> /api/ispb/&lt;ispb&gt;</h3>
        <p>Busca instituição específica por ISPB.</p>
        <div class="example">
            <strong>Exemplo:</strong><br>
            curl {{ request.url_root }}api/ispb/00000000
        </div>
    </div>
    
    <div class="endpoint">
        <h3><span class="method">GET</span> /api/stats</h3>
        <p>Retorna estatísticas dos dados.</p>
        <div class="example">
            <strong>Exemplo:</strong><br>
            curl {{ request.url_root }}api/stats
        </div>
    </div>
    
    <h2>🌐 Uso Direto via GitHub</h2>
    <div class="example">
        import requests<br><br>
        # Carregar dados diretamente<br>
        url = "https://raw.githubusercontent.com/seu-usuario/brasil-ispb-database/main/data/ispbs.json"<br>
        response = requests.get(url)<br>
        ispbs = response.json()
    </div>
    
    <script>
        function searchISPB() {
            const ispb = document.getElementById('ispbSearch').value.trim();
            const resultDiv = document.getElementById('searchResult');
            
            if (!ispb) {
                resultDiv.innerHTML = '<p style="color: red;">Por favor, digite um ISPB.</p>';
                return;
            }
            
                         if (ispb.length !== 8 || !/^\\d+$/.test(ispb)) {
                resultDiv.innerHTML = '<p style="color: red;">ISPB deve ter exatamente 8 dígitos.</p>';
                return;
            }
            
            resultDiv.innerHTML = '<p>Buscando...</p>';
            
            fetch(`/api/ispb/${ispb}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        resultDiv.innerHTML = `<p style="color: red;">${data.error}</p>`;
                    } else {
                        resultDiv.innerHTML = `
                            <div style="background: #e8f5e8; padding: 10px; border-radius: 5px;">
                                <h4>${data.nome}</h4>
                                <p><strong>ISPB:</strong> ${data.ispb}</p>
                                <p><strong>CNPJ:</strong> ${data.cnpj || 'Não informado'}</p>
                                <p><strong>Tipo:</strong> ${data.tipo_instituicao || 'Não informado'}</p>
                                <p><strong>Status:</strong> ${data.status_producao || 'Não informado'}</p>
                                <p><strong>Fonte:</strong> ${data.fonte}</p>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    resultDiv.innerHTML = '<p style="color: red;">Erro ao buscar dados.</p>';
                });
        }
        
        // Buscar ao pressionar Enter
        document.getElementById('ispbSearch').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchISPB();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """Página inicial com documentação."""
    stats = service.get_stats()
    return render_template_string(HOME_TEMPLATE, stats=stats, request=request)

@app.route('/api/ispbs')
def get_all_ispbs():
    """Endpoint para listar todas as instituições."""
    try:
        data = service.get_all_ispbs()
        return jsonify({
            "success": True,
            "total": len(data),
            "data": data
        })
    except Exception as e:
        logger.error(f"Erro ao buscar ISPBs: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route('/api/ispb/<string:ispb>')
def get_ispb(ispb: str):
    """Endpoint para buscar instituição por ISPB."""
    try:
        # Validar ISPB
        ispb_clean = str(ispb).strip()
        if len(ispb_clean) > 8 or not ispb_clean.isdigit():
            return jsonify({"error": "ISPB deve conter apenas dígitos e ter no máximo 8 caracteres"}), 400
        
        institution = service.get_ispb(ispb_clean)
        
        if institution:
            return jsonify(institution)
        else:
            return jsonify({"error": f"ISPB {ispb_clean.zfill(8)} não encontrado"}), 404
            
    except Exception as e:
        logger.error(f"Erro ao buscar ISPB {ispb}: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route('/api/stats')
def get_stats():
    """Endpoint para estatísticas dos dados."""
    try:
        stats = service.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.errorhandler(404)
def not_found(error):
    """Handler para páginas não encontradas."""
    return jsonify({"error": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos."""
    return jsonify({"error": "Erro interno do servidor"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=debug) 