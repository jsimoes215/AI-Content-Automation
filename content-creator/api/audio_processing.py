"""
Wrapper module to handle audio-processing directory with dash in name
"""
import sys
import importlib.util
from pathlib import Path

# Load the audio_pipeline module directly
audio_pipeline_path = Path(__file__).parent / "audio-processing" / "audio_pipeline.py"
spec = importlib.util.spec_from_file_location("audio_pipeline_module", audio_pipeline_path)
audio_pipeline_module = importlib.util.module_from_spec(spec)
sys.modules["audio_pipeline_module"] = audio_pipeline_module
spec.loader.exec_module(audio_pipeline_module)

# Export the classes
AudioPipeline = audio_pipeline_module.AudioPipeline
AudioMix = audio_pipeline_module.AudioMix