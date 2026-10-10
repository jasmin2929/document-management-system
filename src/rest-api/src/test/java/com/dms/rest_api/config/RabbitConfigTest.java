package com.dms.rest_api.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.amqp.AmqpConnectException;
import org.springframework.amqp.core.Message;
import org.springframework.amqp.core.MessageProperties;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.connection.Connection;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.support.StaticListableBeanFactory;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.DefaultApplicationArguments;

import java.net.ConnectException;
import java.nio.charset.StandardCharsets;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class RabbitConfigTest {

    private final RabbitConfig rabbitConfig = new RabbitConfig();

    @Test
    @DisplayName("ocrQueue() is durable so queued messages survive a broker restart")
    void ocrQueue_IsDurableWithExpectedName() {
        Queue queue = rabbitConfig.ocrQueue();

        assertThat(queue.getName()).isEqualTo(RabbitConfig.OCR_QUEUE);
        assertThat(queue.isDurable()).isTrue();
        assertThat(queue.isExclusive()).isFalse();
        assertThat(queue.isAutoDelete()).isFalse();
    }

    @Test
    @DisplayName("jsonMessageConverter() serializes payloads as JSON and reads them back")
    void jsonMessageConverter_RoundTripsJson() {
        MessageConverter converter = rabbitConfig.jsonMessageConverter(new ObjectMapper());

        Message message = converter.toMessage(Map.of("documentId", 7), new MessageProperties());

        assertThat(message.getMessageProperties().getContentType()).isEqualTo(MessageProperties.CONTENT_TYPE_JSON);
        assertThat(new String(message.getBody(), StandardCharsets.UTF_8)).isEqualTo("{\"documentId\":7}");
        assertThat(converter.fromMessage(message)).isEqualTo(Map.of("documentId", 7));
    }

    @Test
    @DisplayName("declareQueuesOnStartup() opens and closes a connection when RabbitMQ is configured")
    void declareQueuesOnStartup_OpensConnection() throws Exception {
        ConnectionFactory connectionFactory = mock(ConnectionFactory.class);
        Connection connection = mock(Connection.class);
        given(connectionFactory.createConnection()).willReturn(connection);

        runner(providerOf(connectionFactory)).run(new DefaultApplicationArguments());

        verify(connectionFactory).createConnection();
        verify(connection).close();
    }

    @Test
    @DisplayName("declareQueuesOnStartup() does not fail startup when RabbitMQ is unreachable")
    void declareQueuesOnStartup_BrokerDown_DoesNotThrow() {
        ConnectionFactory connectionFactory = mock(ConnectionFactory.class);
        given(connectionFactory.createConnection())
                .willThrow(new AmqpConnectException(new ConnectException("Connection refused")));

        ApplicationRunner runner = runner(providerOf(connectionFactory));

        assertThatCode(() -> runner.run(new DefaultApplicationArguments())).doesNotThrowAnyException();
        verify(connectionFactory).createConnection();
    }

    @Test
    @DisplayName("declareQueuesOnStartup() does nothing when RabbitMQ auto-configuration is excluded")
    void declareQueuesOnStartup_NoConnectionFactory_DoesNothing() {
        ApplicationRunner runner = runner(new StaticListableBeanFactory().getBeanProvider(ConnectionFactory.class));

        assertThatCode(() -> runner.run(new DefaultApplicationArguments())).doesNotThrowAnyException();
    }

    private ApplicationRunner runner(ObjectProvider<ConnectionFactory> provider) {
        return rabbitConfig.declareQueuesOnStartup(provider);
    }

    private static ObjectProvider<ConnectionFactory> providerOf(ConnectionFactory connectionFactory) {
        return new StaticListableBeanFactory(Map.of("connectionFactory", connectionFactory))
                .getBeanProvider(ConnectionFactory.class);
    }
}
