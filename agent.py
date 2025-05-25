# -*- coding: utf-8 -*-
from agents import Agent, Runner, ModelSettings,set_default_openai_key, function_tool, trace, TResponseInputItem, MessageOutputItem, HandoffOutputItem, ToolCallItem, ToolCallOutputItem
from pydantic import BaseModel
from openai import OpenAI
import os
import logging
from pathlib import Path
import json


set_default_openai_key(key = os.getenv("OPENAI_API_KEY_AC"),  use_for_tracing = True)

# Configuração do logger
logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_AC"))

class salesAgent(BaseModel):
    """
    Classe para representar um agente de vendas.
    """

def speech_to_text(audio_file: bytes) -> str:
    """
    Função para converter áudio em texto usando o modelo Whisper.
    Args:
        ctx (RunContextWrapper): Contexto de execução do agente.
        audio_file (base64): Arquivo de áudio em base64.
    Returns:
        str: O texto convertido do áudio.
    """

    logger.info("Iniciando transcrição de áudio.")

    transcription = client.audio.transcriptions.create(
            model="gpt-4o-transcribe", 
            file=(audio_file),
            response_format="text",
            language="pt"
            )
    
    logger.info("Transcrição de áudio concluída.")
    logger.info(f"Transcrição: {transcription}")

    return transcription

# lendo o esquema de saída esperado para o agente de vendas do arquivo output_json_schema.json
output_schema_path = Path(__file__).parent / "output_json_schema.json"
with open(output_schema_path, 'r', encoding='utf-8') as file:
    output_schema = json.load(file)
#     
salesAssistant = Agent[salesAgent](
    name="Sales Assistant",
    instructions=f"""Você é um experiente assistente de vendas. Os vendedores vão enviar para você textos sobre conversas com os clientes 
            e com base nisso você deve extrair as informações necessárias para criar ou atualizar os dados do lead no CRM.  
            Caso não tenha todas as informações requeridas no output json schema {output_schema}, deixe como NULL
            retorne somente o objeto json""",
    model="gpt-4o-mini",
    model_settings=ModelSettings(temperature=0.0)
)

def assemble_conversation(history, transcription):
    logger.info("Montando conversa com histórico")
    if history:
        # Se o histórico for uma lista, usamos diretamente
        if isinstance(history, list):
            logger.info("Usando histórico em formato de lista")
            return history + [{"content": transcription, "role": "user"}]
        # Se for um objeto com o método to_input_list, usamos o método
        elif hasattr(history, 'to_input_list'):
            logger.info("Usando histórico com método to_input_list")
            return history.to_input_list() + [{"content": transcription, "role": "user"}]
    logger.info("Iniciando nova conversa sem histórico")
    return [{"content": transcription, "role": "user"}]

async def answers(transcription: str, history: str) -> dict:
    """
    Função principal para processar a resposta do agente de vendas.
    Args:
        audio_file (object): Arquivo de áudio em base64.
    Returns:
        dict: o objeto json com os dados do cliente e o resumo da conversa.
    """
    logger.info("Iniciando processamento de resposta")
    context = salesAgent()
    result: list[TResponseInputItem] = []

    while True:
        with trace(workflow_name='chatDataAnalyst'):
            logger.info("Executando agente para processar pergunta")
            result = await Runner.run(salesAssistant, assemble_conversation(history, transcription), context=context)

            for new_item in result.new_items:
                logger.debug(f'Processando item do tipo: {type(new_item)}')
                agent_name = new_item.agent.name

                if isinstance(new_item, MessageOutputItem):
                    logger.info(f"{agent_name}: Mensagem gerada")
                elif isinstance(new_item, HandoffOutputItem):
                    logger.info(f"Transferência de {new_item.source_agent.name} para {new_item.target_agent.name}")
                elif isinstance(new_item, ToolCallItem):
                    logger.info(f"{agent_name}: Chamando ferramenta {new_item.tool.raw_item}")
                elif isinstance(new_item, ToolCallOutputItem):
                    logger.info(f"{agent_name}: Resultado da ferramenta obtido")
                else:
                    logger.debug(f"{agent_name}: Item ignorado: {new_item.__class__.__name__}")

            logger.info("Processamento concluído")
            return result.final_output