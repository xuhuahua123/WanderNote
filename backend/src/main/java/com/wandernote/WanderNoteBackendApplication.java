package com.wandernote;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.wandernote.mapper")
public class WanderNoteBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(WanderNoteBackendApplication.class, args);
    }
}