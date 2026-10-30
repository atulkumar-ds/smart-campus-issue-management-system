# Database Normalization Documentation (1NF, 2NF, 3NF)

## 1. Normalization Objectives
Database normalization reduces data redundancy and eliminates insertion, update, and deletion anomalies. The **Smart Campus Issue Management System** database is designed strictly in Third Normal Form (3NF).

---

## 2. First Normal Form (1NF)
### Definition
A relation is in 1NF if and only if:
1. Every attribute value is atomic (indivisible single scalar values).
2. There are no repeating groups or multi-valued arrays.
3. Each record is uniquely identifiable by a Primary Key.

### Implementation in Smart Campus
- **Comments and Attachments**: Rather than storing comma-separated file paths or a list of user remarks within the `issues` table, they are decomposed into distinct child tables: `comments` and `attachments`. Each row represents exactly one atomic comment or uploaded file.
- **Atomic Location Attributes**: Locations are broken down into discrete atomic attributes: `building_name`, `floor`, and `room_number` instead of a concatenated address string.
- **Single Values**: Contact information (`phone`, `email`), user roles, and category mappings contain single scalar values.

---

## 3. Second Normal Form (2NF)
### Definition
A relation is in 2NF if:
1. It is already in 1NF.
2. Every non-prime attribute is fully functionally dependent on the entire Primary Key (no partial dependencies on a composite candidate key).

### Implementation in Smart Campus
- All 12 tables employ **single-attribute surrogate Primary Keys** (e.g., `issue_id`, `user_id`, `category_id`, `assignment_id`).
- Because no primary key consists of a composite key, **partial functional dependencies are mathematically impossible**. Every non-key attribute depends entirely on the single primary key column.

---

## 4. Third Normal Form (3NF)
### Definition
A relation is in 3NF if:
1. It is already in 2NF.
2. There are no transitive dependencies (no non-prime attribute is functionally dependent on another non-prime attribute, i.e., $X \to Y$ and $Y \to Z$ where $X$ is the primary key).

### Implementation in Smart Campus
- **Departments & Categories**: In an un-normalized schema, an issue row might record `category_name`, `department_name`, and `department_head`. This introduces a transitive dependency: `issue_id -> category_id -> department_id -> head_user_id`. In our schema:
  - `issues` only holds `category_id`.
  - `issue_categories` holds `default_department_id`.
  - `departments` holds `head_user_id`.
- **SLA Hours**: Instead of storing `sla_hours` directly inside `issues` alongside `priority_name`, priority names and their SLA hours are stored in the lookup table `priority_levels`.
- **Lifecycle Status**: Status names and descriptions reside exclusively in `issue_status`, referenced via `status_id`.
- **Technician & Reporter Details**: Reporter profile details (name, email, phone) are referenced via foreign key `reported_by -> users.user_id`, never duplicated inside the `issues` table.

---

## 5. Functional Dependencies (FDs) for All 12 Tables

### 1. `departments`
- $department\_id \to department\_name, head\_user\_id, created\_at$
- $department\_name \to department\_id$ (Candidate Key)

### 2. `locations`
- $location\_id \to building\_name, floor, room\_number, location\_type, created\_at$
- $(building\_name, floor, room\_number) \to location\_id, location\_type, created\_at$ (Candidate Key)

### 3. `issue_categories`
- $category\_id \to category\_name, description, default\_department\_id, created\_at$
- $category\_name \to category\_id$ (Candidate Key)

### 4. `priority_levels`
- $priority\_id \to level\_name, sla\_hours, created\_at$
- $level\_name \to priority\_id$ (Candidate Key)

### 5. `issue_status`
- $status\_id \to status\_name, description$
- $status\_name \to status\_id$ (Candidate Key)

### 6. `users`
- $user\_id \to name, email, password\_hash, phone, role, department\_id, is\_active, created\_at$
- $email \to user\_id, name, password\_hash, phone, role, department\_id, is\_active, created\_at$ (Candidate Key)

### 7. `issues`
- $issue\_id \to title, description, reported\_by, category\_id, location\_id, priority\_id, status\_id, created\_at, updated\_at, resolved\_at$

### 8. `assignments`
- $assignment\_id \to issue\_id, assigned\_to, assigned\_by, assigned\_at, expected\_completion, completed\_at$

### 9. `issue_status_history`
- $history\_id \to issue\_id, old\_status\_id, new\_status\_id, changed\_by, changed\_at, remarks$

### 10. `comments`
- $comment\_id \to issue\_id, user\_id, comment\_text, created\_at$

### 11. `attachments`
- $attachment\_id \to issue\_id, file\_path, file\_type, uploaded\_by, uploaded\_at$

### 12. `feedback`
- $feedback\_id \to issue\_id, user\_id, rating, feedback\_text, submitted\_at$
- $issue\_id \to feedback\_id, user\_id, rating, feedback\_text, submitted\_at$ (Candidate Key due to 1:0..1 UNIQUE constraint)
