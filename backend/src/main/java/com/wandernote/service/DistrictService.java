package com.wandernote.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.wandernote.config.WanderNoteProperties;
import com.wandernote.entity.District;
import com.wandernote.mapper.DistrictMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

/**
 * 行政区划服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DistrictService {

    private final WanderNoteProperties properties;
    private final DistrictMapper districtMapper;
    private final ObjectMapper objectMapper;
    private final RestTemplate restTemplate = new RestTemplate();

    private static final String TENCENT_DISTRICT_API = "https://apis.map.qq.com/ws/district/v1/list";

    /**
     * 从腾讯地图初始化行政区划数据
     */
    @Transactional
    public void initFromTencentMap() {
        String mapKey = properties.getTencent().getMap().getKey();
        if (mapKey == null || mapKey.isEmpty()) {
            log.warn("腾讯地图 Key 未配置，跳过行政区划初始化");
            return;
        }

        String url = TENCENT_DISTRICT_API + "?key=" + mapKey + "&struct_type=1";

        try {
            log.info("开始从腾讯地图拉取行政区划数据...");
            String response = restTemplate.getForObject(url, String.class);
            JsonNode root = objectMapper.readTree(response);

            int status = root.path("status").asInt();
            if (status != 0) {
                String message = root.path("message").asText();
                log.error("腾讯地图 API 返回错误: status={}, message={}", status, message);
                throw new RuntimeException("腾讯地图 API 错误: " + message);
            }

            JsonNode result = root.path("result");
            JsonNode districtList = result.isArray() && result.size() > 0 ? result.get(0) : result;

            List<District> districts = new ArrayList<>();
            parseDistrictsRecursive(districtList, null, null, null, districts);

            // 清空旧数据
            districtMapper.delete(new LambdaQueryWrapper<>());

            // 批量插入
            for (District district : districts) {
                districtMapper.insert(district);
            }

            log.info("行政区划初始化完成，共 {} 条记录", districts.size());

        } catch (Exception e) {
            log.error("从腾讯地图拉取行政区划数据失败", e);
            throw new RuntimeException("行政区划初始化失败: " + e.getMessage(), e);
        }
    }

    private void parseDistrictsRecursive(JsonNode node, String parentAdcode,
                                         String provinceAdcode, String provinceName,
                                         List<District> districts) {
        if (node == null || !node.isArray()) {
            return;
        }

        for (JsonNode item : node) {
            String adcode = item.path("adcode").asText();
            String name = item.path("name").asText();
            String fullName = item.path("fullname").asText(name);
            String level = item.path("level").asText();

            District district = new District();
            district.setAdcode(adcode);
            district.setName(name);
            district.setFullName(fullName);
            district.setLevel(level);
            district.setParentAdcode(parentAdcode);
            district.setSource("tencent");

            // 解析坐标
            JsonNode location = item.path("location");
            if (location != null && !location.isMissingNode()) {
                district.setLat(new BigDecimal(location.path("lat").asText("0")));
                district.setLng(new BigDecimal(location.path("lng").asText("0")));
            }

            // 设置省份信息
            if ("province".equals(level)) {
                district.setProvinceAdcode(adcode);
                district.setProvinceName(name);
                provinceAdcode = adcode;
                provinceName = name;
            } else {
                district.setProvinceAdcode(provinceAdcode);
                district.setProvinceName(provinceName);
            }

            // 设置城市信息
            if ("city".equals(level) || "district".equals(level)) {
                if (parentAdcode != null && !parentAdcode.equals(provinceAdcode)) {
                    district.setCityAdcode(parentAdcode);
                    // 尝试获取城市名称
                    district.setCityName(findCityName(node, parentAdcode));
                }
            }

            districts.add(district);

            // 递归处理子节点
            JsonNode children = item.path("c");
            if (children != null && !children.isMissingNode() && children.isArray()) {
                String currentAdcode = adcode;
                parseDistrictsRecursive(children, currentAdcode, provinceAdcode, provinceName, districts);
            }
        }
    }

    private String findCityName(JsonNode siblings, String cityAdcode) {
        if (siblings == null || cityAdcode == null) {
            return null;
        }
        for (JsonNode sibling : siblings) {
            if (cityAdcode.equals(sibling.path("adcode").asText())) {
                return sibling.path("name").asText();
            }
        }
        return null;
    }

    /**
     * 检查行政区划是否已初始化
     */
    public boolean isInitialized() {
        return districtMapper.selectCount(new LambdaQueryWrapper<>()) > 0;
    }
}
