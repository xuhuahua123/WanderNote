package com.wandernote.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.LocalDateTime;

/**
 * Photo-Agent 状态表
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("agent")
public class Agent extends BaseEntity {

    /**
     * Agent 唯一标识，如 home-mac-001
     */
    private String agentId;

    /**
     * Agent 名称
     */
    private String name;

    /**
     * Agent 版本
     */
    private String version;

    /**
     * Agent 状态: idle, scanning, syncing
     */
    private String status;

    /**
     * 最近心跳时间
     */
    private LocalDateTime lastHeartbeatAt;

    /**
     * 最近扫描时间
     */
    private LocalDateTime lastScanAt;

    /**
     * 最近同步时间
     */
    private LocalDateTime lastSyncAt;

    /**
     * 照片总数
     */
    private Integer photoCount;

    /**
     * 有 GPS 的照片数量
     */
    private Integer gpsPhotoCount;

    /**
     * 缩略图已同步数量
     */
    private Integer thumbSyncedCount;

    /**
     * 预览图已同步数量
     */
    private Integer previewSyncedCount;

    /**
     * 失败数量
     */
    private Integer failedCount;
}
