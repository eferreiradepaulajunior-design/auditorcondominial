"""
Sistema de memória compartilhada entre agentes.
Cada condomínio mantém sua própria memória isolada em arquivos JSON.
"""

import json
from pathlib import Path
from datetime import datetime
from loguru import logger


class Memory:
    """
    Gerencia a memória persistente de um condomínio.

    Estrutura:
        condominios/<slug>/memoria/
            contratos.json   — dados extraídos de contratos
            atas.json         — decisões e deliberações de assembleias
            historico.json    — histórico de auditorias e achados
    """

    def __init__(self, condominio_path: Path):
        self.memoria_path = condominio_path / "memoria"
        self.memoria_path.mkdir(parents=True, exist_ok=True)

        self._contratos = self._load("contratos.json")
        self._atas = self._load("atas.json")
        self._historico = self._load("historico.json")

    def _load(self, filename: str) -> dict:
        filepath = self.memoria_path / filename
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"registros": [], "atualizado_em": None}

    def _save(self, filename: str, data: dict):
        data["atualizado_em"] = datetime.now().isoformat()
        filepath = self.memoria_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- Contratos ---

    @property
    def contratos(self) -> list:
        return self._contratos.get("registros", [])

    def add_contrato(self, contrato: dict):
        self._contratos["registros"].append({
            **contrato,
            "registrado_em": datetime.now().isoformat()
        })
        self._save("contratos.json", self._contratos)
        logger.info(f"Contrato registrado: {contrato.get('fornecedor', 'N/A')}")

    def get_contrato_por_fornecedor(self, fornecedor: str) -> list:
        return [
            c for c in self.contratos
            if fornecedor.lower() in c.get("fornecedor", "").lower()
        ]

    # --- Atas ---

    @property
    def atas(self) -> list:
        return self._atas.get("registros", [])

    def add_ata(self, ata: dict):
        self._atas["registros"].append({
            **ata,
            "registrado_em": datetime.now().isoformat()
        })
        self._save("atas.json", self._atas)
        logger.info(f"Ata registrada: {ata.get('data', 'N/A')}")

    def get_decisoes_assembleia(self, data: str = None) -> list:
        if data:
            return [a for a in self.atas if a.get("data") == data]
        return self.atas

    # --- Histórico de Auditoria ---

    @property
    def historico(self) -> list:
        return self._historico.get("registros", [])

    def add_achado(self, achado: dict):
        self._historico["registros"].append({
            **achado,
            "registrado_em": datetime.now().isoformat()
        })
        self._save("historico.json", self._historico)
        logger.info(f"Achado registrado: {achado.get('tipo', 'N/A')} — {achado.get('descricao', '')[:60]}")

    def get_achados_por_severidade(self, severidade: str) -> list:
        return [
            a for a in self.historico
            if a.get("severidade", "").lower() == severidade.lower()
        ]

    def get_achados_por_agente(self, agente: str) -> list:
        return [
            a for a in self.historico
            if a.get("agente", "").lower() == agente.lower()
        ]

    def resumo(self) -> dict:
        return {
            "total_contratos": len(self.contratos),
            "total_atas": len(self.atas),
            "total_achados": len(self.historico),
            "achados_criticos": len(self.get_achados_por_severidade("critico")),
            "achados_atencao": len(self.get_achados_por_severidade("atencao")),
            "achados_info": len(self.get_achados_por_severidade("info")),
        }
