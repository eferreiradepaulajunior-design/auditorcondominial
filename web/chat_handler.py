"""
Handler central de chat.
Recebe mensagens do usuário, roteia para o agente correto,
gerencia delegação do Gestor e retorna respostas.
"""

import os
import re
import asyncio
from pathlib import Path
from loguru import logger

from web.database import (
    get_or_create_conversation, get_conversation_messages,
    save_message, get_setting
)
from web.agent_profiles import get_profile, AGENT_PROFILES
from core.llm_router import LLMRouter
from core.meta_agent import MetaAgent

# Carregar skills disponíveis
SKILLS_PATH = Path(__file__).resolve().parent.parent / "skills"


def _load_skill(agent_id: str) -> str:
    """Carrega o SKILL.md do agente, se existir."""
    skill_map = {
        "financial": "financial",
        "contracts": "contracts",
        "maintenance": "maintenance",
        "compliance": "compliance",
        "gestor": "meta",
        "context": None,
        "investment": None,
    }
    folder = skill_map.get(agent_id)
    if not folder:
        return ""

    skill_file = SKILLS_PATH / folder / "SKILL.md"
    if skill_file.exists():
        return f"\n\n--- INSTRUÇÕES TÉCNICAS ---\n{skill_file.read_text(encoding='utf-8')}"
    return ""


def _get_api_key(provider: str) -> str:
    """Busca chave de API: primeiro no banco, depois no .env."""
    key_map = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    env_name = key_map.get(provider, "")
    # Tenta o banco de dados primeiro
    db_val = get_setting(env_name)
    if db_val:
        return db_val
    return os.getenv(env_name, "")


