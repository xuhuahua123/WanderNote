package com.wandernote.controller;

import com.wandernote.common.ApiResponse;
import com.wandernote.dto.AgentDto;
import com.wandernote.service.AgentService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 同步状态控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/sync")
@RequiredArgsConstructor
public class SyncStatusController {

    private final AgentService agentService;

    /**
     * 获取同步状态
     */
    @GetMapping("/status")
    public ApiResponse<AgentDto.SyncStatusResponse> getSyncStatus() {
        AgentDto.SyncStatusResponse response = agentService.getSyncStatus();
        return ApiResponse.success(response);
    }
}
