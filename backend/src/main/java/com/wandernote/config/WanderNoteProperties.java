package com.wandernote.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * WanderNote 应用配置属性
 */
@Data
@Component
@ConfigurationProperties(prefix = "wandernote")
public class WanderNoteProperties {

    /**
     * 访问码
     */
    private String accessCode;

    /**
     * Agent Token
     */
    private String agentToken;

    /**
     * 腾讯地图配置
     */
    private TencentMapConfig tencent = new TencentMapConfig();

    /**
     * COS 配置
     */
    private CosConfig cos = new CosConfig();

    /**
     * MiMo AI 配置
     */
    private MimoConfig mimo = new MimoConfig();

    @Data
    public static class TencentMapConfig {
        private MapConfig map = new MapConfig();

        @Data
        public static class MapConfig {
            private String key;
        }
    }

    @Data
    public static class CosConfig {
        private String region;
        private String bucket;
        private String secretId;
        private String secretKey;
        private int uploadUrlTtlSeconds = 600;
        private int downloadUrlTtlSeconds = 900;
    }

    @Data
    public static class MimoConfig {
        private String apiBaseUrl;
        private String apiKey;
        private String model = "mimo-v2.5";
    }
}