def _get_provider_for_agent(agent_id: str):
    """Retorna o provider configurado para o agente."""
    # Configuração padrão por agente (pode ser customizada via admin)
    default_config = {
        "gestor":      {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
        "context":     {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
        "financial":   {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
        "contracts":   {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
        "maintenance": {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
        "investment":  {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
        "compliance":  {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
    }

    # Verifica se há configuração customizada no banco
    provider_name = get_setting(f"agent_{agent_id}_provider") or default_config[agent_id]["provider"]
    model_name = get_setting(f"agent_{agent_id}_model") or default_config[agent_id]["model"]
    api_key = _get_api_key(provider_name)

    if not api_key:
        raise ValueError(
            f"Chave de API não configurada para o provedor '{provider_name}'. "
            f"Configure em Admin > Chaves de API."
        )

    router = LLMRouter()
    # Inject the api key into env temporarily for the router
    env_key = {"gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY",
               "groq": "GROQ_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}[provider_name]

    original = os.environ.get(env_key)
    os.environ[env_key] = api_key
    try:
        provider = router.get(provider_name, model_name)
    finally:
        if original is not None:
            os.environ[env_key] = original
        elif env_key in os.environ:
            del os.environ[env_key]

    return provider


def _build_system_prompt(agent_id: str) -> str:
    """Monta o system prompt com persona + skill."""
    profile = get_profile(agent_id)
    persona = profile["persona"]
    skill = _load_skill(agent_id)
    return persona + skill


def _build_chat_messages(conversation_id: int, new_message: str) -> list[dict]:
    """Monta a lista de mensagens para enviar ao LLM."""
    history = get_conversation_messages(conversation_id, limit=30)
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": new_message})
    return messages


def _format_messages_for_llm(messages: list[dict]) -> str:
    """Formata mensagens como texto para LLMs que não suportam multi-turn nativo."""
    parts = []
    for msg in messages:
        prefix = "Usuário" if msg["role"] == "user" else "Você"
        parts.append(f"{prefix}: {msg['content']}")
    return "\n\n".join(parts)


# ── Delegação do Gestor ──────────────────────────────────────────

DELEGATION_PATTERN = re.compile(r'\[DELEGAR:(\w+)\](.*?)\[/DELEGAR\]', re.DOTALL)
CREATE_AGENT_PATTERN = re.compile(r'\[CRIAR_AGENTE\](.*?)\[/CRIAR_AGENTE\]', re.DOTALL)


def _handle_delegation(response_text: str) -> str:
    """
    Detecta markers de delegação na resposta do Gestor.
    Se encontrados, chama o agente delegado e substitui o marker pelo resultado.
    """
    delegations = DELEGATION_PATTERN.findall(response_text)
    if not delegations:
        return response_text

    result = response_text
    for agent_id, task in delegations:
        agent_id = agent_id.strip()
        task = task.strip()

        if agent_id not in AGENT_PROFILES or agent_id == "gestor":
            continue

        try:
            logger.info(f"Gestor delegando para {agent_id}: {task[:80]}...")
            provider = _get_provider_for_agent(agent_id)
            system = _build_system_prompt(agent_id)
            prompt = f"O Gestor Carlos pediu que você analise o seguinte:\n\n{task}"

            llm_response = provider.complete(system_prompt=system, user_message=prompt)
            agent_name = get_profile(agent_id)["name"]

            # Substitui o marker pela resposta do agente
            marker = f"[DELEGAR:{agent_id}]{task}[/DELEGAR]"
            replacement = (
                f"\n\n📋 **Relatório de {agent_name}:**\n{llm_response.content}\n"
            )
            result = result.replace(marker, replacement)

        except Exception as e:
            logger.error(f"Erro na delegação para {agent_id}: {e}")
            marker = f"[DELEGAR:{agent_id}]{task}[/DELEGAR]"
            agent_name = get_profile(agent_id)["name"]
            result = result.replace(
                marker,
                f"\n\n⚠️ Não consegui contato com {agent_name} no momento. Erro: {str(e)}\n"
            )

    return result


def _handle_agent_creation(response_text: str, condominio: str) -> str:
    """Detecta markers de criação de agente e executa via MetaAgent."""
    creations = CREATE_AGENT_PATTERN.findall(response_text)
    if not creations:
        return response_text

    result = response_text
    for description in creations:
        description = description.strip()
        try:
            logger.info(f"Gestor criando agente: {description[:80]}...")
            meta = MetaAgent(condominio=condominio)
            creation_result = meta.create_agent(necessidade=description)

            marker = f"[CRIAR_AGENTE]{description}[/CRIAR_AGENTE]"
            if creation_result.get("status") == "sucesso":
                replacement = (
                    f"\n\n✅ **Novo agente criado com sucesso!**\n"
                    f"- Nome: {creation_result.get('agent_name', 'N/A')}\n"
                    f"- Classe: {creation_result.get('class_name', 'N/A')}\n"
                    f"- Arquivos: {', '.join(creation_result.get('arquivos_criados', []))}\n"
                )
            else:
                replacement = (
                    f"\n\n⚠️ Não foi possível criar o agente: {creation_result.get('erro', 'Erro desconhecido')}\n"
                )
            result = result.replace(marker, replacement)

        except Exception as e:
            logger.error(f"Erro na criação de agente: {e}")
            marker = f"[CRIAR_AGENTE]{description}[/CRIAR_AGENTE]"
            result = result.replace(marker, f"\n\n⚠️ Erro ao criar agente: {str(e)}\n")

    return result


# ── Função principal de chat ─────────────────────────────────────

async def process_chat_message(
    user_id: int,
    agent_id: str,
    message: str,
    condominio: str = "parque_colibri"
) -> dict:
    """
    Processa uma mensagem de chat e retorna a resposta do agente.

    Returns:
        {"agent_id": str, "agent_name": str, "content": str, "conversation_id": int}
    """
    profile = get_profile(agent_id)

    # Obter ou criar conversa
    conv_id = get_or_create_conversation(user_id, agent_id, condominio)

    # Salvar mensagem do usuário
    save_message(conv_id, "user", message)

    try:
        # Obter provider e montar prompt
        provider = _get_provider_for_agent(agent_id)
        system_prompt = _build_system_prompt(agent_id)
        chat_messages = _build_chat_messages(conv_id, message)
        formatted = _format_messages_for_llm(chat_messages[:-1])  # sem a última (já no prompt)

        # Prompt com histórico
        if formatted:
            full_prompt = f"Histórico da conversa:\n{formatted}\n\nUsuário: {message}"
        else:
            full_prompt = message

        # Chamar LLM em thread separada (não bloquear o event loop)
        llm_response = await asyncio.to_thread(
            provider.complete,
            system_prompt=system_prompt,
            user_message=full_prompt,
        )

        response_text = llm_response.content

        # Se é o Gestor, processar delegações e criações
        if agent_id == "gestor":
            response_text = await asyncio.to_thread(
                _handle_delegation, response_text
            )
            response_text = await asyncio.to_thread(
                _handle_agent_creation, response_text, condominio
            )

        # Limpar markers que sobraram
        response_text = DELEGATION_PATTERN.sub('', response_text)
        response_text = CREATE_AGENT_PATTERN.sub('', response_text)

        # Salvar resposta
        save_message(conv_id, "assistant", response_text)

        return {
            "agent_id": agent_id,
            "agent_name": profile["name"],
            "avatar": profile["avatar"],
            "content": response_text,
            "conversation_id": conv_id,
        }

    except Exception as e:
        logger.error(f"Erro no chat com {agent_id}: {e}")
        error_msg = f"Desculpe, estou com dificuldade técnica no momento. Erro: {str(e)}"
        save_message(conv_id, "assistant", error_msg)
        return {
            "agent_id": agent_id,
            "agent_name": profile["name"],
            "avatar": profile["avatar"],
            "content": error_msg,
            "conversation_id": conv_id,
        }
