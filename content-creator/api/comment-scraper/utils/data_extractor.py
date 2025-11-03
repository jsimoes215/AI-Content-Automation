"""
Data Extraction and Processing Utilities.

This module provides utilities for extracting, filtering, and processing
comment data from various sources and formats.
"""

import json
import csv
import asyncio
from typing import List, Dict, Any, Optional, Union, AsyncIterator
from datetime import datetime, timedelta
from pathlib import Path
import logging

from ..models.comment_models import CommentBase, CommentWithAnalysis, Platform, ScrapingJob, ScrapingStats
from ..scraper_factory import scraping_manager
from ..utils.comment_analyzer import comment_analyzer

logger = logging.getLogger(__name__)


class DataExtractor:
    """Handles data extraction, filtering, and export operations."""
    
    def __init__(self):
        """Initialize the data extractor."""
        self.export_formats = ['json', 'csv', 'xlsx', 'parquet']
    
    async def extract_comments(
        self,
        platform: Platform,
        content_id: str,
        content_type: str = "video",
        max_comments: int = 1000,
        include_analysis: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        output_format: str = "json",
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract and process comments from specified content.
        
        Args:
            platform: Platform to extract from
            content_id: Content ID to extract from
            content_type: Type of content
            max_comments: Maximum comments to extract
            include_analysis: Whether to include sentiment analysis
            filters: Optional filters to apply
            output_format: Output format (json, csv, xlsx, parquet)
            output_file: Optional output file path
            
        Returns:
            Dictionary with extraction results and metadata
        """
        logger.info(f"Starting data extraction for {platform}:{content_id}")
        
        # Prepare filters
        filters = filters or {}
        date_filter = self._parse_date_filter(filters.get('date_range'))
        sentiment_filter = filters.get('sentiment')
        min_likes = filters.get('min_likes', 0)
        language_filter = filters.get('language')
        
        # Extract comments
        comments = []
        async for comment in scraping_manager.scrape_comments(
            platform=platform,
            content_id=content_id,
            max_comments=max_comments,
            start_date=date_filter.get('start') if date_filter else None,
            end_date=date_filter.get('end') if date_filter else None,
            language_filter=language_filter
        ):
            # Apply filters
            if self._apply_filters(comment, filters):
                # Analyze if requested
                if include_analysis:
                    comment = await comment_analyzer.analyze_comment(comment)
                
                comments.append(comment)
        
        # Apply final filters
        comments = self._apply_post_extraction_filters(comments, filters)
        
        # Generate metadata
        metadata = self._generate_metadata(comments, platform, content_id, filters)
        
        # Export data if requested
        export_result = None
        if output_format != "none":
            export_result = await self.export_data(
                comments=comments,
                format=output_format,
                file_path=output_file,
                metadata=metadata
            )
        
        return {
            'comments': comments,
            'metadata': metadata,
            'export': export_result,
            'total_extracted': len(comments),
            'filters_applied': filters
        }
    
    def _parse_date_filter(self, date_range: Optional[str]) -> Optional[Dict[str, datetime]]:
        """Parse date range filter string."""
        if not date_range:
            return None
        
        try:
            # Expected format: "YYYY-MM-DD:YYYY-MM-DD" or "7d", "30d"
            if date_range.endswith('d'):
                days = int(date_range[:-1])
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                return {'start': start_date, 'end': end_date}
            
            elif ':' in date_range:
                start_str, end_str = date_range.split(':')
                return {
                    'start': datetime.fromisoformat(start_str),
                    'end': datetime.fromisoformat(end_str)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date filter {date_range}: {e}")
            return None
    
    def _apply_filters(self, comment: CommentBase, filters: Dict[str, Any]) -> bool:
        """Apply pre-extraction filters to comment."""
        try:
            # Min likes filter
            min_likes = filters.get('min_likes', 0)
            if comment.like_count < min_likes:
                return False
            
            # Language filter
            language_filter = filters.get('language')
            if language_filter and comment.language != language_filter:
                return False
            
            # Spam filter
            if filters.get('exclude_spam', False) and comment.is_spam:
                return False
            
            # Deleted comments filter
            if filters.get('exclude_deleted', True) and comment.is_deleted:
                return False
            
            # Username filter
            username_filter = filters.get('username_pattern')
            if username_filter:
                import re
                if not re.search(username_filter, comment.username or ''):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return True  # Fail open - don't exclude on filter errors
    
    def _apply_post_extraction_filters(
        self, 
        comments: List[CommentWithAnalysis], 
        filters: Dict[str, Any]
    ) -> List[CommentWithAnalysis]:
        """Apply filters that require analysis results."""
        try:
            filtered_comments = comments.copy()
            
            # Sentiment filter (requires analysis)
            sentiment_filter = filters.get('sentiment')
            if sentiment_filter:
                filtered_comments = [
                    c for c in filtered_comments 
                    if c.sentiment_label and c.sentiment_label.value == sentiment_filter
                ]
            
            # Quality filter
            min_quality = filters.get('min_quality_score')
            if min_quality:
                filtered_comments = [
                    c for c in filtered_comments 
                    if (c.quality_score or 0) >= min_quality
                ]
            
            # Engagement potential filter
            min_engagement = filters.get('min_engagement_potential')
            if min_engagement:
                filtered_comments = [
                    c for c in filtered_comments 
                    if (c.engagement_potential or 0) >= min_engagement
                ]
            
            # Topic filter
            topic_filter = filters.get('topics')
            if topic_filter:
                if isinstance(topic_filter, str):
                    topic_filter = [topic_filter]
                
                filtered_comments = [
                    c for c in filtered_comments 
                    if any(topic in c.topics for topic in topic_filter)
                ]
            
            return filtered_comments
            
        except Exception as e:
            logger.error(f"Error applying post-extraction filters: {e}")
            return comments
    
    def _generate_metadata(
        self, 
        comments: List[CommentWithAnalysis], 
        platform: Platform, 
        content_id: str, 
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate metadata for extracted comments."""
        try:
            if not comments:
                return {
                    'platform': platform.value,
                    'content_id': content_id,
                    'extracted_at': datetime.utcnow().isoformat(),
                    'total_comments': 0,
                    'filters': filters
                }
            
            # Basic statistics
            dates = [c.created_at for c in comments if c.created_at]
            languages = [c.language for c in comments if c.language]
            like_counts = [c.like_count for c in comments if c.like_count]
            
            # Sentiment distribution
            sentiments = [c.sentiment_label for c in comments if c.sentiment_label]
            sentiment_distribution = {}
            from collections import Counter
            for sentiment in sentiments:
                sentiment_distribution[sentiment.value] = sentiment_distribution.get(sentiment.value, 0) + 1
            
            # Top topics
            all_topics = []
            for comment in comments:
                all_topics.extend(comment.topics)
            topic_counts = Counter(all_topics)
            
            return {
                'platform': platform.value,
                'content_id': content_id,
                'extracted_at': datetime.utcnow().isoformat(),
                'total_comments': len(comments),
                'date_range': {
                    'earliest': min(dates).isoformat() if dates else None,
                    'latest': max(dates).isoformat() if dates else None
                },
                'languages': list(set(languages)),
                'language_distribution': dict(Counter(languages)),
                'like_statistics': {
                    'total': sum(like_counts),
                    'average': sum(like_counts) / len(like_counts) if like_counts else 0,
                    'max': max(like_counts) if like_counts else 0,
                    'min': min(like_counts) if like_counts else 0
                },
                'sentiment_distribution': sentiment_distribution,
                'top_topics': dict(topic_counts.most_common(10)),
                'filters_applied': filters,
                'analysis_included': any(hasattr(c, 'sentiment_score') for c in comments)
            }
            
        except Exception as e:
            logger.error(f"Error generating metadata: {e}")
            return {
                'platform': platform.value,
                'content_id': content_id,
                'extracted_at': datetime.utcnow().isoformat(),
                'total_comments': len(comments),
                'filters': filters,
                'error': str(e)
            }
    
    async def export_data(
        self,
        comments: List[CommentWithAnalysis],
        format: str = "json",
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export comments to specified format.
        
        Args:
            comments: Comments to export
            format: Export format
            file_path: Output file path
            metadata: Metadata to include
            
        Returns:
            Dictionary with export results
        """
        try:
            if format not in self.export_formats:
                raise ValueError(f"Unsupported format: {format}. Supported: {self.export_formats}")
            
            if not file_path:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                file_path = f"comments_export_{timestamp}.{format}"
            
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                'comments': [comment.dict() for comment in comments],
                'metadata': metadata or {}
            }
            
            if format == 'json':
                await self._export_json(export_data, file_path)
            
            elif format == 'csv':
                await self._export_csv(comments, file_path)
            
            elif format == 'xlsx':
                await self._export_xlsx(export_data, file_path)
            
            elif format == 'parquet':
                await self._export_parquet(export_data, file_path)
            
            return {
                'success': True,
                'file_path': file_path,
                'format': format,
                'records_exported': len(comments),
                'file_size_bytes': Path(file_path).stat().st_size if Path(file_path).exists() else 0
            }
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'format': format
            }
    
    async def _export_json(self, data: Dict[str, Any], file_path: str) -> None:
        """Export to JSON format."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    async def _export_csv(self, comments: List[CommentWithAnalysis], file_path: str) -> None:
        """Export to CSV format."""
        if not comments:
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            # Get all possible fields from first comment
            fieldnames = list(comments[0].dict().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for comment in comments:
                row = comment.dict()
                # Convert non-serializable fields
                for key, value in row.items():
                    if hasattr(value, 'isoformat'):  # datetime objects
                        row[key] = value.isoformat()
                    elif isinstance(value, (list, dict)):
                        row[key] = json.dumps(value)
                writer.writerow(row)
    
    async def _export_xlsx(self, data: Dict[str, Any], file_path: str) -> None:
        """Export to Excel format."""
        try:
            import pandas as pd
            
            # Convert comments to DataFrame
            comments_data = [comment.dict() for comment in data['comments']]
            df_comments = pd.DataFrame(comments_data)
            
            # Convert metadata to DataFrame
            df_metadata = pd.DataFrame([data['metadata']])
            
            # Write to Excel with multiple sheets
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df_comments.to_excel(writer, sheet_name='Comments', index=False)
                df_metadata.to_excel(writer, sheet_name='Metadata', index=False)
                
        except ImportError:
            logger.warning("pandas or openpyxl not available, falling back to CSV")
            csv_file = file_path.replace('.xlsx', '.csv')
            await self._export_csv(data['comments'], csv_file)
    
    async def _export_parquet(self, data: Dict[str, Any], file_path: str) -> None:
        """Export to Parquet format."""
        try:
            import pandas as pd
            
            # Convert to DataFrame
            df = pd.DataFrame(data['comments'])
            
            # Add metadata as attributes
            df.attrs['metadata'] = data['metadata']
            
            # Export to Parquet
            df.to_parquet(file_path, index=False)
            
        except ImportError:
            logger.warning("pandas or pyarrow not available, falling back to JSON")
            json_file = file_path.replace('.parquet', '.json')
            await self._export_json(data, json_file)
    
    async def batch_extract(
        self,
        extraction_requests: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Batch extract data from multiple sources.
        
        Args:
            extraction_requests: List of extraction request dictionaries
            max_concurrent: Maximum concurrent extractions
            
        Returns:
            List of extraction results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_with_semaphore(request):
            async with semaphore:
                return await self.extract_comments(**request)
        
        tasks = [extract_with_semaphore(req) for req in extraction_requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch extraction {i} failed: {result}")
                successful_results.append({
                    'success': False,
                    'error': str(result),
                    'request': extraction_requests[i]
                })
            else:
                successful_results.append(result)
        
        return successful_results
    
    async def extract_trending_topics(
        self,
        platforms: List[Platform],
        content_ids: List[str],
        time_range: str = "7d",
        min_mentions: int = 3
    ) -> Dict[str, Any]:
        """
        Extract trending topics across multiple content pieces.
        
        Args:
            platforms: Platforms to analyze
            content_ids: Content IDs to analyze
            time_range: Time range for analysis
            min_mentions: Minimum mentions for a topic to be considered
            
        Returns:
            Dictionary with trending topics analysis
        """
        all_comments = []
        
        # Extract comments from all sources
        for platform in platforms:
            for content_id in content_ids:
                try:
                    extraction_result = await self.extract_comments(
                        platform=platform,
                        content_id=content_id,
                        max_comments=500,  # Reasonable limit for trending analysis
                        include_analysis=True,
                        filters={'date_range': time_range}
                    )
                    all_comments.extend(extraction_result['comments'])
                    
                except Exception as e:
                    logger.error(f"Error extracting from {platform}:{content_id} - {e}")
        
        # Analyze trending topics
        if not all_comments:
            return {'trending_topics': [], 'analysis_summary': {'total_comments': 0}}
        
        # Count topic mentions
        topic_mentions = {}
        for comment in all_comments:
            for topic in comment.topics:
                topic_mentions[topic] = topic_mentions.get(topic, 0) + 1
        
        # Filter by minimum mentions
        trending_topics = [
            {'topic': topic, 'mentions': count, 'percentage': count / len(all_comments) * 100}
            for topic, count in topic_mentions.items()
            if count >= min_mentions
        ]
        
        # Sort by mentions
        trending_topics.sort(key=lambda x: x['mentions'], reverse=True)
        
        return {
            'trending_topics': trending_topics[:20],  # Top 20
            'analysis_summary': {
                'total_comments_analyzed': len(all_comments),
                'platforms_analyzed': [p.value for p in platforms],
                'content_pieces_analyzed': len(content_ids),
                'time_range': time_range,
                'min_mentions_threshold': min_mentions
            },
            'sentiment_trends': await self._analyze_sentiment_trends(all_comments)
        }
    
    async def _analyze_sentiment_trends(self, comments: List[CommentWithAnalysis]) -> Dict[str, Any]:
        """Analyze sentiment trends over time."""
        try:
            from collections import defaultdict
            
            # Group comments by day
            daily_sentiment = defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0})
            
            for comment in comments:
                if comment.created_at and comment.sentiment_label:
                    date_key = comment.created_at.date().isoformat()
                    daily_sentiment[date_key][comment.sentiment_label.value] += 1
            
            return dict(daily_sentiment)
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment trends: {e}")
            return {}


# Global data extractor instance
data_extractor = DataExtractor()