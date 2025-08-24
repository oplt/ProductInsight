from TikTokApi import TikTokApi
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import os
import asyncio


class TikTokAnalyzer:
    """TikTok content analysis service"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or os.environ.get('TIKTOK_SESSION_ID')
        self.api = None
    
    async def initialize(self):
        """Initialize TikTok API"""
        try:
            self.api = TikTokApi()
            await self.api.create_sessions(
                ms_tokens=[self.session_id] if self.session_id else None,
                num_sessions=1,
                sleep_after=3
            )
            return True
        except Exception as e:
            print(f"TikTok API initialization failed: {str(e)}")
            return False
    
    async def get_user_videos(self, username: str, count: int = 20) -> List[Dict]:
        """Get recent videos for a user"""
        if not self.api:
            if not await self.initialize():
                return []
        
        try:
            user = self.api.user(username)
            videos = []
            
            async for video in user.videos(count=count):
                video_data = {
                    'id': video.id,
                    'description': getattr(video, 'desc', '') or '',
                    'created_at': datetime.fromtimestamp(getattr(video, 'createTime', 0)).isoformat(),
                    'views': getattr(video.stats, 'playCount', 0) or 0,
                    'likes': getattr(video.stats, 'diggCount', 0) or 0,
                    'comments': getattr(video.stats, 'commentCount', 0) or 0,
                    'shares': getattr(video.stats, 'shareCount', 0) or 0,
                    'username': username,
                    'duration': getattr(video, 'duration', 0) or 0,
                    'url': f"https://www.tiktok.com/@{username}/video/{video.id}"
                }
                videos.append(video_data)
            
            return videos
            
        except Exception as e:
            print(f"Error fetching TikTok videos: {str(e)}")
            return []
    
    async def get_hashtag_videos(self, hashtag: str, count: int = 20) -> List[Dict]:
        """Get recent videos for a hashtag"""
        if not self.api:
            if not await self.initialize():
                return []
        
        try:
            hashtag_obj = self.api.hashtag(name=hashtag)
            videos = []
            
            async for video in hashtag_obj.videos(count=count):
                video_data = {
                    'id': video.id,
                    'description': getattr(video, 'desc', '') or '',
                    'created_at': datetime.fromtimestamp(getattr(video, 'createTime', 0)).isoformat(),
                    'views': getattr(video.stats, 'playCount', 0) or 0,
                    'likes': getattr(video.stats, 'diggCount', 0) or 0,
                    'comments': getattr(video.stats, 'commentCount', 0) or 0,
                    'shares': getattr(video.stats, 'shareCount', 0) or 0,
                    'username': getattr(video.author, 'uniqueId', '') or '',
                    'duration': getattr(video, 'duration', 0) or 0,
                    'hashtag': hashtag,
                    'url': f"https://www.tiktok.com/@{getattr(video.author, 'uniqueId', '')}/video/{video.id}"
                }
                videos.append(video_data)
            
            return videos
            
        except Exception as e:
            print(f"Error fetching TikTok hashtag videos: {str(e)}")
            return []
    
    async def get_video_comments(self, video_id: str, count: int = 50) -> List[Dict]:
        """Get comments for a specific video"""
        if not self.api:
            if not await self.initialize():
                return []
        
        try:
            video = self.api.video(id=video_id)
            comments = []
            
            async for comment in video.comments(count=count):
                comment_data = {
                    'id': getattr(comment, 'cid', ''),
                    'text': getattr(comment, 'text', '') or '',
                    'username': getattr(comment.user, 'uniqueId', '') or '',
                    'created_at': datetime.fromtimestamp(getattr(comment, 'createTime', 0)).isoformat(),
                    'likes': getattr(comment, 'diggCount', 0) or 0,
                    'reply_count': getattr(comment, 'replyCommentTotal', 0) or 0
                }
                comments.append(comment_data)
            
            return comments
            
        except Exception as e:
            print(f"Error fetching TikTok comments: {str(e)}")
            return []
    
    async def search_videos(self, keyword: str, count: int = 20) -> List[Dict]:
        """Search for videos by keyword"""
        if not self.api:
            if not await self.initialize():
                return []
        
        try:
            videos = []
            
            async for video in self.api.search.videos(keyword, count=count):
                video_data = {
                    'id': video.id,
                    'description': getattr(video, 'desc', '') or '',
                    'created_at': datetime.fromtimestamp(getattr(video, 'createTime', 0)).isoformat(),
                    'views': getattr(video.stats, 'playCount', 0) or 0,
                    'likes': getattr(video.stats, 'diggCount', 0) or 0,
                    'comments': getattr(video.stats, 'commentCount', 0) or 0,
                    'shares': getattr(video.stats, 'shareCount', 0) or 0,
                    'username': getattr(video.author, 'uniqueId', '') or '',
                    'duration': getattr(video, 'duration', 0) or 0,
                    'keyword': keyword,
                    'url': f"https://www.tiktok.com/@{getattr(video.author, 'uniqueId', '')}/video/{video.id}"
                }
                videos.append(video_data)
            
            return videos
            
        except Exception as e:
            print(f"Error searching TikTok videos: {str(e)}")
            return []
    
    async def analyze_user_engagement(self, username: str, video_count: int = 20) -> Dict:
        """Analyze engagement metrics for a user"""
        videos = await self.get_user_videos(username, video_count)
        
        if not videos:
            return {}
        
        total_views = sum(video['views'] for video in videos)
        total_likes = sum(video['likes'] for video in videos)
        total_comments = sum(video['comments'] for video in videos)
        total_shares = sum(video['shares'] for video in videos)
        total_videos = len(videos)
        
        avg_views = total_views / total_videos if total_videos > 0 else 0
        avg_likes = total_likes / total_videos if total_videos > 0 else 0
        avg_comments = total_comments / total_videos if total_videos > 0 else 0
        avg_shares = total_shares / total_videos if total_videos > 0 else 0
        
        engagement_rate = (total_likes + total_comments + total_shares) / total_views if total_views > 0 else 0
        
        return {
            'username': username,
            'total_videos_analyzed': total_videos,
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'average_views_per_video': avg_views,
            'average_likes_per_video': avg_likes,
            'average_comments_per_video': avg_comments,
            'average_shares_per_video': avg_shares,
            'engagement_rate': engagement_rate,
            'videos': videos
        }


# Synchronous wrapper functions for easier integration
class TikTokAnalyzerSync:
    """Synchronous wrapper for TikTok analyzer"""
    
    def __init__(self, session_id: str = None):
        self.analyzer = TikTokAnalyzer(session_id)
    
    def get_user_videos(self, username: str, count: int = 20) -> List[Dict]:
        """Get recent videos for a user (sync)"""
        return asyncio.run(self.analyzer.get_user_videos(username, count))
    
    def get_hashtag_videos(self, hashtag: str, count: int = 20) -> List[Dict]:
        """Get recent videos for a hashtag (sync)"""
        return asyncio.run(self.analyzer.get_hashtag_videos(hashtag, count))
    
    def get_video_comments(self, video_id: str, count: int = 50) -> List[Dict]:
        """Get comments for a specific video (sync)"""
        return asyncio.run(self.analyzer.get_video_comments(video_id, count))
    
    def search_videos(self, keyword: str, count: int = 20) -> List[Dict]:
        """Search for videos by keyword (sync)"""
        return asyncio.run(self.analyzer.search_videos(keyword, count))
    
    def analyze_user_engagement(self, username: str, video_count: int = 20) -> Dict:
        """Analyze engagement metrics for a user (sync)"""
        return asyncio.run(self.analyzer.analyze_user_engagement(username, video_count))
