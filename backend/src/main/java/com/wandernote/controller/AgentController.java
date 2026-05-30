package com.wandernote.controller;

import com.wandernote.common.ApiResponse;
import com.wandernote.dto.AgentDto;
import com.wandernote.service.AgentService;
import com.wandernote.service.CosService;
import com.wandernote.service.PhotoService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Agent 控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/agent")
@RequiredArgsConstructor
public class AgentController {

    private final AgentService agentService;
    private final PhotoService photoService;
    private final CosService cosService;

    /**
     * Agent 心跳
     */
    @PostMapping("/heartbeat")
    public ApiResponse<AgentDto.HeartbeatResponse> heartbeat(@Valid @RequestBody AgentDto.HeartbeatRequest request) {
        log.debug("收到 Agent 心跳: agentId={}", request.getAgentId());

        agentService.heartbeat(request);

        AgentDto.HeartbeatResponse response = new AgentDto.HeartbeatResponse();
        response.setMessage("ok");
        return ApiResponse.success(response);
    }

    /**
     * 批量上传照片索引
     */
    @PostMapping("/photos/batch")
    public ApiResponse<AgentDto.BatchPhotosResponse> batchUploadPhotos(
            @Valid @RequestBody AgentDto.BatchPhotosRequest request) {
        log.info("收到照片索引上传: agentId={}, count={}", request.getAgentId(),
                request.getPhotos() != null ? request.getPhotos().size() : 0);

        List<AgentDto.PhotoUploadResult> results = photoService.batchUploadPhotos(
                request.getAgentId(),
                request.getPhotos()
        );

        AgentDto.BatchPhotosResponse response = new AgentDto.BatchPhotosResponse();
        response.setResults(results);
        return ApiResponse.success(response);
    }

    /**
     * 申请 COS 上传地址
     */
    @PostMapping("/assets/upload-ticket")
    public ApiResponse<AgentDto.UploadTicketResponse> getUploadTicket(
            @Valid @RequestBody AgentDto.UploadTicketRequest request) {
        log.info("申请上传地址: agentId={}, photoId={}, assetType={}",
                request.getAgentId(), request.getPhotoId(), request.getAssetType());

        AgentDto.UploadTicketResponse ticket = cosService.generateUploadTicket(
                request.getAgentId(),
                request.getPhotoId(),
                request.getAssetType(),
                request.getContentType()
        );

        return ApiResponse.success(ticket);
    }

    /**
     * 通知资源上传完成
     */
    @PostMapping("/assets/upload-complete")
    public ApiResponse<AgentDto.UploadCompleteResponse> uploadComplete(
            @Valid @RequestBody AgentDto.UploadCompleteRequest request) {
        log.info("上传完成通知: agentId={}, photoId={}, assetType={}",
                request.getAgentId(), request.getPhotoId(), request.getAssetType());

        var asset = photoService.createOrUpdateAsset(
                request.getPhotoId(),
                request.getAssetType(),
                request.getStorageProvider(),
                cosService.getBucket(),
                cosService.getRegion(),
                request.getStorageKey(),
                request.getFileSize(),
                request.getWidth(),
                request.getHeight()
        );

        AgentDto.UploadCompleteResponse response = new AgentDto.UploadCompleteResponse();
        response.setAssetId(asset.getId().toString());
        return ApiResponse.success(response);
    }
}
