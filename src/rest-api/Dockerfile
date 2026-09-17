# 1. Build-Phase: Use Maven with JDK 25
FROM maven:3.9-eclipse-temurin-25 AS builder
WORKDIR /app

# Copy and download dependencies (for Caching-Optimizing)
COPY pom.xml .
RUN mvn dependency:go-offline

# Copy source code and build JAR
COPY src ./src
RUN mvn clean package -DskipTests

# 2. Runtime-Phase: Thin JDK 25 image for execution
FROM eclipse-temurin:25-jre-alpine
WORKDIR /app

# Copy the built JAR from the build phase
COPY --from=builder /app/target/*.jar app.jar

# Expose the port of the REST server
EXPOSE 8081

# Start the server
ENTRYPOINT ["java", "-jar", "app.jar"]