package com.dms.rest_api.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.AmqpException;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.connection.Connection;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Slf4j
@Configuration
public class RabbitConfig {

    public static final String OCR_QUEUE = "ocr-queue";

    @Bean
    public Queue ocrQueue() {
        return new Queue(OCR_QUEUE, true);
    }

    @Bean
    public MessageConverter jsonMessageConverter(ObjectMapper objectMapper) {
        return new Jackson2JsonMessageConverter(objectMapper);
    }

    @Bean
    public ApplicationRunner declareQueuesOnStartup(ObjectProvider<ConnectionFactory> connectionFactory) {
        return args -> connectionFactory.ifAvailable(factory -> {
            try (Connection ignored = factory.createConnection()) {
                log.info("Connected to RabbitMQ, declared queue '{}'", OCR_QUEUE);
            } catch (AmqpException e) {
                log.warn("RabbitMQ not reachable at startup, queues will be declared on first use: {}", e.getMessage());
            }
        });
    }
}
