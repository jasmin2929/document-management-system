package com.dms.rest_api.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import lombok.*;

import java.util.ArrayList;
import java.util.List;

/**
 * Represents a Category entity stored in the PostgreSQL database.
 * 
 * Used to organize and categorize documents (e.g., "Invoices", "Contracts").
 * Demonstrates an ORM One-to-Many relationship with the {@link Document} entity.
 */
@Entity
@Table(name = "categories") // Defines the exact table name in the PostgreSQL database
@Data                       // Lombok: Automatically generates getters, setters, toString(), equals(), and hashCode()
@NoArgsConstructor          // Lombok: Generates a no-argument constructor (REQUIRED by JPA/Hibernate)
@AllArgsConstructor         // Lombok: Generates a constructor with parameters for all fields
@Builder                    // Lombok: Enables the Builder pattern for clean and fluent object creation
public class Category {

    /**
     * Primary Key for the table.
     * 
     * @Id marks this field as the unique identifier.
     * @GeneratedValue specifies that the database automatically increments this value.
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Unique name of the category (e.g., "Invoices", "Contracts").
     */
    @Column(nullable = false, unique = true)
    private String name;

    /**
     * List of documents associated with this category.
     * 
     * - mappedBy = "category": Specifies that the Document entity owns the foreign key.
     * - cascade = CascadeType.ALL: Automatically propagates persist/remove operations to child documents.
     * - orphanRemoval = true: Ensures orphaned documents are deleted from the database.
     * - @JsonIgnoreProperties("category"): Prevents infinite recursion loops during JSON serialization.
     */
    @OneToMany(mappedBy = "category", cascade = CascadeType.ALL, orphanRemoval = true)
    @JsonIgnoreProperties("category")
    @Builder.Default
    private List<Document> documents = new ArrayList<>();
}