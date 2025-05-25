
# -*- coding: utf-8 -*-
# a streamlit app to run the audio-crm project
# author: "Bruno Curtarelli"
# the audio-crm project is a project to create an AI agent that receives audio input and generates a CRM entry
# the app is quite simple, it just receive the audio input, which is  processed by the AI agent and returns a json oject
# the json object is then evaluated by the sales person, who can accept or edit the entry before sending it to the CRM in supabase


def main():
    
    import streamlit as st
    from supabase_client import SupabaseClient
    import os
    import logging
    import asyncio
    from agent import answers, speech_to_text

    logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gata_guru.log')
    ]
    )
    logger = logging.getLogger(__name__)

    # Configuração do Supabase
    url = os.getenv("SUPABASE_DB_URL")
    key = os.getenv("SUPABASE_DB_PASS")
    supabase_client = SupabaseClient(url, key)

    st.title("Audio CRM")

    # Gravação de áudio
    audio_file = st.audio_input("Grave seu áudio", key="audio-input")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        logger.info("Histórico de chat inicializado")
    if "transcription" not in st.session_state:
        st.session_state.transcription = None


    col1, col2, col3 = st.columns(3)
    with col3:
        limpar = st.button("Limpar histórico", use_container_width=True)
    with col2:
        salvar = st.button("Salvar no CRM", use_container_width=True)
    with col1:
        transcrever = st.button("Executar transcrição", use_container_width=True)

    # Mensagem placeholder ao clicar em "Limpar histórico"
    if limpar:
        st.info(f"Histórico apagado: {st.session_state.chat_history}")
        st.session_state.pop("chat_history", None)
        st.session_state.pop("transcription", None)
        logger.info("Histórico de chat e transcrição limpos")

    # Mensagem placeholder ao clicar em "Salvar no CRM"
    if salvar:
        st.info("Funcionalidade de salvar no CRM em breve!")

    # Só executa a transcrição se o botão for pressionado e houver áudio
    if transcrever and audio_file is not None:
        logger.info(f"Novo audio recebido do tipo {audio_file.type} com tamanho {audio_file.size} bytes")

        # encoding audio file
        transcription = speech_to_text(audio_file)
        logger.info(f"Audio transcrito com sucesso")
        
        with st.spinner("Pensando..."):
            try:
                logger.info("Iniciando processamento da resposta")
                response = asyncio.run(answers(transcription, st.session_state.chat_history))
                st.session_state.transcription = transcription  # Salva a transcrição no estado
                st.session_state.chat_history.append({"role": "user", "content": transcription})
                logger.info("Resposta processada com sucesso")
                st.markdown(response)
                logger.info("Resposta exibida para o usuário")
            except Exception as e:
                logger.error(f"Erro ao processar pergunta: {str(e)}", exc_info=True)
                st.error(f"Ocorreu um erro ao processar sua pergunta: {str(e)}")
                st.info("Por favor, tente novamente.")

    # Exibe a transcrição apenas se existir
    if st.session_state.get("transcription"):
        st.write(f"Transcrição do áudio: {st.session_state.transcription}")


if __name__ == "__main__":
    main()
