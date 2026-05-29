# 006. 外部服务与密钥安全决策记录

## 状态

已确认。

## 背景

项目会使用三个外部服务：

- 腾讯地图 WebService：行政区划、地点搜索、地点坐标解析
- 腾讯云 COS：存储缩略图和预览图
- 小米 MiMo-V2.5：AI 游记生成和文章改写

这些服务都涉及密钥，密钥不能放在前端，也不能提交到代码仓库。

## 总体原则

所有外部服务密钥只放在云端后端。

```text
H5 前端：不保存任何腾讯地图/COS/MiMo 密钥
Photo-Agent：不保存腾讯地图/COS/MiMo 密钥
云端后端：保存并使用外部服务密钥
```

前端和 Photo-Agent 都只调用自己的后端接口。

后端负责：

- 调用腾讯地图
- 生成 COS 上传签名 URL
- 生成 COS 下载签名 URL
- 调用 MiMo-V2.5
- 记录调用日志
- 处理失败和重试

## 密钥存放方式

生产环境使用服务器环境变量或服务器安全配置。

不允许：

- 写进前端代码
- 写进 Photo-Agent 代码
- 写进 Git 仓库
- 写进 Markdown 文档
- 发到聊天记录里
- 放到可公开访问的配置文件里

建议后端读取以下环境变量：

```text
TENCENT_MAP_KEY=服务器环境变量配置

COS_REGION=ap-guangzhou
COS_BUCKET=baizhi-wandernote-1318597275
COS_SECRET_ID=服务器环境变量配置
COS_SECRET_KEY=服务器环境变量配置
COS_UPLOAD_URL_TTL_SECONDS=600
COS_DOWNLOAD_URL_TTL_SECONDS=900

MIMO_API_BASE_URL=小米 MiMo API 地址
MIMO_API_KEY=服务器环境变量配置
MIMO_MODEL=mimo-v2.5

AGENT_TOKEN=服务器环境变量配置
ACCESS_CODE=服务器环境变量配置
```

本地开发可以使用 `.env`，但 `.env` 必须加入 `.gitignore`。

仓库里只允许提交 `.env.example`：

```text
TENCENT_MAP_KEY=
COS_REGION=ap-guangzhou
COS_BUCKET=baizhi-wandernote-1318597275
COS_SECRET_ID=
COS_SECRET_KEY=
COS_UPLOAD_URL_TTL_SECONDS=600
COS_DOWNLOAD_URL_TTL_SECONDS=900
MIMO_API_BASE_URL=
MIMO_API_KEY=
MIMO_MODEL=mimo-v2.5
AGENT_TOKEN=
ACCESS_CODE=
```

## 腾讯地图服务

用途：

- 初始化行政区划数据
- 用户添加地点时解析地点候选
- 获取地点坐标

MVP 使用接口：

```text
GET /ws/district/v1/list
GET /ws/place/v1/suggestion
```

可选接口：

```text
GET /ws/place/v1/detail
GET /ws/geocoder/v1/
```

调用方式：

```text
云端后端 -> 腾讯地图 WebService
```

前端不直接调用腾讯地图。

Photo-Agent 不调用腾讯地图。

腾讯地图 key 只保存在后端环境变量：

```text
TENCENT_MAP_KEY
```

后端建议做缓存：

- 行政区划数据落库到 `district`
- POI 查询结果缓存到 `poi_cache`

这样可以减少重复调用，并方便排查地点解析问题。

### 腾讯地图接口清单

MVP 必用接口：

```text
1. 行政区划列表
GET https://apis.map.qq.com/ws/district/v1/list

用途：
- 初始化省、市/地区、区县数据
- 支撑前端“添加城市”
- 写入 district 表

调用频率：
- 很低
- 部署初始化调用一次
- 后续可按月或手动刷新

建议参数：
- key
- struct_type=1
```

```text
2. 关键词输入提示 / 地点候选
GET https://apis.map.qq.com/ws/place/v1/suggestion

用途：
- 用户在城市下面输入二级地点时解析候选 POI
- 例如：日喀则市 + 珠峰北坡
- 返回 POI 名称、地址、分类、省市区、坐标、POI ID
- 后端再结合照片 GPS 选择最佳候选

调用频率：
- 中低
- 每次添加地点时调用
- 相同 keyword + region 结果应缓存到 poi_cache

建议参数：
- key
- keyword
- region
```

MVP 备用接口：

```text
3. 地点搜索
GET https://apis.map.qq.com/ws/place/v1/search

用途：
- suggestion 结果不理想时备用
- 支持 boundary=region 指定城市/区域搜索
- 也可用于 nearby 搜索

调用频率：
- 低
- 只在 suggestion 结果不足时 fallback
```

