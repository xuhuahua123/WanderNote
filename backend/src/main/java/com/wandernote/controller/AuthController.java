package com.wandernote.controller;

import com.wandernote.common.ApiResponse;
import com.wandernote.common.BusinessException;
import com.wandernote.common.ErrorCode;
import com.wandernote.config.JwtProperties;
import com.wandernote.config.WanderNoteProperties;
import com.wandernote.entity.AccessSession;
import com.wandernote.mapper.AccessSessionMapper;
import com.wandernote.security.JwtUtils;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

/**
 * 认证控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final WanderNoteProperties properties;
    private final JwtUtils jwtUtils;
    private final JwtProperties jwtProperties;
    private final AccessSessionMapper accessSessionMapper;

    /**
     * 访问码登录
     */
    @PostMapping("/access-code/login")
    public ApiResponse<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        String expectedCode = properties.getAccessCode();

        if (expectedCode == null || expectedCode.isEmpty()) {
            log.error("访问码未配置");
            throw new BusinessException(ErrorCode.INTERNAL_ERROR, "系统配置错误");
        }

        if (!expectedCode.equals(request.getAccessCode())) {
            log.warn("访问码不正确");
            throw new BusinessException(ErrorCode.ACCESS_CODE_INVALID);
        }

        // 生成 token
        String token = jwtUtils.generateToken();
        String tokenHash = jwtUtils.hashToken(token);
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime expiresAt = now.plusHours(jwtProperties.getExpirationHours());
        LocalDateTime maxExpiresAt = now.plusDays(jwtProperties.getMaxExpirationDays());

        // 创建会话记录
        AccessSession session = new AccessSession();
        session.setTokenHash(tokenHash);
        session.setCreatedAt(now);
        session.setExpiresAt(expiresAt);
        session.setLastSeenAt(now);
        accessSessionMapper.insert(session);

        LoginResponse response = new LoginResponse();
        response.setAccessToken(token);
        response.setExpiresAt(expiresAt);
        response.setMaxExpiresAt(maxExpiresAt);

        log.info("访问码登录成功");
        return ApiResponse.success(response);
    }

    /**
     * Token 续期
     */
    @PostMapping("/refresh")
    public ApiResponse<RefreshResponse> refresh(@RequestHeader("Authorization") String authHeader) {
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            throw new BusinessException(ErrorCode.TOKEN_INVALID);
        }

        String oldToken = authHeader.substring(7);

        // 检查是否可以续期
        if (!jwtUtils.canRefresh(oldToken)) {
            throw new BusinessException(ErrorCode.TOKEN_EXPIRED, "Token 已超过最大有效期，请重新登录");
        }

        // 生成新 token
        String newToken = jwtUtils.generateToken();
        String newTokenHash = jwtUtils.hashToken(newToken);
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime expiresAt = now.plusHours(jwtProperties.getExpirationHours());

        // 创建新会话记录
        AccessSession session = new AccessSession();
        session.setTokenHash(newTokenHash);
        session.setCreatedAt(now);
        session.setExpiresAt(expiresAt);
        session.setLastSeenAt(now);
        accessSessionMapper.insert(session);

        // 撤销旧会话
        String oldTokenHash = jwtUtils.hashToken(oldToken);
        AccessSession oldSession = accessSessionMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<AccessSession>()
                        .eq(AccessSession::getTokenHash, oldTokenHash)
        );
        if (oldSession != null) {
            oldSession.setRevokedAt(now);
            accessSessionMapper.updateById(oldSession);
        }

        RefreshResponse response = new RefreshResponse();
        response.setAccessToken(newToken);
        response.setExpiresAt(expiresAt);

        log.info("Token 续期成功");
        return ApiResponse.success(response);
    }

    @Data
    public static class LoginRequest {
        @NotBlank(message = "访问码不能为空")
        private String accessCode;
    }

    @Data
    public static class LoginResponse {
        private String accessToken;
        private LocalDateTime expiresAt;
        private LocalDateTime maxExpiresAt;
    }

    @Data
    public static class RefreshResponse {
        private String accessToken;
        private LocalDateTime expiresAt;
    }
}
