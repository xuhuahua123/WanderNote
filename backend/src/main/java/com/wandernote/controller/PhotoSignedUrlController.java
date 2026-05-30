package com.wandernote.controller;

import com.wandernote.common.ApiResponse;
import com.wandernote.service.CosService;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 照片签名 URL 控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/photos")
@RequiredArgsConstructor
public class PhotoSignedUrlController {

    private final CosService cosService;

    /**
     * 批量获取签名下载 URL
     */
    @PostMapping("/signed-urls")
    public ApiResponse<SignedUrlsResponse> getSignedUrls(@RequestBody SignedUrlsRequest request) {
        log.debug("获取签名URL: photoIds={}, assetType={}", request.getPhotoIds(), request.getAssetType());

        List<Long> photoIds = request.getPhotoIds().stream()
                .map(Long::parseLong)
                .collect(Collectors.toList());

        Map<Long, String> urlMap = cosService.batchGetPhotoDownloadUrls(photoIds, request.getAssetType());

        List<SignedUrlItem> items = request.getPhotoIds().stream()
                .map(photoIdStr -> {
                    Long photoId = Long.parseLong(photoIdStr);
                    String url = urlMap.get(photoId);

                    SignedUrlItem item = new SignedUrlItem();
                    item.setPhotoId(photoIdStr);
                    item.setAssetType(request.getAssetType());
                    item.setUrl(url);
                    item.setExpiresIn(900);
                    return item;
                })
                .collect(Collectors.toList());

        SignedUrlsResponse response = new SignedUrlsResponse();
        response.setUrls(items);
        return ApiResponse.success(response);
    }

    @Data
    public static class SignedUrlsRequest {
        private List<String> photoIds;
        private String assetType = "thumb";
    }

    @Data
    public static class SignedUrlsResponse {
        private List<SignedUrlItem> urls;
    }

    @Data
    public static class SignedUrlItem {
        private String photoId;
        private String assetType;
        private String url;
        private Integer expiresIn;
    }
}
