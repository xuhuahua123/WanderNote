package com.wandernote.security;

import com.wandernote.common.ErrorCode;
import com.wandernote.config.WanderNoteProperties;
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
import java.util.List;

/**
 * Agent Token 认证过滤器
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AgentAuthenticationFilter extends OncePerRequestFilter {

    private final WanderNoteProperties properties;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        String path = request.getRequestURI();

        // 只处理 Agent 接口
        if (!path.startsWith("/api/agent/")) {
            filterChain.doFilter(request, response);
            return;
        }

        // 从 header 获取 Agent Token
        String agentToken = extractAgentToken(request);

        if (!StringUtils.hasText(agentToken)) {
            log.debug("Agent 接口缺少 Token: {}", path);
            setErrorResponse(response, ErrorCode.AGENT_TOKEN_REQUIRED);
            return;
        }

        String expectedToken = properties.getAgentToken();
        if (expectedToken == null || !expectedToken.equals(agentToken)) {
            log.debug("Agent Token 无效: {}", path);
            setErrorResponse(response, ErrorCode.AGENT_TOKEN_INVALID);
            return;
        }

        // 设置认证信息
        UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                "agent",
                null,
                List.of(new SimpleGrantedAuthority("AGENT"))
        );
        SecurityContextHolder.getContext().setAuthentication(authentication);

        filterChain.doFilter(request, response);
    }

    private String extractAgentToken(HttpServletRequest request) {
        // 从 header 获取
        String token = request.getHeader("X-Agent-Token");
        if (StringUtils.hasText(token)) {
            return token;
        }

        // 从 Authorization header 获取
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
