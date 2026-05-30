package com.wandernote.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.wandernote.dto.AgentDto;
import com.wandernote.entity.Agent;
import com.wandernote.mapper.AgentMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.format.DateTimeParseException;
import java.util.concurrent.TimeUnit;

/**
 * Agent 服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AgentService {

    private final AgentMapper agentMapper;
    private final StringRedisTemplate redisTemplate;

    private static final String AGENT_ONLINE_KEY_PREFIX = "agent:online:";
    private static final long AGENT_ONLINE_TTL_SECONDS = 90;

    /**
     * 解析时间字符串
     */
    private LocalDateTime parseDateTime(String dateTimeStr) {
        if (dateTimeStr == null || dateTimeStr.isEmpty()) {
            return null;
        }
        try {
            OffsetDateTime offsetDateTime = OffsetDateTime.parse(dateTimeStr);
            return offsetDateTime.toLocalDateTime();
        } catch (DateTimeParseException e1) {
            try {
                return LocalDateTime.parse(dateTimeStr);
            } catch (DateTimeParseException e2) {
                log.warn("无法解析时间: {}", dateTimeStr);
                return null;
            }
        }
    }

    /**
     * 处理心跳
     */
    public void heartbeat(AgentDto.HeartbeatRequest request) {
        String agentId = request.getAgentId();

        // 更新 Redis 在线状态
        String onlineKey = AGENT_ONLINE_KEY_PREFIX + agentId;
        redisTemplate.opsForValue().set(onlineKey, "1", AGENT_ONLINE_TTL_SECONDS, TimeUnit.SECONDS);

        // 更新数据库
        Agent agent = agentMapper.selectOne(
                new LambdaQueryWrapper<Agent>().eq(Agent::getAgentId, agentId)
        );

        LocalDateTime now = LocalDateTime.now();

        if (agent == null) {
            agent = new Agent();
            agent.setAgentId(agentId);
            agent.setVersion(request.getVersion());
            agent.setStatus(request.getStatus() != null ? request.getStatus() : "idle");
            agent.setLastHeartbeatAt(now);
            agent.setLastScanAt(parseDateTime(request.getLastScanAt()));
            agent.setLastSyncAt(parseDateTime(request.getLastSyncAt()));
            agent.setPhotoCount(request.getPhotoCount() != null ? request.getPhotoCount() : 0);
            agent.setGpsPhotoCount(request.getGpsPhotoCount() != null ? request.getGpsPhotoCount() : 0);
            agent.setThumbSyncedCount(request.getThumbSyncedCount() != null ? request.getThumbSyncedCount() : 0);
            agent.setPreviewSyncedCount(request.getPreviewSyncedCount() != null ? request.getPreviewSyncedCount() : 0);
            agent.setFailedCount(request.getFailedCount() != null ? request.getFailedCount() : 0);
            agentMapper.insert(agent);
            log.info("新 Agent 注册: {}", agentId);
        } else {
            agent.setVersion(request.getVersion());
            agent.setStatus(request.getStatus() != null ? request.getStatus() : agent.getStatus());
            agent.setLastHeartbeatAt(now);
            if (request.getLastScanAt() != null) {
                agent.setLastScanAt(parseDateTime(request.getLastScanAt()));
            }
            if (request.getLastSyncAt() != null) {
                agent.setLastSyncAt(parseDateTime(request.getLastSyncAt()));
            }
            if (request.getPhotoCount() != null) {
                agent.setPhotoCount(request.getPhotoCount());
            }
            if (request.getGpsPhotoCount() != null) {
                agent.setGpsPhotoCount(request.getGpsPhotoCount());
            }
            if (request.getThumbSyncedCount() != null) {
                agent.setThumbSyncedCount(request.getThumbSyncedCount());
            }
            if (request.getPreviewSyncedCount() != null) {
                agent.setPreviewSyncedCount(request.getPreviewSyncedCount());
            }
            if (request.getFailedCount() != null) {
                agent.setFailedCount(request.getFailedCount());
            }
            agentMapper.updateById(agent);
        }
    }

    /**
     * 检查 Agent 是否在线
     */
    public boolean isAgentOnline(String agentId) {
        String onlineKey = AGENT_ONLINE_KEY_PREFIX + agentId;
        return Boolean.TRUE.equals(redisTemplate.hasKey(onlineKey));
    }

    /**
     * 获取 Agent 信息
     */
    public Agent getAgent(String agentId) {
        return agentMapper.selectOne(
                new LambdaQueryWrapper<Agent>().eq(Agent::getAgentId, agentId)
        );
    }

    /**
     * 获取同步状态
     */
    public AgentDto.SyncStatusResponse getSyncStatus() {
        // 获取最新的 Agent
        Agent agent = agentMapper.selectOne(
                new LambdaQueryWrapper<Agent>()
                        .orderByDesc(Agent::getLastHeartbeatAt)
                        .last("LIMIT 1")
        );

        AgentDto.SyncStatusResponse response = new AgentDto.SyncStatusResponse();

        if (agent == null) {
            response.setAgentOnline(false);
            return response;
        }

        boolean online = isAgentOnline(agent.getAgentId());
        response.setAgentOnline(online);
        response.setAgentId(agent.getAgentId());
        response.setAgentVersion(agent.getVersion());
        response.setLastHeartbeatAt(agent.getLastHeartbeatAt());
        response.setLastScanAt(agent.getLastScanAt());
        response.setLastSyncAt(agent.getLastSyncAt());
        response.setPhotoCount(agent.getPhotoCount());
        response.setGpsPhotoCount(agent.getGpsPhotoCount());
        response.setThumbSyncedCount(agent.getThumbSyncedCount());
        response.setPreviewSyncedCount(agent.getPreviewSyncedCount());
        response.setFailedCount(agent.getFailedCount());

        // 计算 GPS 覆盖率
        if (agent.getPhotoCount() != null && agent.getPhotoCount() > 0 && agent.getGpsPhotoCount() != null) {
            response.setGpsCoverageRate((double) agent.getGpsPhotoCount() / agent.getPhotoCount());
        } else {
            response.setGpsCoverageRate(0.0);
        }

        // TODO: 计算待同步数量
        response.setPendingThumbCount(0);
        response.setPendingPreviewCount(0);

        return response;
    }
}
