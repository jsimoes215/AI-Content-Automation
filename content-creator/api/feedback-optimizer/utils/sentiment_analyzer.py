"""
Sentiment Analysis Utility Module

Provides comprehensive sentiment analysis for feedback text and metadata.
"""

import re
import math
from typing import Dict, List, Any, Tuple, Optional
from collections import Counter, defaultdict

from ..models.sentiment_metrics import SentimentMetrics


class SentimentAnalyzer:
    """
    Advanced sentiment analysis using hybrid approach combining rule-based and pattern matching.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the sentiment analyzer with configuration."""
        self.config = config or self._default_config()
        self.positive_words = set(self._load_positive_words())
        self.negative_words = set(self._load_negative_words())
        self.intensity_words = self._load_intensity_words()
        self.emotion_indicators = self._load_emotion_indicators()
        
    def _default_config(self) -> Dict:
        """Default configuration for sentiment analysis."""
        return {
            'confidence_threshold': 0.6,
            'negation_lookback': 3,
            'intensity_modifier_multiplier': 1.5,
            'context_window_size': 5,
            'emotion_weights': {
                'joy': 1.0,
                'anger': 0.8,
                'fear': 0.7,
                'sadness': 0.6,
                'surprise': 0.9,
                'disgust': 0.7
            }
        }
    
    def analyze_sentiment(self, text: str, metadata: Optional[Dict] = None) -> SentimentMetrics:
        """
        Comprehensive sentiment analysis of text.
        
        Args:
            text: Text to analyze
            metadata: Additional metadata for context analysis
            
        Returns:
            SentimentMetrics object with detailed analysis results
        """
        if not text:
            return SentimentMetrics()
        
        # Clean and preprocess text
        cleaned_text = self._preprocess_text(text)
        
        # Core sentiment analysis
        overall_sentiment = self._analyze_overall_sentiment(cleaned_text)
        emotion_breakdown = self._analyze_emotions(cleaned_text)
        
        # Additional analysis
        confidence_score = self._calculate_confidence_score(cleaned_text, overall_sentiment)
        subjectivity = self._calculate_subjectivity(cleaned_text)
        polarity_distribution = self._calculate_polarity_distribution(cleaned_text)
        
        # Text features
        sentiment_keywords = self._extract_sentiment_keywords(cleaned_text)
        opinion_words = self._extract_opinion_words(cleaned_text)
        intensity_modifiers = self._extract_intensity_modifiers(cleaned_text)
        
        # Context and topic analysis
        context_sentiment = self._analyze_context_sentiment(cleaned_text, metadata or {})
        topic_sentiment = self._analyze_topic_sentiment(cleaned_text)
        
        return SentimentMetrics(
            overall_sentiment=overall_sentiment,
            emotion_breakdown=emotion_breakdown,
            confidence_score=confidence_score,
            subjectivity=subjectivity,
            polarity_distribution=polarity_distribution,
            sentiment_keywords=sentiment_keywords,
            opinion_words=opinion_words,
            intensity_modifiers=intensity_modifiers,
            context_sentiment=context_sentiment,
            topic_sentiment=topic_sentiment,
            word_count=len(cleaned_text.split()),
            sentence_count=len(re.findall(r'[.!?]+', text)),
            language='en',  # Could be made configurable
            analysis_method='hybrid'
        )
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Handle hashtags and mentions
        text = re.sub(r'#[A-Za-z0-9_]+', ' ', text)
        text = re.sub(r'@[A-Za-z0-9_]+', ' ', text)
        
        # Normalize emoticons
        text = self._normalize_emoticons(text)
        
        return text.strip()
    
    def _normalize_emoticons(self, text: str) -> str:
        """Convert common emoticons to text representations."""
        emoticon_mapping = {
            '😊': 'happy', '😄': 'happy', '😃': 'happy', '😁': 'happy',
            '😢': 'sad', '😭': 'sad', '😞': 'sad', '😔': 'sad',
            '😠': 'angry', '😡': 'angry', '😤': 'angry',
            '😱': 'fearful', '😨': 'fearful', '😰': 'fearful',
            '😮': 'surprised', '😲': 'surprised', '🤔': 'surprised',
            '😷': 'disgusted', '🤢': 'disgusted', '🤮': 'disgusted'
        }
        
        for emoticon, word in emoticon_mapping.items():
            text = text.replace(emoticon, word)
        
        return text
    
    def _analyze_overall_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze overall sentiment using rule-based approach."""
        words = text.split()
        
        if not words:
            return {'label': 'neutral', 'score': 0.0}
        
        sentiment_score = 0.0
        word_count = 0
        negation_count = 0
        
        for i, word in enumerate(words):
            word_score = 0.0
            
            # Check for negations (look back up to negation_lookback words)
            negation_context = words[max(0, i-self.config['negation_lookback']):i]
            has_negation = any(neg_word in negation_context for neg_word in ['not', 'no', 'never', 'none', 'nothing', 'neither', 'nor', 'hardly', 'barely'])
            
            if word in self.positive_words:
                word_score = 1.0
            elif word in self.negative_words:
                word_score = -1.0
            
            # Apply negation
            if has_negation and word_score != 0:
                word_score = -word_score
            
            # Apply intensity modifiers
            intensity_multiplier = self._get_intensity_multiplier(word, i, words)
            word_score *= intensity_multiplier
            
            sentiment_score += word_score
            word_count += 1
        
        # Calculate final sentiment
        if word_count == 0:
            final_score = 0.0
        else:
            final_score = sentiment_score / word_count
        
        # Determine sentiment label
        if final_score > 0.1:
            label = 'positive'
        elif final_score < -0.1:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'label': label,
            'score': max(-1.0, min(1.0, final_score))
        }
    
    def _analyze_emotions(self, text: str) -> Dict[str, float]:
        """Analyze specific emotions in the text."""
        words = text.split()
        emotion_scores = {
            'joy': 0.0,
            'anger': 0.0,
            'fear': 0.0,
            'sadness': 0.0,
            'surprise': 0.0,
            'disgust': 0.0
        }
        
        emotion_words = defaultdict(list)
        
        for word in words:
            for emotion, word_list in self.emotion_indicators.items():
                if word in word_list:
                    emotion_scores[emotion] += 1.0
                    emotion_words[emotion].append(word)
        
        # Normalize scores
        total_score = sum(emotion_scores.values())
        if total_score > 0:
            emotion_scores = {k: v / total_score for k, v in emotion_scores.items()}
        
        return emotion_scores
    
    def _calculate_confidence_score(self, text: str, sentiment: Dict[str, Any]) -> float:
        """Calculate confidence in the sentiment analysis."""
        if not text:
            return 0.0
        
        # Factors that increase confidence:
        # 1. Text length (more words = more confidence)
        # 2. Sentiment strength (stronger sentiment = more confidence)
        # 3. Number of sentiment words found
        # 4. Consistency of sentiment direction
        
        word_count = len(text.split())
        sentiment_strength = abs(sentiment['score'])
        
        # Count sentiment-bearing words
        sentiment_words = 0
        for word in text.split():
            if word in self.positive_words or word in self.negative_words:
                sentiment_words += 1
        
        # Calculate confidence based on factors
        confidence = 0.0
        
        # Length factor (0-0.4)
        if word_count > 50:
            confidence += 0.4
        elif word_count > 20:
            confidence += 0.3
        elif word_count > 10:
            confidence += 0.2
        elif word_count > 5:
            confidence += 0.1
        
        # Sentiment strength factor (0-0.3)
        confidence += sentiment_strength * 0.3
        
        # Sentiment word count factor (0-0.3)
        if sentiment_words > 0:
            confidence += min(0.3, sentiment_words * 0.1)
        
        return min(1.0, confidence)
    
    def _calculate_subjectivity(self, text: str) -> float:
        """Calculate subjectivity score (0 = objective, 1 = subjective)."""
        words = text.split()
        if not words:
            return 0.0
        
        # Count subjective indicators
        subjective_indicators = 0
        opinion_words_count = 0
        
        for word in words:
            if word in ['i', 'you', 'he', 'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them']:
                subjective_indicators += 1
            if word in self.positive_words or word in self.negative_words:
                opinion_words_count += 1
            if word in ['think', 'believe', 'feel', 'opinion', 'view', 'perspective']:
                subjective_indicators += 2
        
        # Calculate subjectivity score
        total_factors = len(words) + subjective_indicators + opinion_words_count
        if total_factors == 0:
            return 0.0
        
        subjectivity = (subjective_indicators + opinion_words_count) / total_factors
        return min(1.0, subjectivity)
    
    def _calculate_polarity_distribution(self, text: str) -> Dict[str, float]:
        """Calculate distribution of positive, negative, and neutral content."""
        words = text.split()
        if not words:
            return {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33}
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        neutral_count = len(words) - positive_count - negative_count
        
        total = len(words)
        return {
            'positive': positive_count / total,
            'negative': negative_count / total,
            'neutral': neutral_count / total
        }
    
    def _extract_sentiment_keywords(self, text: str) -> List[str]:
        """Extract keywords that contribute to sentiment."""
        words = text.split()
        sentiment_words = []
        
        for word in words:
            if word in self.positive_words or word in self.negative_words:
                sentiment_words.append(word)
        
        return sentiment_words
    
    def _extract_opinion_words(self, text: str) -> List[str]:
        """Extract explicit opinion indicators."""
        words = text.split()
        opinion_words = []
        
        for word in words:
            if word in ['think', 'believe', 'feel', 'opinion', 'view', 'perspective', 'consider', 'reckon']:
                opinion_words.append(word)
        
        return opinion_words
    
    def _extract_intensity_modifiers(self, text: str) -> List[str]:
        """Extract intensity-modifying words."""
        words = text.split()
        intensity_modifiers = []
        
        for word in words:
            if word in self.intensity_words:
                intensity_modifiers.append(word)
        
        return intensity_modifiers
    
    def _analyze_context_sentiment(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment in context of metadata."""
        context_sentiment = {
            'platform_adjustment': 0.0,
            'user_type_adjustment': 0.0,
            'time_context': 0.0
        }
        
        # Platform-based adjustments
        platform = metadata.get('platform', '').lower()
        if 'youtube' in platform:
            context_sentiment['platform_adjustment'] = 0.05  # Slightly more positive expected
        elif 'twitter' in platform or 'x' in platform:
            context_sentiment['platform_adjustment'] = -0.02  # Slightly more negative expected
        
        return context_sentiment
    
    def _analyze_topic_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment by topic clusters."""
        # Simplified topic sentiment analysis
        topic_sentiment = {}
        
        # Define topic keywords (this could be expanded significantly)
        topics = {
            'technology': ['tech', 'software', 'app', 'digital', 'computer', 'internet'],
            'politics': ['politics', 'government', 'policy', 'vote', 'election'],
            'entertainment': ['movie', 'music', 'show', 'game', 'celebrity'],
            'business': ['business', 'company', 'money', 'profit', 'market'],
            'lifestyle': ['life', 'health', 'food', 'travel', 'fashion']
        }
        
        for topic, keywords in topics.items():
            topic_score = 0.0
            topic_word_count = 0
            
            for word in text.split():
                if word in keywords:
                    # Simple scoring based on surrounding words
                    if word in self.positive_words:
                        topic_score += 1.0
                    elif word in self.negative_words:
                        topic_score -= 1.0
                    topic_word_count += 1
            
            if topic_word_count > 0:
                topic_sentiment[topic] = topic_score / topic_word_count
            else:
                topic_sentiment[topic] = 0.0
        
        return topic_sentiment
    
    def _get_intensity_multiplier(self, word: str, position: int, words: List[str]) -> float:
        """Get intensity multiplier for sentiment word based on context."""
        multiplier = 1.0
        
        # Check for intensity modifiers nearby
        context_start = max(0, position - 2)
        context_end = min(len(words), position + 3)
        context = words[context_start:context_end]
        
        for context_word in context:
            if context_word in self.intensity_words:
                if context_word in ['very', 'extremely', 'incredibly', 'absolutely']:
                    multiplier *= self.config['intensity_modifier_multiplier']
                elif context_word in ['slightly', 'somewhat', 'a_bit']:
                    multiplier *= 0.7
                elif context_word in ['not', 'never', 'no']:
                    multiplier *= -1.0  # Handle negation
        
        return multiplier
    
    def _load_positive_words(self) -> set:
        """Load positive sentiment words."""
        return {
            'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 'wonderful',
            'love', 'like', 'enjoy', 'beautiful', 'nice', 'perfect', 'brilliant', 'outstanding',
            'happy', 'pleased', 'satisfied', 'impressed', 'thankful', 'grateful', 'appreciate',
            'best', 'superb', 'incredible', 'marvelous', 'terrific', 'fabulous', 'spectacular',
            'positive', 'optimistic', 'encouraging', 'inspiring', 'uplifting', 'motivating',
            'success', 'successful', 'winning', 'victory', 'triumph', 'achievement', 'progress',
            'quality', 'valuable', 'worthwhile', 'beneficial', 'advantageous', 'helpful',
            'creative', 'innovative', 'original', 'fresh', 'unique', 'special', 'exceptional'
        }
    
    def _load_negative_words(self) -> set:
        """Load negative sentiment words."""
        return {
            'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate', 'dislike', 'ugly',
            'worst', 'pathetic', 'useless', 'worthless', 'disappointing', 'frustrating',
            'angry', 'mad', 'furious', 'annoyed', 'irritated', 'upset', 'disappointed',
            'boring', 'stupid', 'dumb', 'foolish', 'ridiculous', 'absurd', 'nonsense',
            'fail', 'failure', 'failed', 'disaster', 'problem', 'issue', 'trouble', 'difficulty',
            'slow', 'late', 'broken', 'damaged', 'defective', 'poor', 'inferior', 'lacking',
            'negative', 'pessimistic', 'critical', 'critical', 'complaint', 'problematic',
            'stress', 'pressure', 'overwhelming', 'impossible', 'hopeless', 'pointless'
        }
    
    def _load_intensity_words(self) -> List[str]:
        """Load intensity-modifying words."""
        return [
            'very', 'extremely', 'incredibly', 'absolutely', 'completely', 'totally',
            'really', 'truly', 'highly', 'deeply', 'strongly', 'significantly',
            'slightly', 'somewhat', 'a_bit', 'a_little', 'mildly', 'fairly',
            'not', 'never', 'no', 'none', 'nothing', 'neither', 'nor',
            'hardly', 'barely', 'scarcely', 'rarely', 'seldom'
        ]
    
    def _load_emotion_indicators(self) -> Dict[str, List[str]]:
        """Load emotion-indicating words."""
        return {
            'joy': [
                'happy', 'joyful', 'cheerful', 'delighted', 'elated', 'euphoric', 'ecstatic',
                'smile', 'laugh', 'funny', 'hilarious', 'amusing', 'entertaining',
                'celebrate', 'party', 'wonderful', 'fantastic', 'amazing', 'awesome'
            ],
            'anger': [
                'angry', 'mad', 'furious', 'rage', 'wrath', 'irritated', 'annoyed', 'frustrated',
                'hate', 'detest', 'despise', 'outraged', 'pissed', 'pissed_off',
                'resentful', 'bitter', 'hostile', 'aggressive', 'violent', 'brutal'
            ],
            'fear': [
                'afraid', 'scared', 'terrified', 'frightened', 'petrified', 'panic', 'panicked',
                'worry', 'anxious', 'nervous', 'stress', 'stressed', 'overwhelmed',
                'danger', 'dangerous', 'threat', 'threatened', 'risk', 'risky', 'unsafe'
            ],
            'sadness': [
                'sad', 'depressed', 'miserable', 'unhappy', 'melancholy', 'gloomy', 'dejected',
                'cry', 'tears', 'weep', 'sob', 'heartbroken', 'devastated', 'destroyed',
                'lonely', 'isolated', 'alone', 'grief', 'sorrow', 'regret', 'sorry'
            ],
            'surprise': [
                'surprised', 'amazed', 'astonished', 'shocked', 'stunned', 'bewildered',
                'unexpected', 'sudden', 'suddenly', 'wow', 'omg', 'incredible', 'unbelievable',
                'speechless', 'mind_blown', 'mind-blown', 'speechless'
            ],
            'disgust': [
                'disgusted', 'revolted', 'sickened', 'nauseated', 'repulsed',
                'gross', 'nasty', 'disgusting', 'awful', 'terrible', 'horrible',
                'filthy', 'dirty', 'contaminated', 'polluted', 'toxic'
            ]
        }