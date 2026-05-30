package com.wandernote.controller;

import com.wandernote.common.ApiResponse;
import com.wandernote.service.DistrictService;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 管理接口控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/admin")
@RequiredArgsConstructor
public class AdminController {

    private final DistrictService districtService;

    /**
     * 初始化行政区划数据
     */
    @PostMapping("/districts/init")
    public ApiResponse<InitResponse> initDistricts() {
        log.info("开始初始化行政区划数据...");

        try {
            districtService.initFromTencentMap();

            InitResponse response = new InitResponse();
            response.setMessage("行政区划初始化成功");
            return ApiResponse.success(response);

        } catch (Exception e) {
            log.error("行政区划初始化失败", e);
            return ApiResponse.error("INIT_FAILED", "初始化失败: " + e.getMessage());
        }
    }

    @Data
    public static class InitResponse {
        private String message;
    }
}
