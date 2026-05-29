"""
后端 API 通信模块

实现与云端后端的 API 通信，包括：
- 心跳上报
- 批量上传照片索引
- 申请 COS 上传地址
- 通知上传完成
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ApiResponse:
    """API 响应"""
    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None
    status_code: int = 0


class ApiClient:
    """后端 API 客户端"""
    
    def __init__(self, server_url: str, agent_token: str, agent_id: str):
        """
        初始化 API 客户端
        
        Args:
            server_url: 后端服务器地址
            agent_token: Agent 认证 token
            agent_id: Agent ID
        """
        self.server_url = server_url.rstrip('/')
        self.agent_id = agent_id
        self.headers = {
            "Authorization": f"Bearer {agent_token}",
            "Content-Type": "application/json",
        }
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=5),
            )
        return self._client
    
    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[dict] = None,
        max_retries: int = 3
    ) -> ApiResponse:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            path: API 路径
            json_data: 请求体
            max_retries: 最大重试次数
        
        Returns:
            ApiResponse 对象
        """
        url = f"{self.server_url}{path}"
        client = await self._get_client()
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await client.request(
                    method,
                    url,
                    json=json_data,
                    headers=self.headers,
                )
                
                # 处理 429 限流
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"API 限流，等待 {retry_after} 秒后重试")
                    await asyncio.sleep(retry_after)
                    continue
                
                # 处理成功响应
                if response.status_code < 400:
                    try:
                        data = response.json()
                        return ApiResponse(
                            success=data.get("success", True),
                            data=data.get("data"),
                            status_code=response.status_code,
                        )
                    except Exception:
                        return ApiResponse(
                            success=True,
                            status_code=response.status_code,
                        )
                
                # 处理错误响应
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "未知错误")
                except Exception:
                    error_msg = f"HTTP {response.status_code}"
                
                logger.error(f"API 请求失败: {method} {path} - {error_msg}")
                
                return ApiResponse(
                    success=False,
                    error={"message": error_msg},
                    status_code=response.status_code,
                )
            
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"API 请求超时 (尝试 {attempt + 1}/{max_retries}): {e}")
            
            except httpx.NetworkError as e:
                last_error = e
                logger.warning(f"API 网络错误 (尝试 {attempt + 1}/{max_retries}): {e}")
            
            except Exception as e:
                last_error = e
                logger.error(f"API 请求异常 (尝试 {attempt + 1}/{max_retries}): {e}")
            
            # 指数退避
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 30)
                logger.info(f"等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)
        
        # 所有重试都失败
        error_msg = f"API 请求失败: {method} {path}"
        if last_error:
            error_msg += f" - {last_error}"
        
        logger.error(error_msg)
        return ApiResponse(
            success=False,
            error={"message": error_msg},
            status_code=0,
        )
    
    async def heartbeat(self, stats: dict) -> bool:
        """
        上报心跳
        
        Args:
            stats: 心跳统计数据
        
        Returns:
            是否成功
        """
        data = {
            "agentId": self.agent_id,
            **stats,
        }
        
        response = await self._request("POST", "/api/agent/heartbeat", data)
        
        if not response.success:
            logger.error(f"心跳上报失败: {response.error}")
            return False
        
        logger.debug("心跳上报成功")
        return True
    
    async def batch_upload_photos(self, photos: list[dict]) -> Optional[dict]:
        """
        批量上传照片索引
        
        Args:
            photos: 照片信息列表
        
        Returns:
            响应数据，包含 results 列表
        """
        data = {
            "agentId": self.agent_id,
            "photos": photos,
        }
        
        response = await self._request("POST", "/api/agent/photos/batch", data)
        
        if not response.success:
            logger.error(f"批量上传照片索引失败: {response.error}")
            return None
        
        return response.data
    
    async def get_upload_ticket(
        self,
        photo_id: str,
        asset_type: str,
        content_type: str,
        file_size: int,
        width: int,
        height: int
    ) -> Optional[dict]:
        """
        申请 COS 上传地址
        
        Args:
            photo_id: 后端返回的照片 ID
            asset_type: 资源类型（thumb/preview）
            content_type: 内容类型
            file_size: 文件大小
            width: 图片宽度
            height: 图片高度
        
        Returns:
            上传地址信息
        """
        data = {
            "agentId": self.agent_id,
            "photoId": photo_id,
            "assetType": asset_type,
            "contentType": content_type,
            "fileSize": file_size,
            "width": width,
            "height": height,
        }
        
        response = await self._request("POST", "/api/agent/assets/upload-ticket", data)
        
        if not response.success:
            logger.error(f"申请上传地址失败: {response.error}")
            return None
        
        return response.data
    
    async def notify_upload_complete(
        self,
        photo_id: str,
        asset_type: str,
        storage_key: str,
        file_size: int,
        width: int,
        height: int
    ) -> bool:
        """
        通知上传完成
        
        Args:
            photo_id: 后端返回的照片 ID
            asset_type: 资源类型（thumb/preview）
            storage_key: COS 存储键
            file_size: 文件大小
            width: 图片宽度
            height: 图片高度
        
        Returns:
            是否成功
        """
        data = {
            "agentId": self.agent_id,
            "photoId": photo_id,
            "assetType": asset_type,
            "storageProvider": "cos",
            "storageKey": storage_key,
            "fileSize": file_size,
            "width": width,
            "height": height,
        }
        
        response = await self._request("POST", "/api/agent/assets/upload-complete", data)
        
        if not response.success:
            logger.error(f"通知上传完成失败: {response.error}")
            return False
        
        logger.debug(f"通知上传完成成功: {photo_id} {asset_type}")
        return True
