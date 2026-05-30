package com.wandernote.service;

import com.qcloud.cos.COSClient;
import com.qcloud.cos.auth.BasicCOSCredentials;
import com.qcloud.cos.auth.COSCredentials;
import com.qcloud.cos.http.HttpMethodName;
import com.qcloud.cos.model.GeneratePresignedUrlRequest;
import com.wandernote.config.WanderNoteProperties;
import com.wandernote.dto.AgentDto;
import com.wandernote.entity.Photo;
import com.wandernote.entity.PhotoAsset;
import com.wandernote.mapper.PhotoAssetMapper;
import com.wandernote.mapper.PhotoMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.URL;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * 腾讯 COS 服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CosService {

    private final WanderNoteProperties properties;
    private final PhotoMapper photoMapper;
    private final PhotoAssetMapper photoAssetMapper;

    private COSClient cosClient;

    private COSClient getCosClient() {
        if (cosClient == null) {
            WanderNoteProperties.CosConfig cosConfig = properties.getCos();
            COSCredentials cred = new BasicCOSCredentials(
                    cosConfig.getSecretId(),
                    cosConfig.getSecretKey()
            );
            com.qcloud.cos.ClientConfig clientConfig = new com.qcloud.cos.ClientConfig(
                    new com.qcloud.cos.region.Region(cosConfig.getRegion())
            );
            cosClient = new COSClient(cred, clientConfig);
        }
        return cosClient;
    }

    public String getBucket() {
        return properties.getCos().getBucket();
    }

    public String getRegion() {
        return properties.getCos().getRegion();
    }

    /**
     * 生成上传凭证
     */
    public AgentDto.UploadTicketResponse generateUploadTicket(String agentId, String photoId, String assetType, String contentType) {
        WanderNoteProperties.CosConfig cosConfig = properties.getCos();

        // 生成存储路径
        LocalDate now = LocalDate.now();
        String year = String.valueOf(now.getYear());
        String month = String.format("%02d", now.getMonthValue());

        String folder = assetType.equals("thumb") ? "thumbs" : "previews";
        String storageKey = String.format("%s/%s/%s/%s/%s.webp", folder, agentId, year, month, photoId);

        // 生成预签名上传 URL
        GeneratePresignedUrlRequest request = new GeneratePresignedUrlRequest(
                cosConfig.getBucket(),
                storageKey,
                HttpMethodName.PUT
        );

        if (contentType != null) {
            request.setContentType(contentType);
        }

        Date expiration = new Date(System.currentTimeMillis() +
                TimeUnit.SECONDS.toMillis(cosConfig.getUploadUrlTtlSeconds()));
        request.setExpiration(expiration);

        URL uploadUrl = getCosClient().generatePresignedUrl(request);

        AgentDto.UploadTicketResponse response = new AgentDto.UploadTicketResponse();
        response.setStorageProvider("cos");
        response.setBucket(cosConfig.getBucket());
        response.setRegion(cosConfig.getRegion());
        response.setStorageKey(storageKey);
        response.setUploadUrl(uploadUrl.toString());
        response.setExpiresIn(cosConfig.getUploadUrlTtlSeconds());

        log.debug("生成上传凭证: storageKey={}, expiresIn={}", storageKey, cosConfig.getUploadUrlTtlSeconds());

        return response;
    }

    /**
     * 生成短期下载 URL
     */
    public String generateDownloadUrl(String storageKey) {
        WanderNoteProperties.CosConfig cosConfig = properties.getCos();

        GeneratePresignedUrlRequest request = new GeneratePresignedUrlRequest(
                cosConfig.getBucket(),
                storageKey,
                HttpMethodName.GET
        );

        Date expiration = new Date(System.currentTimeMillis() +
                TimeUnit.SECONDS.toMillis(cosConfig.getDownloadUrlTtlSeconds()));
        request.setExpiration(expiration);

        URL downloadUrl = getCosClient().generatePresignedUrl(request);
        return downloadUrl.toString();
    }

    /**
     * 批量生成短期下载 URL
     */
    public Map<String, String> batchGenerateDownloadUrls(List<String> storageKeys) {
        Map<String, String> result = new HashMap<>();
        for (String storageKey : storageKeys) {
            result.put(storageKey, generateDownloadUrl(storageKey));
        }
        return result;
    }

    /**
     * 获取照片的短期下载 URL
     */
    public String getPhotoDownloadUrl(Long photoId, String assetType) {
        PhotoAsset asset = photoAssetMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<PhotoAsset>()
                        .eq(PhotoAsset::getPhotoId, photoId)
                        .eq(PhotoAsset::getAssetType, assetType)
                        .eq(PhotoAsset::getSyncStatus, "completed")
        );

        if (asset == null || asset.getStorageKey() == null) {
            return null;
        }

        return generateDownloadUrl(asset.getStorageKey());
    }

    /**
     * 批量获取照片的短期下载 URL
     */
    public Map<Long, String> batchGetPhotoDownloadUrls(List<Long> photoIds, String assetType) {
        List<PhotoAsset> assets = photoAssetMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<PhotoAsset>()
                        .in(PhotoAsset::getPhotoId, photoIds)
                        .eq(PhotoAsset::getAssetType, assetType)
                        .eq(PhotoAsset::getSyncStatus, "completed")
        );

        Map<Long, String> result = new HashMap<>();
        for (PhotoAsset asset : assets) {
            if (asset.getStorageKey() != null) {
                result.put(asset.getPhotoId(), generateDownloadUrl(asset.getStorageKey()));
            }
        }
        return result;
    }
}
