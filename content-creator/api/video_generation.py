"""
Wrapper module to handle video-generation directory with dash in name
"""
import sys
import importlib.util
from pathlib import Path

# Load the video_pipeline module directly
video_pipeline_path = Path(__file__).parent / "video-generation" / "video_pipeline.py"
spec = importlib.util.spec_from_file_location("video_pipeline_module", video_pipeline_path)
video_pipeline_module = importlib.util.module_from_spec(spec)
sys.modules["video_pipeline_module"] = video_pipeline_module
spec.loader.exec_module(video_pipeline_module)

# Export the classes
VideoGenerationPipeline = video_pipeline_module.VideoGenerationPipeline
VideoComposition = video_pipeline_module.VideoComposition