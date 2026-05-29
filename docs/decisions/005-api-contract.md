# 005. 后端接口协议草案

## 状态

草案。

## 背景

本文件用于串联前端 H5、云端后端、Photo-Agent、腾讯地图、腾讯 COS 和 AI 写作服务。

接口风格先按 REST JSON 设计。

文件上传不经过云服务器转发图片内容，Photo-Agent 使用后端生成的 COS 临时上传 URL 直传 COS。

## 通用约定

基础路径：

```text
/api
```

请求格式：

```text
Content-Type: application/json
```

成功响应：

```json
{
  "success": true,
  "data": {}
}
```

失败响应：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "给用户或开发者看的错误说明"
  }
}
```

时间格式：

```text
ISO-8601
2026-05-29T12:12:46+08:00
```

鉴权：

- H5 使用访问码登录后获得 access token。
- Photo-Agent 使用 agent token。
- COS SecretId / SecretKey 只保存在云端后端。

## 1. 登录接口

### 1.1 访问码登录

```text
POST /api/auth/access-code/login
```

请求：

```json
{
  "accessCode": "123456"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "accessToken": "token",
    "expiresAt": "2026-05-29T14:00:00+08:00",
    "maxExpiresAt": "2026-06-05T12:00:00+08:00"
  }
}
```

说明：

- token 基础有效期 2 小时。
- 用户活跃时自动续期。
- 最长保持 7 天。

### 1.2 续期

```text
POST /api/auth/refresh
```

响应：

```json
{
  "success": true,
  "data": {
    "accessToken": "new-token",
    "expiresAt": "2026-05-29T15:00:00+08:00"
  }
}
```

## 2. 首页 / 路线接口

### 2.1 路线列表

```text
GET /api/routes
```

查询参数：

```text
keyword 可选，搜索路线、城市、地点
```

响应：

```json
{
  "success": true,
  "data": {
    "routes": [
      {
        "id": "r001",
        "name": "2025 西藏新疆大环线",
        "year": 2025,
        "summary": "河南出发 · 西藏 · 新疆 · 内蒙古 · 回到河南",
        "cityCount": 12,
        "placeCount": 36,
        "photoCount": 428,
        "coverThumbUrl": "短期签名URL",
        "latestDraft": {
          "targetType": "place",
          "targetId": "p001",
          "title": "珠峰北坡",
          "updatedAt": "2026-05-29T12:00:00+08:00"
        }
      }
    ]
  }
}
```

### 2.2 新建路线

```text
POST /api/routes
```

请求：

```json
{
  "name": "2025 西藏新疆大环线",
  "year": 2025
}
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "r001"
  }
}
```

### 2.3 路线详情

```text
GET /api/routes/{routeId}
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "r001",
    "name": "2025 西藏新疆大环线",
    "year": 2025,
    "cityCount": 12,
    "placeCount": 36,
    "photoCount": 428,
    "provinceGroups": [
      {
        "provinceName": "西藏自治区",
        "cities": [
          {
            "id": "rc001",
            "cityName": "日喀则市",
            "photoCount": 41,
            "placeCount": 2,
            "places": [
              {
                "id": "rp001",
                "name": "珠峰北坡",
                "photoCount": 23,
                "matchStatus": "matched",
                "hasDraft": true
              }
            ]
          }
        ]
      }
    ]
  }
}
```

## 3. 行政区划接口

### 3.1 省份列表

```text
GET /api/districts/provinces
```

响应：

```json
{
  "success": true,
  "data": {
    "provinces": [
      {
        "adcode": "540000",
        "name": "西藏自治区"
      }
    ]
  }
}
```

### 3.2 城市/地区列表

```text
GET /api/districts/provinces/{provinceAdcode}/cities
```

响应：

```json
{
  "success": true,
  "data": {
    "cities": [
      {
        "adcode": "540200",
        "name": "日喀则市"
      }
    ]
  }
}
```

## 4. 路线城市接口

### 4.1 添加城市

```text
POST /api/routes/{routeId}/cities
```

请求：

```json
{
  "cityAdcode": "540200"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "routeCityId": "rc001"
  }
}
```

## 5. 地点接口

### 5.1 添加地点并自动匹配照片

```text
POST /api/route-cities/{routeCityId}/places
```

请求：

```json
{
  "name": "珠峰北坡"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "routePlaceId": "rp001",
    "name": "珠峰北坡",
    "resolvedTitle": "珠峰北坡大本营深度探索路线",
    "matchStatus": "matched",
    "photoCount": 23,
    "previewPhotos": [
      {
        "photoId": "ph001",
        "thumbUrl": "短期签名URL"
      }
    ]
  }
}
```

`matchStatus`：

```text
matched
unmatched
pending
```

说明：

- 后端带城市上下文调用腾讯地图地点提示/搜索。
- 后端根据 POI 坐标匹配照片 GPS。
- 如果没有可靠匹配，也允许保存地点。

### 5.2 重新查找地点照片

```text
POST /api/route-places/{routePlaceId}/rematch
```

用途：

- 地点已保存，但照片后续才同步上来。
- 或用户希望重新查找。

响应同添加地点。

## 6. 地点照片接口

### 6.1 地点照片分页

```text
GET /api/route-places/{routePlaceId}/photos
```

查询参数：

```text
page=1
pageSize=30
```

响应：

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "photoId": "ph001",
        "takenAt": "2025-08-12T10:20:00+08:00",
        "thumbUrl": "短期签名URL",
        "previewUrl": "短期签名URL"
      }
    ],
    "page": 1,
    "pageSize": 30,
    "hasMore": true
  }
}
```

