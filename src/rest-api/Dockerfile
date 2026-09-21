# 1. Build-Phase: JDK 25 auf Debian/Ubuntu Basis
FROM maven:3.9-eclipse-temurin-25 AS builder
WORKDIR /app

# Copy and download dependencies
COPY pom.xml .
RUN mvn dependency:go-offline

# Copy source code and build JAR
COPY src ./src
RUN mvn clean package -DskipTests

# 2. Runtime-Phase: JRE 25 auf Debian/Ubuntu Basis
FROM eclipse-temurin:25-jre
WORKDIR /app

# Copy the built JAR from the build phase
COPY --from=builder /app/target/*.jar app.jar

# Expose the port of the REST server
EXPOSE 8081

# Start the server
ENTRYPOINT ["java", "-jar", "app.jar"]