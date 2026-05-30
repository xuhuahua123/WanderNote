package com.wandernote.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.wandernote.dto.AgentDto;
import com.wandernote.entity.Photo;
import com.wandernote.entity.PhotoAsset;
import com.wandernote.mapper.PhotoAssetMapper;
import com.wandernote.mapper.PhotoMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;

/**
 * 照片服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PhotoService {

    private final PhotoMapper photoMapper;
    private final PhotoAssetMapper photoAssetMapper;

    /**
     * 解析时间字符串，支持多种格式
     */
    private LocalDateTime parseDateTime(String dateTimeStr) {
        if (dateTimeStr == null || dateTimeStr.isEmpty()) {
            return null;
        }
        try {
            // 尝试解析带时区的时间格式
            OffsetDateTime offsetDateTime = OffsetDateTime.parse(dateTimeStr);
            return offsetDateTime.toLocalDateTime();
        } catch (DateTimeParseException e1) {
            try {
                // 尝试解析 ISO_LOCAL_DATE_TIME 格式
                return LocalDateTime.parse(dateTimeStr);
            } catch (DateTimeParseException e2) {
                log.warn("无法解析时间: {}", dateTimeStr);
                return null;
            }
        }
    }

    /**
     * 批量上传照片索引
     */
    @Transactional
    public List<AgentDto.PhotoUploadResult> batchUploadPhotos(String agentId, List<AgentDto.PhotoIndexItem> photos) {
        List<AgentDto.PhotoUploadResult> results = new ArrayList<>();

        for (AgentDto.PhotoIndexItem item : photos) {
            AgentDto.PhotoUploadResult result = new AgentDto.PhotoUploadResult();
            result.setLocalPhotoId(item.getLocalPhotoId());

            try {
                // 查找是否已存在
                Photo existingPhoto = photoMapper.selectOne(
                        new LambdaQueryWrapper<Photo>()
                                .eq(Photo::getAgentId, agentId)
                                .eq(Photo::getLocalPhotoId, item.getLocalPhotoId())
                );

                Photo photo;
                if (existingPhoto != null) {
                    // 更新现有记录
                    photo = existingPhoto;
                    updatePhotoFromItem(photo, item);
                    photoMapper.updateById(photo);
                    log.debug("更新照片索引: agentId={}, localPhotoId={}", agentId, item.getLocalPhotoId());
                } else {
                    // 创建新记录
                    photo = new Photo();
                    photo.setAgentId(agentId);
                    photo.setLocalPhotoId(item.getLocalPhotoId());
                    updatePhotoFromItem(photo, item);
                    photo.setSyncStatus("indexed");
                    photoMapper.insert(photo);
                    log.debug("创建照片索引: agentId={}, localPhotoId={}, photoId={}", agentId, item.getLocalPhotoId(), photo.getId());
                }

                result.setPhotoId(photo.getId().toString());

                // 检查是否需要上传缩略图和预览图
                boolean needThumb = !hasAsset(photo.getId(), "thumb");
                boolean needPreview = !hasAsset(photo.getId(), "preview");

                result.setNeedThumb(needThumb);
                result.setNeedPreview(needPreview);

            } catch (Exception e) {
                log.error("处理照片索引失败: agentId={}, localPhotoId={}", agentId, item.getLocalPhotoId(), e);
                result.setPhotoId(null);
                result.setNeedThumb(false);
                result.setNeedPreview(false);
            }

            results.add(result);
        }

        return results;
    }

    private void updatePhotoFromItem(Photo photo, AgentDto.PhotoIndexItem item) {
        photo.setRelativePath(item.getRelativePath());
        photo.setFileName(item.getFileName());
        photo.setFileSize(item.getFileSize());
        photo.setContentHash(item.getContentHash());
        // 解析时间字符串
        if (item.getMtime() != null) {
            photo.setMtime(parseDateTime(item.getMtime()));
        }
        if (item.getTakenAt() != null) {
            photo.setTakenAt(parseDateTime(item.getTakenAt()));
        }
        if (item.getLat() != null) {
            photo.setLat(BigDecimal.valueOf(item.getLat()));
        }
        if (item.getLng() != null) {
            photo.setLng(BigDecimal.valueOf(item.getLng()));
        }
        photo.setWidth(item.getWidth());
        photo.setHeight(item.getHeight());
        photo.setHasGps(item.getHasGps() != null ? item.getHasGps() : false);
    }

    private boolean hasAsset(Long photoId, String assetType) {
        return photoAssetMapper.selectCount(
                new LambdaQueryWrapper<PhotoAsset>()
                        .eq(PhotoAsset::getPhotoId, photoId)
                        .eq(PhotoAsset::getAssetType, assetType)
                        .eq(PhotoAsset::getSyncStatus, "completed")
        ) > 0;
    }

    /**
     * 获取照片
     */
    public Photo getPhoto(Long photoId) {
        return photoMapper.selectById(photoId);
    }

    /**
     * 根据 ID 字符串获取照片
     */
    public Photo getPhoto(String photoIdStr) {
        try {
            Long photoId = Long.parseLong(photoIdStr);
            return getPhoto(photoId);
        } catch (NumberFormatException e) {
            return null;
        }
    }

    /**
     * 创建或更新照片资源
     * @param photoIdStr photoId 字符串（可以是数据库 ID 或 localPhotoId）
     */
    @Transactional
    public PhotoAsset createOrUpdateAsset(String photoIdStr, String assetType, String storageProvider,
                                          String bucket, String region, String storageKey,
                                          Long fileSize, Integer width, Integer height) {
        // 尝试解析 photoId
        Long photoId = null;
        try {
            photoId = Long.parseLong(photoIdStr);
        } catch (NumberFormatException e) {
            // 如果不是数字，可能是 localPhotoId，需要查找对应的 photo 记录
            Photo photo = photoMapper.selectOne(
                    new LambdaQueryWrapper<Photo>()
                            .eq(Photo::getLocalPhotoId, photoIdStr)
                            .last("LIMIT 1")
            );
            if (photo != null) {
                photoId = photo.getId();
                log.debug("通过 localPhotoId 找到 photoId: {} -> {}", photoIdStr, photoId);
            } else {
                log.warn("找不到 photoId 对应的照片记录: {}", photoIdStr);
                throw new RuntimeException("找不到照片记录: " + photoIdStr);
            }
        }

        PhotoAsset asset = photoAssetMapper.selectOne(
                new LambdaQueryWrapper<PhotoAsset>()
                        .eq(PhotoAsset::getPhotoId, photoId)
                        .eq(PhotoAsset::getAssetType, assetType)
        );

        if (asset == null) {
            asset = new PhotoAsset();
            asset.setPhotoId(photoId);
            asset.setAssetType(assetType);
        }

        asset.setStorageProvider(storageProvider);
        asset.setBucket(bucket);
        asset.setRegion(region);
        asset.setStorageKey(storageKey);
        asset.setFileSize(fileSize);
        asset.setWidth(width);
        asset.setHeight(height);
        asset.setSyncStatus("completed");

        if (asset.getId() == null) {
            photoAssetMapper.insert(asset);
        } else {
            photoAssetMapper.updateById(asset);
        }

        return asset;
    }
}
