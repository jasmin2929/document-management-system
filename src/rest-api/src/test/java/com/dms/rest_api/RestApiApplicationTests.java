package com.dms.rest_api;

import org.junit.jupiter.api.Test;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import software.amazon.awssdk.services.s3.S3Client;

@SpringBootTest
@ActiveProfiles("test")
class RestApiApplicationTests {

	// RabbitMQ and RustFS are not running during tests, so their clients are replaced by mocks
	@MockitoBean
	private RabbitTemplate rabbitTemplate;

	@MockitoBean
	private S3Client s3Client;

	@Test
	void contextLoads() {
	}

}
