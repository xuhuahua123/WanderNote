# 003. 后端数据模型草案

## 状态

已确认。

## 背景

前端 MVP 和 Photo-Agent 边界已经基本确认。

后端需要连接三类数据：

- Photo-Agent 上传的照片索引和同步状态
- 前端维护的路线、城市、地点和文章
- 腾讯地图提供的行政区划和 POI 坐标

本文件是后端数据模型草案，明天继续讨论确认。

## 设计原则

- MVP 按单用户系统设计，避免复杂用户体系。
- 路线和文章由云端后端管理。
- Photo-Agent 只上传照片素材，不参与路线业务。
- 原图不上传。
- 缩略图和预览图都保存到腾讯 COS。
- Photo-Agent 通过后端生成的临时上传地址直传 COS。
- 照片 GPS 是地点匹配的核心字段。
- 草稿不做历史版本，只保存每个写作对象的当前草稿。

## 核心模块

```text
访问/系统
- access_session
- agent

地图/行政区划
- district
- poi_cache

照片
- photo
- photo_asset

路线
- route
- route_city
- route_place
- route_place_photo

文章
- article_draft
- article_generation_log
```

## access_session

访问码登录后的会话表。

MVP 不做用户注册和多用户体系，但仍建议保存会话，方便失效、续期和排查。

```text
access_session
- id
- token_hash
- created_at
- expires_at
- last_seen_at
- revoked_at
- user_agent
- client_ip
```

说明：

- 访问码本身不入库明文保存。
- 前端拿 token 访问接口。
- token 基础有效期 2 小时。
- 活跃时自动续期。
- 最长保持 7 天。

## agent

家庭电脑 Photo-Agent 状态表。

```text
agent
- id
- agent_id
- name
- version
- status
- last_heartbeat_at
- last_scan_at
- last_sync_at
- photo_count
- gps_photo_count
- thumb_synced_count
- preview_synced_count
- failed_count
- created_at
- updated_at
```

说明：

- 当前在线状态优先由 Redis 判断。
- 数据库保存最近一次心跳和同步统计。
- `agent_id` 示例：`home-mac-001`。

Redis 在线 key：

```text
agent:online:{agentId} = 1
TTL = 90 秒
```

## district

腾讯地图行政区划数据表。

用于前端选择省、市/地区，也用于地点解析时限制城市上下文。

```text
district
- adcode
- name
- full_name
- level
- parent_adcode
- province_adcode
- province_name
- city_adcode
- city_name
- lat
- lng
- source
- updated_at
```

说明：

- 数据来自腾讯地图行政区划接口。
- 前端一级路线节点只允许选择市/地区级数据。
- 省份只作为分组标题和颜色提示。

## poi_cache

腾讯地图 POI 查询缓存。

用于减少重复调用腾讯地图 API，并方便排查地点解析结果。

```text
poi_cache
- id
- keyword
- region_adcode
- region_name
- provider
- provider_poi_id
- title
- address
- category
- province_name
- city_name
- district_name
- lat
- lng
- raw_json
- created_at
- updated_at
```

说明：

- `keyword` 示例：`珠峰北坡`。
- `region_name` 示例：`日喀则市`。
- `raw_json` 保留腾讯地图原始返回，方便后续优化匹配算法。

## photo

照片索引主表。

由 Photo-Agent 上传。

```text
photo
- id
- agent_id
- local_photo_id
- relative_path
- file_name
- file_size
- content_hash
- mtime
- taken_at
- lat
- lng
- width
- height
- has_gps
- sync_status
- last_error
- created_at
- updated_at
```

说明：

- `relative_path` 是相对照片根目录的路径。
- `local_photo_id` 由 Agent 本地生成，用于幂等同步。
- `content_hash` 用于判断文件变化。
- 没有 GPS 的照片也保存，但 MVP 不参与自动地点匹配。

建议唯一约束：

```text
unique(agent_id, local_photo_id)
```

其中 `local_photo_id` 由 Agent 基于本地照片稳定信息生成。

推荐生成方式：

```text
local_photo_id = hash(relative_path + file_size + mtime)
```

`content_hash` 仍然保留，但不建议作为唯一主键的一部分。

原因：

- 全量计算文件内容 hash 成本较高，照片多时会拖慢扫描。
- `relative_path + content_hash` 在文件移动或重命名时容易产生新的照片记录。
- `local_photo_id` 更适合作为 Agent 与云端之间的幂等同步标识。
- `content_hash` 更适合用于判断文件内容是否变化，而不是做业务主键。

## photo_asset

照片派生资源表。

保存缩略图和预览图。

```text
photo_asset
- id
- photo_id
- asset_type
- storage_key
- url
- width
- height
- file_size
- sync_status
- created_at
- updated_at
```

`asset_type`：

```text
thumb
preview
```

说明：

- thumb 长边约 360px。
- preview 长边约 1280px。
- MVP 不保存原图资源。
- thumb 保存到腾讯 COS。
- preview 保存到腾讯 COS。
- Photo-Agent 不保存 COS 密钥。
- 后端生成 COS 存储路径和临时上传 URL。
- Photo-Agent 使用临时上传 URL 直传 COS。
- 上传完成后，Photo-Agent 通知后端入库。

## route

旅行路线表。

```text
route
- id
- name
- year
- cover_photo_id
- summary
- created_at
- updated_at
```

说明：

