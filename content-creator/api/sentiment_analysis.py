"""
Wrapper module to handle sentiment-analysis directory with dash in name
"""
import sys
import importlib.util
from pathlib import Path

# Load the sentiment_analysis module directly from init file
sentiment_analysis_path = Path(__file__).parent / "sentiment-analysis" / "__init__.py"
spec = importlib.util.spec_from_file_location("sentiment_analysis_module", sentiment_analysis_path)
sentiment_analysis_module = importlib.util.module_from_spec(spec)
sys.modules["sentiment_analysis_module"] = sentiment_analysis_module
spec.loader.exec_module(sentiment_analysis_module)

# Export the classes from the module
SentimentAnalysisPipeline = sentiment_analysis_module.SentimentAnalysisPipeline
SentimentAnalysisPipelineFactory = sentiment_analysis_module.SentimentAnalysisPipelineFactory