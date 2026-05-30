package com.wandernote.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.wandernote.common.ApiResponse;
import com.wandernote.entity.District;
import com.wandernote.mapper.DistrictMapper;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 行政区划控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/districts")
@RequiredArgsConstructor
public class DistrictController {

    private final DistrictMapper districtMapper;

    /**
     * 获取省份列表
     */
    @GetMapping("/provinces")
    public ApiResponse<ProvincesResponse> getProvinces() {
        List<District> provinces = districtMapper.selectList(
                new LambdaQueryWrapper<District>()
                        .eq(District::getLevel, "province")
                        .orderByAsc(District::getAdcode)
        );

        List<ProvinceDto> provinceDtos = provinces.stream()
                .map(p -> {
                    ProvinceDto dto = new ProvinceDto();
                    dto.setAdcode(p.getAdcode());
                    dto.setName(p.getName());
                    return dto;
                })
                .collect(Collectors.toList());

        ProvincesResponse response = new ProvincesResponse();
        response.setProvinces(provinceDtos);
        return ApiResponse.success(response);
    }

    /**
     * 获取城市/地区列表
     */
    @GetMapping("/provinces/{provinceAdcode}/cities")
    public ApiResponse<CitiesResponse> getCities(@PathVariable String provinceAdcode) {
        List<District> cities = districtMapper.selectList(
                new LambdaQueryWrapper<District>()
                        .eq(District::getProvinceAdcode, provinceAdcode)
                        .eq(District::getLevel, "city")
                        .orderByAsc(District::getAdcode)
        );

        List<CityDto> cityDtos = cities.stream()
                .map(c -> {
                    CityDto dto = new CityDto();
                    dto.setAdcode(c.getAdcode());
                    dto.setName(c.getName());
                    return dto;
                })
                .collect(Collectors.toList());

        CitiesResponse response = new CitiesResponse();
        response.setCities(cityDtos);
        return ApiResponse.success(response);
    }

    @Data
    public static class ProvincesResponse {
        private List<ProvinceDto> provinces;
    }

    @Data
    public static class ProvinceDto {
        private String adcode;
        private String name;
    }

    @Data
    public static class CitiesResponse {
        private List<CityDto> cities;
    }

    @Data
    public static class CityDto {
        private String adcode;
        private String name;
    }
}
