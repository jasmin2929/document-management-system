# ---------- Build stage: JDK 25 + Maven ----------
FROM maven:3.9-eclipse-temurin-25-alpine AS builder
WORKDIR /app

COPY pom.xml .
COPY src ./src
# -e prints the stack trace on failure; the ls makes the step fail
# right here (with a readable message) if no jar was produced
RUN mvn -B -e clean package -DskipTests \
 && ls -la target/*.jar

# ---------- Runtime stage: JRE 25 ----------
FROM eclipse-temurin:25-jre-alpine
WORKDIR /app

# Copy the built JAR from the build phase
COPY --from=builder /app/target/rest-api-0.0.1-SNAPSHOT.jar ./app.jar

# Expose the port of the REST server
EXPOSE 8081

# Start the server
ENTRYPOINT ["java", "-jar", "app.jar"]
