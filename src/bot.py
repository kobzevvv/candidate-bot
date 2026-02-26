"""Pipecat pipeline for the candidate bot."""
from __future__ import annotations

import logging

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.daily.transport import DailyParams, DailyTransport
from pipecat.turns.user_start.vad_user_turn_start_strategy import VADUserTurnStartStrategy
from pipecat.turns.user_stop.speech_timeout_user_turn_stop_strategy import (
    SpeechTimeoutUserTurnStopStrategy,
)
from pipecat.turns.user_turn_strategies import UserTurnStrategies

from src.config import Settings
from src.persona import CandidatePersona, build_system_prompt

logger = logging.getLogger(__name__)


async def run_candidate_bot(
    room_url: str,
    persona: CandidatePersona,
    settings: Settings,
) -> None:
    """Build and run the full Pipecat pipeline. Blocks until the call ends."""
    system_prompt = build_system_prompt(persona)

    vad_analyzer = SileroVADAnalyzer(
        params=VADParams(
            stop_secs=settings.vad_stop_secs,
        )
    )

    # Guest join — no token needed for public Daily rooms
    transport = DailyTransport(
        room_url,
        None,
        f"{persona.name} (candidate)",
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            camera_out_enabled=False,
            vad_analyzer=vad_analyzer,
        ),
    )

    stt = _build_stt(settings)

    llm = OpenAILLMService(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )

    tts = ElevenLabsTTSService(
        api_key=settings.elevenlabs_api_key,
        voice_id=settings.elevenlabs_voice_id,
    )

    context = LLMContext(
        messages=[{"role": "system", "content": system_prompt}]
    )

    user_params = LLMUserAggregatorParams(
        user_turn_strategies=UserTurnStrategies(
            start=[VADUserTurnStartStrategy()],
            stop=[SpeechTimeoutUserTurnStopStrategy(
                user_speech_timeout=settings.user_speech_timeout
            )],
        ),
    )

    pair = LLMContextAggregatorPair(context, user_params=user_params)

    pipeline = Pipeline([
        transport.input(),
        stt,
        pair.user(),
        llm,
        tts,
        transport.output(),
        pair.assistant(),
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
        ),
    )

    runner = PipelineRunner(handle_sigint=False)

    logger.info("Candidate bot joining room: %s as '%s'", room_url, persona.name)
    await runner.run(task)
    logger.info("Candidate bot left room: %s", room_url)


def _build_stt(settings: Settings):
    if settings.stt_provider == "deepgram" and settings.deepgram_api_key:
        from pipecat.services.deepgram.stt import DeepgramSTTService
        return DeepgramSTTService(api_key=settings.deepgram_api_key)

    from pipecat.services.openai.stt import OpenAISTTService
    return OpenAISTTService(api_key=settings.openai_api_key)