### 6.2 移除地点误匹配照片

```text
DELETE /api/route-places/{routePlaceId}/photos/{photoId}
```

说明：

- 只删除地点和照片绑定关系。
- 不删除照片索引。
- 不删除 COS 图片。

### 6.3 换一批照片

```text
POST /api/route-places/{routePlaceId}/photos/recommend
```

请求：

```json
{
  "limit": 10,
  "excludePhotoIds": ["ph001", "ph002"]
}
```

响应：

```json
{
  "success": true,
  "data": {
    "photos": [
      {
        "photoId": "ph003",
        "thumbUrl": "短期签名URL",
        "previewUrl": "短期签名URL"
      }
    ]
  }
}
```

## 7. 写整条路线选图接口

### 7.1 推荐整条路线代表照片

```text
POST /api/routes/{routeId}/photos/recommend
```

请求：

```json
{
  "limit": 10,
  "excludePhotoIds": []
}
```

响应：

```json
{
  "success": true,
  "data": {
    "sourcePhotoCount": 428,
    "photos": [
      {
        "photoId": "ph001",
        "routeCityId": "rc001",
        "routePlaceId": "rp001",
        "placeName": "珠峰北坡",
        "thumbUrl": "短期签名URL",
        "previewUrl": "短期签名URL"
      }
    ]
  }
}
```

## 8. AI 写作接口

### 8.1 生成游记

```text
POST /api/writing/generate
```

请求：

```json
{
  "targetType": "place",
  "targetId": "rp001",
  "selectedPhotoIds": ["ph001", "ph002"],
  "mood": "震撼感动",
  "userNote": "那天风很大，第一次这么近看到珠峰，心里很震撼。"
}
```

`targetType`：

```text
route
place
```

响应：

```json
{
  "success": true,
  "data": {
    "draftId": "ad001",
    "title": "退休后第一次近看珠峰，心里满是震撼",
    "content": "正文内容...",
    "imageCaptions": [
      {
        "photoId": "ph001",
        "caption": "蓝天下的珠峰，远远望去格外清晰。"
      }
    ],
    "updatedAt": "2026-05-29T12:30:00+08:00"
  }
}
```

### 8.2 重新生成

```text
POST /api/writing/regenerate
```

请求：

```json
{
  "draftId": "ad001"
}
```

说明：

- 替换当前草稿。
- 前端必须先二次确认。

### 8.3 更朴实一点

```text
POST /api/writing/make-plainer
```

请求：

```json
{
  "draftId": "ad001"
}
```

### 8.4 更有感情一点

```text
POST /api/writing/make-more-emotional
```

请求：

```json
{
  "draftId": "ad001"
}
```

## 9. 文章草稿接口

### 9.1 获取当前草稿

```text
GET /api/article-drafts/current
```

查询参数：

```text
targetType=place
targetId=rp001
```

响应：

```json
{
  "success": true,
  "data": {
    "draft": {
      "id": "ad001",
      "title": "退休后第一次近看珠峰",
      "content": "正文内容...",
      "imageCaptions": [
        {
          "photoId": "ph001",
          "caption": "图片说明"
        }
      ],
      "selectedPhotoIds": ["ph001"],
      "mood": "震撼感动",
      "userNote": "补充说明",
      "updatedAt": "2026-05-29T12:30:00+08:00"
    }
  }
}
```

### 9.2 保存草稿

```text
PUT /api/article-drafts/{draftId}
```

请求：

```json
{
  "title": "退休后第一次近看珠峰",
  "content": "正文内容...",
  "imageCaptions": [
    {
      "photoId": "ph001",
      "caption": "图片说明"
    }
  ]
}
```

说明：

- 前端编辑时自动保存。
- 停止输入约 2 秒后调用。

## 10. 同步状态接口

### 10.1 获取同步状态

```text
GET /api/sync/status
```

响应：

