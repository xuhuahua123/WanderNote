package com.wandernote.controller;

import com.wandernote.common.ApiResponse;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.sql.SQLException;

/**
 * 健康检查控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/health")
@RequiredArgsConstructor
public class HealthController {

    private final DataSource dataSource;
    private final StringRedisTemplate redisTemplate;

    /**
     * 健康检查
     */
    @GetMapping
    public ApiResponse<HealthResponse> health() {
        HealthResponse response = new HealthResponse();
        response.setStatus("ok");
        response.setTimestamp(System.currentTimeMillis());
        return ApiResponse.success(response);
    }

    /**
     * 检查数据库连接
     */
    @GetMapping("/db")
    public ApiResponse<DbHealthResponse> dbHealth() {
        DbHealthResponse response = new DbHealthResponse();

        try {
            dataSource.getConnection().close();
            response.setConnected(true);
            response.setMessage("数据库连接正常");
        } catch (SQLException e) {
            log.error("数据库连接失败", e);
            response.setConnected(false);
            response.setMessage("数据库连接失败: " + e.getMessage());
        }

        return ApiResponse.success(response);
    }

    /**
     * 检查 Redis 连接
     */
    @GetMapping("/redis")
    public ApiResponse<RedisHealthResponse> redisHealth() {
        RedisHealthResponse response = new RedisHealthResponse();

        try {
            redisTemplate.getConnectionFactory().getConnection().ping();
            response.setConnected(true);
            response.setMessage("Redis 连接正常");
        } catch (Exception e) {
            log.error("Redis 连接失败", e);
            response.setConnected(false);
            response.setMessage("Redis 连接失败: " + e.getMessage());
        }

        return ApiResponse.success(response);
    }

    @Data
    public static class HealthResponse {
        private String status;
        private Long timestamp;
    }

    @Data
    public static class DbHealthResponse {
        private Boolean connected;
        private String message;
    }

    @Data
    public static class RedisHealthResponse {
        private Boolean connected;
        private String message;
    }
}
