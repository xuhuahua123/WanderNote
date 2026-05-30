package com.wandernote.common;

import lombok.Getter;

/**
 * 统一错误码枚举
 */
@Getter
public enum ErrorCode {

    // 认证相关
    UNAUTHORIZED("UNAUTHORIZED", "未授权，请先登录"),
    TOKEN_EXPIRED("TOKEN_EXPIRED", "登录已过期，请重新登录"),
    TOKEN_INVALID("TOKEN_INVALID", "无效的登录凭证"),
    ACCESS_CODE_INVALID("ACCESS_CODE_INVALID", "访问码不正确"),
    ACCESS_CODE_REQUIRED("ACCESS_CODE_REQUIRED", "请输入访问码"),

    // Agent 认证相关
    AGENT_UNAUTHORIZED("AGENT_UNAUTHORIZED", "Agent 未授权"),
    AGENT_TOKEN_INVALID("AGENT_TOKEN_INVALID", "无效的 Agent Token"),
    AGENT_TOKEN_REQUIRED("AGENT_TOKEN_REQUIRED", "缺少 Agent Token"),

    // 资源不存在
    ROUTE_NOT_FOUND("ROUTE_NOT_FOUND", "路线不存在"),
    ROUTE_CITY_NOT_FOUND("ROUTE_CITY_NOT_FOUND", "路线城市不存在"),
    ROUTE_PLACE_NOT_FOUND("ROUTE_PLACE_NOT_FOUND", "地点不存在"),
    PHOTO_NOT_FOUND("PHOTO_NOT_FOUND", "照片不存在"),
    ARTICLE_DRAFT_NOT_FOUND("ARTICLE_DRAFT_NOT_FOUND", "草稿不存在"),
    DISTRICT_NOT_FOUND("DISTRICT_NOT_FOUND", "行政区划不存在"),
    AGENT_NOT_FOUND("AGENT_NOT_FOUND", "Agent 不存在"),

    // COS 相关
    COS_UPLOAD_TICKET_FAILED("COS_UPLOAD_TICKET_FAILED", "生成上传凭证失败"),
    COS_ASSET_NOT_FOUND("COS_ASSET_NOT_FOUND", "资源不存在"),
    COS_UPLOAD_FAILED("COS_UPLOAD_FAILED", "COS 上传失败"),

    // AI 相关
    AI_GENERATION_FAILED("AI_GENERATION_FAILED", "AI 生成失败"),
    AI_PROVIDER_UNAVAILABLE("AI_PROVIDER_UNAVAILABLE", "AI 服务不可用"),

    // 腾讯地图相关
    TENCENT_MAP_FAILED("TENCENT_MAP_FAILED", "腾讯地图服务调用失败"),
    TENCENT_MAP_NO_RESULT("TENCENT_MAP_NO_RESULT", "未找到匹配的地点"),

    // 参数校验
    VALIDATION_FAILED("VALIDATION_FAILED", "参数校验失败"),
    INVALID_PARAMETER("INVALID_PARAMETER", "无效参数"),
    MISSING_PARAMETER("MISSING_PARAMETER", "缺少必要参数"),

    // 限流
    RATE_LIMITED("RATE_LIMITED", "请求过于频繁，请稍后再试"),

    // 系统错误
    INTERNAL_ERROR("INTERNAL_ERROR", "服务器内部错误"),
    DATABASE_ERROR("DATABASE_ERROR", "数据库错误"),
    REDIS_ERROR("REDIS_ERROR", "Redis 错误");

    private final String code;
    private final String message;

    ErrorCode(String code, String message) {
        this.code = code;
        this.message = message;
    }
}
