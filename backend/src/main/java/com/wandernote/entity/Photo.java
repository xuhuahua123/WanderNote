package com.wandernote.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 照片索引主表
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("photo")
public class Photo extends BaseEntity {

    /**
     * 所属 Agent ID
     */
    private String agentId;

    /**
     * 本地照片 ID，由 Agent 生成
     */
    private String localPhotoId;

    /**
     * 相对路径
     */
    private String relativePath;

    /**
     * 文件名
     */
    private String fileName;

    /**
     * 文件大小（字节）
     */
    private Long fileSize;

    /**
     * 内容哈希
     */
    private String contentHash;

    /**
     * 文件修改时间
     */
    private LocalDateTime mtime;

    /**
     * 拍摄时间
     */
    private LocalDateTime takenAt;

    /**
     * 纬度
     */
    private BigDecimal lat;

    /**
     * 经度
     */
    private BigDecimal lng;

    /**
     * 宽度
     */
    private Integer width;

    /**
     * 高度
     */
    private Integer height;

    /**
     * 是否有 GPS 信息
     */
    private Boolean hasGps;

    /**
     * 同步状态
     */
    private String syncStatus;

    /**
     * 最近错误信息
     */
    private String lastError;
}