- 新建路线 MVP 只需要 `name` 和 `year`。
- 起点和终点不放在 route 表里，统一作为地点添加。
- 封面图由系统自动从路线照片中选择。

## route_city

路线中的一级节点：城市/地区。

```text
route_city
- id
- route_id
- city_adcode
- city_name
- province_adcode
- province_name
- sort_order
- note
- created_at
- updated_at
```

说明：

- 城市必须来自 `district` 表。
- 省份用于路线详情页分组展示。
- `sort_order` 表示旅行顺序。
- MVP 默认新增城市追加到最后。

## route_place

路线中的二级节点：具体地点。

```text
route_place
- id
- route_city_id
- name
- source_type
- tencent_poi_id
- resolved_title
- resolved_address
- category
- lat
- lng
- match_status
- match_photo_count
- sort_order
- created_at
- updated_at
```

`source_type`：

```text
custom
tencent_poi
```

`match_status`：

```text
matched
unmatched
pending
```

说明：

- 用户可以自由输入地点名。
- 后端用当前城市上下文调用腾讯地图。
- 如果找到可靠 POI，保存坐标和腾讯 POI ID。
- 如果没有找到可靠结果，也允许保存地点。

## route_place_photo

地点和照片绑定表。

```text
route_place_photo
- id
- route_place_id
- photo_id
- match_source
- distance_meters
- score
- created_at
```

`match_source`：

```text
gps_auto
manual
system_recommend
```

说明：

- 后端自动匹配照片后写入该表。
- 用户移除误匹配照片时，直接删除绑定记录。
- 不保留被移除照片的绑定历史。
- 不删除原始照片索引。

## article_draft

当前文章草稿表。

每个路线或地点只保留一份当前草稿。

```text
article_draft
- id
- target_type
- target_id
- title
- content
- image_captions_json
- selected_photo_ids_json
- mood
- user_note
- status
- created_at
- updated_at
```

`target_type`：

```text
route
place
```

说明：

- 地点写作：`target_type = place`，`target_id = route_place.id`。
- 整条路线写作：`target_type = route`，`target_id = route.id`。
- 不做草稿历史。
- 重新生成会替换当前草稿，需要前端二次确认。
- 前端编辑标题、正文、图片说明后自动保存。

## article_generation_log

AI 文章生成日志表。

用于记录 AI 调用历史、排查问题和后续优化提示词。

```text
article_generation_log
- id
- target_type
- target_id
- action_type
- model_provider
- model_name
- request_json
- response_json
- input_token_count
- output_token_count
- cost_amount
- success
- error_message
- created_at
```

`action_type`：

```text
generate
regenerate
make_plainer
make_more_emotional
```

说明：

- 该表不作为用户草稿历史展示。
- 用户前端仍然只看到当前文章。
- 该表只用于开发排查、成本统计和后续优化。

## 关系概览

```text
agent 1 -> N photo
photo 1 -> N photo_asset

route 1 -> N route_city
route_city 1 -> N route_place
route_place N -> N photo，通过 route_place_photo

route 1 -> 1 article_draft
route_place 1 -> 1 article_draft

district 提供 route_city 的城市选择来源
poi_cache 辅助 route_place 的地点解析
```

## 已确认问题

已确认：

1. `photo` 唯一标识推荐使用 `local_photo_id`。
2. `route_place_photo` 中被用户移除的照片不保留绑定记录，直接删除绑定。
3. 需要单独的 `article_generation_log` 记录 AI 调用历史。
4. 路线、城市、地点不做软删除。
5. 原图不上传。
6. 缩略图和预览图都保存到腾讯 COS。
7. Photo-Agent 不保存 COS 密钥。
8. 后端负责生成 COS 存储路径和临时上传 URL。
9. Photo-Agent 使用临时上传 URL 直传 COS。
10. 上传完成后，Photo-Agent 通知后端写入 `photo_asset`。

## 腾讯 COS 配置

MVP 使用腾讯 COS 存储缩略图和预览图。

已确认桶信息：

```text
存储桶名称：baizhi-wandernote-1318597275
所属地域：广州（中国）（ap-guangzhou）
访问权限：私有读写
创建时间：2026-05-29 12:12:46
```

后端环境变量建议：

```text
COS_REGION=ap-guangzhou
COS_BUCKET=baizhi-wandernote-1318597275
COS_SECRET_ID=服务器环境变量配置
COS_SECRET_KEY=服务器环境变量配置
COS_UPLOAD_URL_TTL_SECONDS=600
COS_DOWNLOAD_URL_TTL_SECONDS=900
```

COS SecretId 和 SecretKey 不写入项目文档，不提交代码仓库，只放在服务器环境变量或安全配置中。

对象路径建议：

```text
thumbs/{agentId}/{yyyy}/{mm}/{photoId}.webp
previews/{agentId}/{yyyy}/{mm}/{photoId}.webp
```

示例：

```text
thumbs/home-mac-001/2025/08/p_abc123.webp
previews/home-mac-001/2025/08/p_abc123.webp
```

COS 桶保持私有读写。

前端访问图片时，后端生成短期签名下载 URL。

Photo-Agent 上传图片时，后端生成短期签名上传 URL。

## 初步结论

这套模型可以支撑当前前端 MVP：

- 首页路线卡片
- 路线详情页
- 添加城市和地点
- 地点自动匹配照片
- 换一批照片
- 写整条路线
- AI 写作准备页
- 文章结果页
- 自动保存当前草稿
- Agent 同步状态页
