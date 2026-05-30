package com.wandernote.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.LocalDateTime;

/**
 * 访问会话表
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("access_session")
public class AccessSession extends BaseEntity {

    /**
     * Token 哈希值
     */
    private String tokenHash;

    /**
     * 会话创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 会话过期时间
     */
    private LocalDateTime expiresAt;

    /**
     * 最后活跃时间
     */
    private LocalDateTime lastSeenAt;

    /**
     * 撤销时间
     */
    private LocalDateTime revokedAt;

    /**
     * 用户代理
     */
    private String userAgent;

    /**
     * 客户端 IP
     */
    private String clientIp;
}