```text
4. POI 详情
GET https://apis.map.qq.com/ws/place/v1/detail

用途：
- 根据 suggestion/search 返回的 POI ID 获取更完整信息
- MVP 通常不需要

调用频率：
- 很低
- 仅当候选信息不足时调用
```

暂不使用：

```text
逆地址解析 /ws/geocoder/v1/
地址解析 /ws/geocoder/v1/
路线规划
距离矩阵
IP 定位
天气
静态图
坐标转换
```

说明：

- 本项目的主链路是“地点名称 -> 腾讯 POI 坐标 -> 匹配照片 GPS”。
- 不需要地图展示、路线规划或导航能力。
- 不需要逐张照片做逆地址解析，否则会消耗大量配额。
- 照片归属地点由后端用 GPS 距离和路线上下文计算，不靠腾讯逐张反查。

## 腾讯云 COS 服务

用途：

- 存储缩略图 thumb
- 存储预览图 preview

已确认桶信息：

```text
Bucket：baizhi-wandernote-1318597275
Region：ap-guangzhou
权限：私有读写
```

COS 桶必须保持私有读写。

不允许公读。

不允许前端直接持有 COS 密钥。

不允许 Photo-Agent 直接持有 COS 密钥。

### 上传流程

```text
Photo-Agent -> 后端申请上传地址
后端 -> 生成 COS storage_key 和短期上传 URL
Photo-Agent -> 使用短期 URL 直传 COS
Photo-Agent -> 通知后端上传完成
后端 -> 写入 photo_asset
```

上传 URL 有效期建议：

```text
600 秒
```

### 下载流程

```text
H5 -> 请求照片列表
后端 -> 生成 COS 短期下载 URL
H5 -> 使用短期 URL 加载图片
```

下载 URL 有效期建议：

```text
900 秒
```

如果前端图片 URL 过期，重新请求后端刷新签名 URL。

### 对象路径

```text
thumbs/{agentId}/{yyyy}/{mm}/{photoId}.webp
previews/{agentId}/{yyyy}/{mm}/{photoId}.webp
```

示例：

```text
thumbs/home-mac-001/2025/08/ph001.webp
previews/home-mac-001/2025/08/ph001.webp
```

数据库 `photo_asset` 保存：

```text
storage_provider = cos
bucket = baizhi-wandernote-1318597275
region = ap-guangzhou
storage_key = thumbs/home-mac-001/2025/08/ph001.webp
```

数据库不需要保存长期公开 URL。

前端需要图片时，由后端临时生成签名 URL。

## 小米 MiMo-V2.5

用途：

- 生成游记
- 重新生成
- 更朴实一点
- 更有感情一点

调用方式：

```text
H5 -> 云端后端 -> MiMo-V2.5
```

前端不直接调用 MiMo。

Photo-Agent 不调用 MiMo。

MiMo API key 只保存在后端环境变量：

```text
MIMO_API_KEY
```

模型配置：

```text
MIMO_MODEL=mimo-v2.5
```

后端封装统一服务：

```text
AiWritingService
```

每次 AI 调用写入：

```text
article_generation_log
```

记录：

- 调用动作
- 模型名称
- 请求内容
- 返回内容
- token 数量
- 成本
- 是否成功
- 错误信息

## Photo-Agent 凭证

Photo-Agent 只保存自己的 Agent Token。

```text
AGENT_TOKEN
```

Agent Token 用于调用：

- 心跳接口
- 照片索引上传接口
- COS 上传地址申请接口
- 上传完成通知接口

Agent Token 不具备：

- 腾讯地图调用权限
- COS 永久读写权限
- MiMo 调用权限
- 管理路线/文章权限

如果 Agent Token 泄露，只能访问 Agent 相关接口，应支持后端更换 token。

## H5 访问凭证

H5 使用访问码登录。

访问码只保存在后端环境变量：

```text
ACCESS_CODE
```

登录成功后，后端返回 access token。

规则：

```text
基础有效期：2 小时
活跃自动续期：需要
最长保持：7 天
```

H5 access token 只用于访问业务接口，不包含任何外部服务密钥。

## 日志安全

日志中不能输出：

- 腾讯地图 key
- COS SecretId
- COS SecretKey
- MiMo API key
- Agent Token
- H5 access token
- 访问码

可以输出：

- request id
- route id
- photo id
- storage_key
- provider_poi_id
- 错误码
- 外部服务返回的非敏感错误信息

## 密钥轮换

需要支持手动轮换：

- 腾讯地图 key
- COS SecretId / SecretKey
- MiMo API key
- Agent Token
- 访问码

MVP 可以通过修改服务器环境变量并重启服务完成轮换。

后续如果需要更平滑，可以再做后台配置和热更新。

## 产品原则

核心原则：

```text
所有外部服务密钥只在云端后端。
前端不碰密钥。
Agent 不碰外部服务永久密钥。
COS 桶私有读写。
图片访问使用短期签名 URL。
AI 调用只由后端代理。
```
