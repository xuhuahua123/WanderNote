package com.wandernote.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;

/**
 * 行政区划表
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("district")
public class District extends BaseEntity {

    /**
     * 行政区划代码
     */
    private String adcode;

    /**
     * 名称
     */
    private String name;

    /**
     * 全称
     */
    private String fullName;

    /**
     * 级别: province, city, district
     */
    private String level;

    /**
     * 父级 adcode
     */
    private String parentAdcode;

    /**
     * 所属省份 adcode
     */
    private String provinceAdcode;

    /**
     * 所属省份名称
     */
    private String provinceName;

    /**
     * 所属城市 adcode
     */
    private String cityAdcode;

    /**
     * 所属城市名称
     */
    private String cityName;

    /**
     * 纬度
     */
    private BigDecimal lat;

    /**
     * 经度
     */
    private BigDecimal lng;

    /**
     * 数据来源
     */
    private String source;
}
