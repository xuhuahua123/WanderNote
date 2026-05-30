package com.wandernote.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 照片派生资源表
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("photo_asset")
public class PhotoAsset extends BaseEntity {

    /**
     * 关联的照片 ID
     */
    private Long photoId;

    /**
     * 资源类型: thumb, preview
     */
    private String assetType;

    /**
     * 存储提供商标识
     */
    private String storageProvider;

    /**
     * 存储桶
     */
    private String bucket;

    /**
     * 存储区域
     */
    private String region;

    /**
     * 存储键（路径）
     */
    private String storageKey;

    /**
     * 宽度
     */
    private Integer width;

    /**
     * 高度
     */
    private Integer height;

    /**
     * 文件大小
     */
    private Long fileSize;

    /**
     * 同步状态
     */
    private String syncStatus;
}