```json
{
  "success": true,
  "data": {
    "agentOnline": true,
    "agentId": "home-mac-001",
    "agentVersion": "0.1.0",
    "lastHeartbeatAt": "2026-05-29T12:20:12+08:00",
    "lastScanAt": "2026-05-29T12:18:02+08:00",
    "lastSyncAt": "2026-05-29T12:20:00+08:00",
    "photoCount": 428,
    "gpsPhotoCount": 421,
    "gpsCoverageRate": 0.98,
    "thumbSyncedCount": 428,
    "previewSyncedCount": 428,
    "failedCount": 0,
    "pendingThumbCount": 0,
    "pendingPreviewCount": 0
  }
}
```

## 11. Photo-Agent 接口

Agent 接口使用 agent token 鉴权。

### 11.1 心跳

```text
POST /api/agent/heartbeat
```

请求：

```json
{
  "agentId": "home-mac-001",
  "version": "0.1.0",
  "status": "idle",
  "lastScanAt": "2026-05-29T12:18:02+08:00",
  "lastSyncAt": "2026-05-29T12:20:00+08:00",
  "photoCount": 428,
  "gpsPhotoCount": 421,
  "thumbSyncedCount": 428,
  "previewSyncedCount": 428,
  "failedCount": 0
}
```

后端处理：

- 更新 `agent` 表。
- 写 Redis `agent:online:{agentId}`。
- TTL 90 秒。

### 11.2 批量上传照片索引

```text
POST /api/agent/photos/batch
```

请求：

```json
{
  "agentId": "home-mac-001",
  "photos": [
    {
      "localPhotoId": "lp001",
      "relativePath": "2025/西藏/IMG_001.jpg",
      "fileName": "IMG_001.jpg",
      "fileSize": 3456789,
      "contentHash": "可选",
      "mtime": "2025-08-12T10:20:00+08:00",
      "takenAt": "2025-08-12T09:58:00+08:00",
      "lat": 28.191379,
      "lng": 86.83015,
      "width": 4032,
      "height": 3024,
      "hasGps": true
    }
  ]
}
```

响应：

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "localPhotoId": "lp001",
        "photoId": "ph001",
        "needThumb": true,
        "needPreview": true
      }
    ]
  }
}
```

### 11.3 申请 COS 上传地址

```text
POST /api/agent/assets/upload-ticket
```

请求：

```json
{
  "agentId": "home-mac-001",
  "photoId": "ph001",
  "assetType": "thumb",
  "contentType": "image/webp",
  "fileSize": 52000,
  "width": 360,
  "height": 270
}
```

响应：

```json
{
  "success": true,
  "data": {
    "storageProvider": "cos",
    "bucket": "baizhi-wandernote-1318597275",
    "region": "ap-guangzhou",
    "storageKey": "thumbs/home-mac-001/2025/08/ph001.webp",
    "uploadUrl": "COS 短期签名上传 URL",
    "expiresIn": 600
  }
}
```

说明：

- `assetType` 支持 `thumb`、`preview`。
- upload URL 只允许上传后端指定的 `storageKey`。
- Photo-Agent 不保存 COS SecretId / SecretKey。

### 11.4 通知资源上传完成

```text
POST /api/agent/assets/upload-complete
```

请求：

```json
{
  "agentId": "home-mac-001",
  "photoId": "ph001",
  "assetType": "thumb",
  "storageProvider": "cos",
  "storageKey": "thumbs/home-mac-001/2025/08/ph001.webp",
  "fileSize": 52000,
  "width": 360,
  "height": 270
}
```

响应：

```json
{
  "success": true,
  "data": {
    "assetId": "pa001"
  }
}
```

## 12. 图片签名下载

正常情况下，照片列表接口直接返回短期签名 URL。

如果前端需要刷新过期 URL，可以调用：

```text
POST /api/photos/signed-urls
```

请求：

```json
{
  "photoIds": ["ph001", "ph002"],
  "assetType": "thumb"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "urls": [
      {
        "photoId": "ph001",
        "assetType": "thumb",
        "url": "COS 短期签名下载 URL",
        "expiresIn": 900
      }
    ]
  }
}
```

## 13. 暂定错误码

```text
UNAUTHORIZED
TOKEN_EXPIRED
ACCESS_CODE_INVALID
AGENT_UNAUTHORIZED
ROUTE_NOT_FOUND
ROUTE_CITY_NOT_FOUND
ROUTE_PLACE_NOT_FOUND
PHOTO_NOT_FOUND
ARTICLE_DRAFT_NOT_FOUND
COS_UPLOAD_TICKET_FAILED
COS_ASSET_NOT_FOUND
AI_GENERATION_FAILED
TENCENT_MAP_FAILED
VALIDATION_FAILED
RATE_LIMITED
```

## 待细化

后续开发前需要继续细化：

- 字段校验规则
- 分页统一格式
- token header 名称
- agent token 配置方式
- COS 签名 URL 具体生成方式
- 腾讯地图失败降级策略
- AI 返回 JSON 容错策略
- 上传限速和 429 退避策略
