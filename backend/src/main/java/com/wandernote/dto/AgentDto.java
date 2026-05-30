package com.wandernote.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Agent 相关 DTO
 */
public class AgentDto {

    @Data
    public static class HeartbeatRequest {
        @NotBlank(message = "agentId 不能为空")
        private String agentId;

        private String version;
        private String status;
        private String lastScanAt;
        private String lastSyncAt;
        private Integer photoCount;
        private Integer gpsPhotoCount;
        private Integer thumbSyncedCount;
        private Integer previewSyncedCount;
        private Integer failedCount;
    }

    @Data
    public static class HeartbeatResponse {
        private String message;
    }

    @Data
    public static class SyncStatusResponse {
        private Boolean agentOnline;
        private String agentId;
        private String agentVersion;
        private LocalDateTime lastHeartbeatAt;
        private LocalDateTime lastScanAt;
        private LocalDateTime lastSyncAt;
        private Integer photoCount;
        private Integer gpsPhotoCount;
        private Double gpsCoverageRate;
        private Integer thumbSyncedCount;
        private Integer previewSyncedCount;
        private Integer failedCount;
        private Integer pendingThumbCount;
        private Integer pendingPreviewCount;
    }

    @Data
    public static class PhotoIndexItem {
        @NotBlank(message = "localPhotoId 不能为空")
        private String localPhotoId;

        private String relativePath;
        private String fileName;
        private Long fileSize;
        private String contentHash;
        private String mtime;
        private String takenAt;
        private Double lat;
        private Double lng;
        private Integer width;
        private Integer height;
        private Boolean hasGps;
    }

    @Data
    public static class BatchPhotosRequest {
        @NotBlank(message = "agentId 不能为空")
        private String agentId;

        private List<PhotoIndexItem> photos;
    }

    @Data
    public static class PhotoUploadResult {
        private String localPhotoId;
        private String photoId;
        private Boolean needThumb;
        private Boolean needPreview;
    }

    @Data
    public static class BatchPhotosResponse {
        private List<PhotoUploadResult> results;
    }

    @Data
    public static class UploadTicketRequest {
        @NotBlank(message = "agentId 不能为空")
        private String agentId;

        @NotBlank(message = "photoId 不能为空")
        private String photoId;

        @NotBlank(message = "assetType 不能为空")
        private String assetType;

        private String contentType;
        private Long fileSize;
        private Integer width;
        private Integer height;
    }

    @Data
    public static class UploadTicketResponse {
        private String storageProvider;
        private String bucket;
        private String region;
        private String storageKey;
        private String uploadUrl;
        private Integer expiresIn;
    }

    @Data
    public static class UploadCompleteRequest {
        @NotBlank(message = "agentId 不能为空")
        private String agentId;

        @NotBlank(message = "photoId 不能为空")
        private String photoId;

        @NotBlank(message = "assetType 不能为空")
        private String assetType;

        private String storageProvider;
        private String storageKey;
        private Long fileSize;
        private Integer width;
        private Integer height;
    }

    @Data
    public static class UploadCompleteResponse {
        private String assetId;
    }
}
