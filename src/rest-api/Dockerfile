FROM maven:3.9-eclipse-temurin-25-alpine AS builder
WORKDIR /app
COPY pom.xml .
COPY src ./src
# -e prints the stack trace on failure; ls fails the step right here if no jar was produced
RUN mvn -B -e clean package -DskipTests \
 && ls -la target/*.jar

FROM eclipse-temurin:25-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/rest-api-0.0.1-SNAPSHOT.jar ./app.jar
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
