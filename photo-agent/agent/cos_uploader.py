"""
COS 临时 URL 上传模块

使用后端下发的临时上传 URL 直传腾讯云 COS。
"""

import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


class CosUploader:
    """COS 上传器"""
    
    def __init__(self, timeout: float = 60.0):
        """
        初始化 COS 上传器
        
        Args:
            timeout: 上传超时时间（秒）
        """
        self.timeout = timeout
        self._client: httpx.AsyncClient = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
            )
        return self._client
    
    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def upload(
        self,
        upload_url: str,
        file_path: str,
        content_type: str = "image/webp"
    ) -> bool:
        """
        上传文件到 COS
        
        Args:
            upload_url: COS 临时上传 URL
            file_path: 本地文件路径
            content_type: 内容类型
        
        Returns:
            是否上传成功
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"文件不存在: {file_path}")
            return False
        
        try:
            client = await self._get_client()
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 上传到 COS
            response = await client.put(
                upload_url,
                content=file_content,
                headers={
                    "Content-Type": content_type,
                    "Content-Length": str(len(file_content)),
                },
            )
            
            # 检查响应
            if response.status_code in (200, 204):
                logger.debug(f"上传成功: {file_path}")
                return True
            else:
                logger.error(
                    f"上传失败: {file_path} - "
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
        
        except httpx.TimeoutException as e:
            logger.error(f"上传超时: {file_path} - {e}")
            return False
        
        except httpx.NetworkError as e:
            logger.error(f"上传网络错误: {file_path} - {e}")
            return False
        
        except Exception as e:
            logger.error(f"上传异常: {file_path} - {e}")
            return False
    
    async def upload_with_retry(
        self,
        upload_url: str,
        file_path: str,
        content_type: str = "image/webp",
        max_retries: int = 3
    ) -> bool:
        """
        带重试的上传
        
        Args:
            upload_url: COS 临时上传 URL
            file_path: 本地文件路径
            content_type: 内容类型
            max_retries: 最大重试次数
        
        Returns:
            是否上传成功
        """
        import asyncio
        
        for attempt in range(max_retries):
            success = await self.upload(upload_url, file_path, content_type)
            
            if success:
                return True
            
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 30)
                logger.info(f"上传重试 ({attempt + 1}/{max_retries})，等待 {wait_time} 秒...")
                await asyncio.sleep(wait_time)
        
        return False
