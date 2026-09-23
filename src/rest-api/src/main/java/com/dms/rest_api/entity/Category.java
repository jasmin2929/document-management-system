package com.dms.rest_api.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.ArrayList;
import java.util.List;

/**
 * Entity representing a category used to classify documents within the system.
 */
@Entity
@Table(name = "categories")
@Getter
@Setter
// Exclude bidirectional collection from Lombok toString and equals/hashCode to prevent StackOverflowError
@ToString(exclude = "documents")
@EqualsAndHashCode(exclude = "documents")
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Category {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String name;

    /**
     * One-To-Many relationship to documents associated with this category.
     * Cascades operations and sets initial empty list to prevent NullPointerExceptions.
     */
    @OneToMany(mappedBy = "category", cascade = CascadeType.ALL)
    @Builder.Default
    private List<Document> documents = new ArrayList<>();
}