# 🎬 Automated Content Creator

A comprehensive AI-powered content generation system that transforms video ideas into multi-platform content with professional audio, video, and social media adaptations.

## ✨ Features

### 🎯 Core Capabilities
- **Idea-to-Script AI**: Convert video ideas into structured scripts with scene breakdowns
- **Multi-Platform Content**: Generate content optimized for YouTube, TikTok, Instagram, LinkedIn, and X
- **Professional Audio**: AI-generated voiceovers with background music integration
- **Video Generation**: Text-to-video and image-to-video pipeline with scene composition
- **Content Library**: Intelligent scene storage with meta-tagging and semantic search
- **Platform Optimization**: Automatic adaptation for platform-specific requirements

### 🚀 Platform Support
- **YouTube**: Longform videos (7-15 minutes, 16:9, comprehensive)
- **TikTok**: Shortform content (15-60 seconds, 9:16, hook-focused)
- **Instagram**: Reels (15-90 seconds, 9:16, visual-focused)
- **LinkedIn**: Professional text posts with engagement optimization
- **X (Twitter)**: Concise tweets and threads

## 🏗️ Architecture

### Pipeline Components
```
Video Idea → Script Generation → Audio Processing → Video Generation → Platform Adaptation
```

1. **Script Generator**: Transforms ideas into structured scripts with scenes, timing, and platform adaptations
2. **Audio Pipeline**: Generates voiceovers and background music with professional mixing
3. **Video Pipeline**: Creates video segments from scenes with transitions and effects
4. **Content Library**: Stores reusable scenes with meta-tagging and intelligent retrieval
5. **Platform Adapters**: Optimizes content for each platform's specific requirements

### Project Structure
```
content-creator/
├── api/                      # Core pipeline components
│   ├── scripts/             # Script generation engines
│   ├── audio_processing/    # Audio pipeline with TTS/music
│   ├── video_generation/    # Video generation and composition
│   ├── content_library/     # Scene storage and management
│   └── main_pipeline.py     # Pipeline orchestration
├── config/                  # System configuration
├── tests/                   # Comprehensive test suite
├── generated-content/       # Output files and assets
├── content-library/         # Scene storage and embeddings
└── data/                    # Database and analytics
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MiniMax AI services (audio_kit, video_kit, image_gen toolkits)

### Installation
```bash
# Clone the repository
git clone https://github.com/jsimoes215/AI-Content-Automation.git
cd AI-Content-Automation

# Install dependencies
pip install -r requirements.txt

# Run tests
python tests/test_simple_pipeline.py
```

### Basic Usage
```python
from api.scripts.simple_generator import SimpleScriptGenerator
from api.main_pipeline import ContentCreationRequest

# Generate content from an idea
generator = SimpleScriptGenerator()
script = generator.generate_script(
    idea="How AI can improve your daily productivity",
    target_audience="busy professionals",
    tone="educational",
    platform="youtube"
)

print(f"Generated script: {script['title']}")
print(f"Duration: {script['total_duration']} seconds")
print(f"Scenes: {len(script['scenes'])}")
```

## 📊 Implementation Status

### ✅ Completed (Steps 1-3)
- [x] Research and requirements analysis
- [x] System architecture and pipeline design  
- [x] Core automation pipeline implementation

### 🚧 In Progress (Step 4)
- [ ] YouTube longform video processor
- [ ] TikTok/Instagram short-form extractor
- [ ] Text content generator for social media
- [ ] Thumbnail generation system

### 📋 Planned (Steps 5-7)
- [ ] User interface and workflow management
- [ ] Comment scraping and feedback system
- [ ] System testing and optimization

## 🧪 Testing

The system includes comprehensive test coverage:

```bash
# Run simplified pipeline tests
python tests/test_simple_pipeline.py

# Run complete pipeline tests  
python tests/test_complete_pipeline.py
```

### Test Results
```
🚀 Testing Simplified Content Pipeline
📝 Test Case 1: AI Productivity
✅ Status: completed
⏱️ Duration: 330s | 🎬 Scenes: 5 | 📱 Platforms: ['youtube', 'tiktok']
⏱️ Processing: 15.5s

📝 Test Case 2: Quick TikTok Tutorial  
✅ Status: completed
📱 Platform: ['tiktok', 'instagram']
```

## 🛠️ Configuration

Key configuration settings in `config/settings.py`:

### Platform Requirements
- **YouTube**: 1920x1080, 16:9, 300-900 seconds
- **TikTok**: 1080x1920, 9:16, 15-60 seconds  
- **Instagram**: 1080x1920, 9:16, 15-90 seconds

### Content Settings
- **Script**: Max 10 scenes, 15-120 seconds per scene
- **Audio**: 44.1kHz sample rate, MP3 format, professional mixing
- **Video**: 30 FPS, high quality, platform-specific optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🎯 Next Steps

Ready for Step 4: Platform-Specific Content Generators
- Build YouTube longform processor (combine scenes, optimize 8-15 min duration)
- Create TikTok/Instagram extractor (vertical 9:16 format)
- Implement text content generator for X and LinkedIn
- Add thumbnail generation and scene re-use system

---

**Built with ❤️ using MiniMax AI services for automated content creation**