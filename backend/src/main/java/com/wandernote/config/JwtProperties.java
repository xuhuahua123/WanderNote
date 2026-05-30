package com.wandernote.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * JWT 配置属性
 */
@Data
@Component
@ConfigurationProperties(prefix = "wandernote.jwt")
public class JwtProperties {

    /**
     * JWT 签名密钥
     */
    private String secret;

    /**
     * JWT 有效期（小时）
     */
    private int expirationHours = 2;

    /**
     * JWT 最大有效期（天）
     */
    private int maxExpirationDays = 7;
}
