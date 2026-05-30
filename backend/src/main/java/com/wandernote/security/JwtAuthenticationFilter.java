package com.wandernote.security;

import com.wandernote.common.ErrorCode;
import com.wandernote.entity.AccessSession;
import com.wandernote.mapper.AccessSessionMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.List;

/**
 * JWT 认证过滤器
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtUtils jwtUtils;
    private final AccessSessionMapper accessSessionMapper;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        String path = request.getRequestURI();

        // 跳过公开接口和 Agent 接口
        if (path.startsWith("/api/auth/") || path.startsWith("/api/agent/")) {
            filterChain.doFilter(request, response);
            return;
        }

        // 从 header 获取 token
        String token = extractToken(request);

        if (!StringUtils.hasText(token)) {
            filterChain.doFilter(request, response);
            return;
        }

        // 验证 token
        if (!jwtUtils.validateToken(token)) {
            log.debug("Token 无效: {}", path);
            setErrorResponse(response, ErrorCode.TOKEN_INVALID);
            return;
        }

        // 检查 token 是否过期
        if (jwtUtils.isTokenExpired(token)) {
            log.debug("Token 已过期: {}", path);
            setErrorResponse(response, ErrorCode.TOKEN_EXPIRED);
            return;
        }

        // 检查会话是否有效
        String tokenHash = jwtUtils.hashToken(token);
        AccessSession session = accessSessionMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<AccessSession>()
                        .eq(AccessSession::getTokenHash, tokenHash)
                        .isNull(AccessSession::getRevokedAt)
        );

        if (session == null) {
            log.debug("会话不存在: {}", path);
            setErrorResponse(response, ErrorCode.TOKEN_INVALID);
            return;
        }

        // 更新最后活跃时间
        session.setLastSeenAt(LocalDateTime.now());
        accessSessionMapper.updateById(session);

        // 设置认证信息
        UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                session.getId(),
                null,
                List.of(new SimpleGrantedAuthority("USER"))
        );
        SecurityContextHolder.getContext().setAuthentication(authentication);

        filterChain.doFilter(request, response);
    }

    private String extractToken(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (StringUtils.hasText(authHeader) && authHeader.startsWith("Bearer ")) {
            return authHeader.substring(7);
        }
        return null;
    }

    private void setErrorResponse(HttpServletResponse response, ErrorCode errorCode) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(String.format(
                "{\"success\":false,\"error\":{\"code\":\"%s\",\"message\":\"%s\"}}",
                errorCode.getCode(),
                errorCode.getMessage()
        ));
    }
}
