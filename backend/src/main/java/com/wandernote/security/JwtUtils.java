package com.wandernote.security;

import com.wandernote.config.JwtProperties;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Date;
import java.util.Optional;

/**
 * JWT 工具类
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtUtils {

    private final JwtProperties jwtProperties;

    private SecretKey getSigningKey() {
        byte[] keyBytes = jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    /**
     * 生成 JWT Token
     */
    public String generateToken() {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime expiresAt = now.plusHours(jwtProperties.getExpirationHours());
        LocalDateTime maxExpiresAt = now.plusDays(jwtProperties.getMaxExpirationDays());

        return Jwts.builder()
                .subject("wandernote-user")
                .issuedAt(toDate(now))
                .expiration(toDate(expiresAt))
                .claim("maxExpiresAt", maxExpiresAt.toString())
                .signWith(getSigningKey())
                .compact();
    }

    /**
     * 解析 Token
     */
    public Optional<Claims> parseToken(String token) {
        try {
            Claims claims = Jwts.parser()
                    .verifyWith(getSigningKey())
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
            return Optional.of(claims);
        } catch (Exception e) {
            log.debug("Token 解析失败: {}", e.getMessage());
            return Optional.empty();
        }
    }

    /**
     * 验证 Token 是否有效
     */
    public boolean validateToken(String token) {
        return parseToken(token).isPresent();
    }

    /**
     * 检查 Token 是否过期
     */
    public boolean isTokenExpired(String token) {
        return parseToken(token)
                .map(claims -> claims.getExpiration().before(new Date()))
                .orElse(true);
    }

    /**
     * 检查是否可以续期
     */
    public boolean canRefresh(String token) {
        return parseToken(token)
                .map(claims -> {
                    String maxExpiresAtStr = claims.get("maxExpiresAt", String.class);
                    if (maxExpiresAtStr == null) {
                        return false;
                    }
                    LocalDateTime maxExpiresAt = LocalDateTime.parse(maxExpiresAtStr);
                    return LocalDateTime.now().isBefore(maxExpiresAt);
                })
                .orElse(false);
    }

    /**
     * 获取 Token 过期时间
     */
    public LocalDateTime getExpirationDate(String token) {
        return parseToken(token)
                .map(claims -> toLocalDateTime(claims.getExpiration()))
                .orElse(null);
    }

    /**
     * 获取最大过期时间
     */
    public LocalDateTime getMaxExpirationDate(String token) {
        return parseToken(token)
                .map(claims -> {
                    String maxExpiresAtStr = claims.get("maxExpiresAt", String.class);
                    if (maxExpiresAtStr == null) {
                        return null;
                    }
                    return LocalDateTime.parse(maxExpiresAtStr);
                })
                .orElse(null);
    }

    /**
     * 生成 Token 哈希值
     */
    public String hashToken(String token) {
        return Integer.toHexString(token.hashCode());
    }

    private Date toDate(LocalDateTime localDateTime) {
        return Date.from(localDateTime.atZone(ZoneId.systemDefault()).toInstant());
    }

    private LocalDateTime toLocalDateTime(Date date) {
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
    }
}
