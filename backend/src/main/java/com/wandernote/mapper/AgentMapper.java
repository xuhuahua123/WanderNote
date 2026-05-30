package com.wandernote.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.wandernote.entity.Agent;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AgentMapper extends BaseMapper<Agent> {
}
