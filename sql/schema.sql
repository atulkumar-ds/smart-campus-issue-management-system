-- =====================================================================
-- SMART CAMPUS ISSUE MANAGEMENT SYSTEM - DATABASE SCHEMA (MySQL 8.0)
-- B.Tech DBMS Project
-- Satisfies 1NF, 2NF, 3NF with exactly 12 core tables.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS smart_campus CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_campus;

-- Temporarily disable foreign key checks for clean teardown/rebuild
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS attachments;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS issue_status_history;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS issues;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS issue_status;
DROP TABLE IF EXISTS priority_levels;
DROP TABLE IF EXISTS issue_categories;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS departments;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- 1. departments
-- Master table for academic and operational campus departments
-- =====================================================================
CREATE TABLE departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    head_user_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
) ENGINE=InnoDB;

-- =====================================================================
-- 2. locations
-- Master table for campus physical locations
-- =====================================================================
CREATE TABLE locations (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    building_name VARCHAR(100) NOT NULL,
    floor INT NOT NULL,
    room_number VARCHAR(50) NOT NULL,
    location_type ENUM('hostel', 'classroom', 'lab', 'library', 'canteen', 'ground', 'other') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_location UNIQUE (building_name, floor, room_number)
) ENGINE=InnoDB;

-- =====================================================================
-- 3. issue_categories
-- Master table mapping issue types to responsible default departments
-- =====================================================================
CREATE TABLE issue_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NULL,
    default_department_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_categories_department
        FOREIGN KEY (default_department_id) REFERENCES departments(department_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- 4. priority_levels
-- Master table defining SLA resolution times
-- =====================================================================
CREATE TABLE priority_levels (
    priority_id INT AUTO_INCREMENT PRIMARY KEY,
    level_name VARCHAR(50) NOT NULL UNIQUE,
    sla_hours INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_sla_positive CHECK (sla_hours > 0)
) ENGINE=InnoDB;

-- =====================================================================
-- 5. issue_status
-- Master table for lifecycle state definitions
-- =====================================================================
CREATE TABLE issue_status (
    status_id INT AUTO_INCREMENT PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NULL
) ENGINE=InnoDB;

-- =====================================================================
-- 6. users
-- People table for students, staff, administrators, and technicians
-- =====================================================================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NULL,
    role ENUM('student', 'staff', 'admin', 'technician') NOT NULL,
    department_id INT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_users_department
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- Circular reference resolution: Add Foreign Key for department head_user_id
ALTER TABLE departments
    ADD CONSTRAINT fk_departments_head
    FOREIGN KEY (head_user_id) REFERENCES users(user_id)
    ON UPDATE CASCADE ON DELETE SET NULL;

-- =====================================================================
-- 7. issues
-- Core workflow table recording all campus problems
-- =====================================================================
CREATE TABLE issues (
    issue_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    reported_by INT NOT NULL,
    category_id INT NOT NULL,
    location_id INT NOT NULL,
    priority_id INT NOT NULL,
    status_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT fk_issues_reporter
        FOREIGN KEY (reported_by) REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_issues_category
        FOREIGN KEY (category_id) REFERENCES issue_categories(category_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_issues_location
        FOREIGN KEY (location_id) REFERENCES locations(location_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_issues_priority
        FOREIGN KEY (priority_id) REFERENCES priority_levels(priority_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_issues_status
        FOREIGN KEY (status_id) REFERENCES issue_status(status_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- 8. assignments
-- Task assignment table mapping issues to technicians
-- =====================================================================
CREATE TABLE assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    issue_id INT NOT NULL,
    assigned_to INT NOT NULL,
    assigned_by INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expected_completion TIMESTAMP NULL DEFAULT NULL,
    completed_at TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT fk_assignments_issue
        FOREIGN KEY (issue_id) REFERENCES issues(issue_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_assignments_technician
        FOREIGN KEY (assigned_to) REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_assignments_admin
        FOREIGN KEY (assigned_by) REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- 9. issue_status_history
-- Audit log recording state transitions and remarks
-- =====================================================================
CREATE TABLE issue_status_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    issue_id INT NOT NULL,
    old_status_id INT NULL,
    new_status_id INT NOT NULL,
    changed_by INT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    remarks TEXT NULL,
    CONSTRAINT fk_history_issue
        FOREIGN KEY (issue_id) REFERENCES issues(issue_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_history_old_status
        FOREIGN KEY (old_status_id) REFERENCES issue_status(status_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_history_new_status
        FOREIGN KEY (new_status_id) REFERENCES issue_status(status_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_history_changed_by
        FOREIGN KEY (changed_by) REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- =====================================================================
-- 10. comments
-- Collaboration thread on issues
-- =====================================================================
CREATE TABLE comments (
    comment_id INT AUTO_INCREMENT PRIMARY KEY,
    issue_id INT NOT NULL,
    user_id INT NOT NULL,
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_comments_issue
        FOREIGN KEY (issue_id) REFERENCES issues(issue_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_comments_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- 11. attachments
-- File/Image uploads associated with reported issues
-- =====================================================================
CREATE TABLE attachments (
    attachment_id INT AUTO_INCREMENT PRIMARY KEY,
    issue_id INT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    uploaded_by INT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_attachments_issue
        FOREIGN KEY (issue_id) REFERENCES issues(issue_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_attachments_user
        FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- 12. feedback
-- Resolution satisfaction ratings submitted by the issue reporter
-- =====================================================================
CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    issue_id INT NOT NULL UNIQUE,
    user_id INT NOT NULL,
    rating INT NOT NULL,
    feedback_text TEXT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_feedback_rating CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT fk_feedback_issue
        FOREIGN KEY (issue_id) REFERENCES issues(issue_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_feedback_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- =====================================================================
-- PERFORMANCE INDEXES (As specified in requirement Section 4)
-- =====================================================================
CREATE INDEX idx_issues_status ON issues(status_id);
CREATE INDEX idx_issues_category ON issues(category_id);
CREATE INDEX idx_issues_reported_by ON issues(reported_by);
CREATE INDEX idx_issues_created_at ON issues(created_at);
CREATE INDEX idx_issues_location ON issues(location_id);
CREATE INDEX idx_issues_priority ON issues(priority_id);

CREATE INDEX idx_assignments_assigned_to ON assignments(assigned_to);
CREATE INDEX idx_assignments_issue_id ON assignments(issue_id);

CREATE INDEX idx_issue_status_history_issue_id ON issue_status_history(issue_id);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_department ON users(department_id);
