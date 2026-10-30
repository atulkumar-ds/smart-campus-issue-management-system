-- =====================================================================
-- SMART CAMPUS ISSUE MANAGEMENT SYSTEM - TRIGGERS, VIEWS & PROCEDURES
-- MySQL 8.0 Implementation
-- =====================================================================

USE smart_campus;

-- =====================================================================
-- SECTION A: TRIGGERS
-- =====================================================================

DELIMITER //

-- ---------------------------------------------------------------------
-- Trigger 1: trg_issue_status_log (AFTER UPDATE ON issues)
-- Automatically inserts an audit record into issue_status_history
-- whenever the issue's status_id changes.
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_issue_status_log //
CREATE TRIGGER trg_issue_status_log
AFTER UPDATE ON issues
FOR EACH ROW
BEGIN
    IF OLD.status_id <> NEW.status_id THEN
        INSERT INTO issue_status_history (
            issue_id,
            old_status_id,
            new_status_id,
            changed_by,
            changed_at,
            remarks
        ) VALUES (
            NEW.issue_id,
            OLD.status_id,
            NEW.status_id,
            @current_user_id,
            NOW(),
            IFNULL(@current_remarks, CONCAT('Status transitioned from status_id ', OLD.status_id, ' to ', NEW.status_id))
        );
    END IF;
END //

-- ---------------------------------------------------------------------
-- Trigger 2: trg_issue_resolved_time (BEFORE UPDATE ON issues)
-- Automatically sets resolved_at when transitioning to resolved status,
-- and updates updated_at. Prevents overwriting resolved_at if already set.
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_issue_resolved_time //
CREATE TRIGGER trg_issue_resolved_time
BEFORE UPDATE ON issues
FOR EACH ROW
BEGIN
    DECLARE v_resolved_status_id INT;

    SET NEW.updated_at = NOW();

    SELECT status_id INTO v_resolved_status_id
    FROM issue_status
    WHERE status_name = 'resolved'
    LIMIT 1;

    IF NEW.status_id = v_resolved_status_id AND (OLD.status_id <> v_resolved_status_id OR OLD.resolved_at IS NULL) THEN
        SET NEW.resolved_at = NOW();
    END IF;
END //

-- ---------------------------------------------------------------------
-- Trigger 3: trg_assignment_status (AFTER INSERT ON assignments)
-- Automatically updates the issue status to 'assigned'.
-- That UPDATE statement in turn causes trg_issue_status_log to fire,
-- preserving single-source status audit trail without duplicate logs.
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_assignment_status //
CREATE TRIGGER trg_assignment_status
AFTER INSERT ON assignments
FOR EACH ROW
BEGIN
    DECLARE v_assigned_status_id INT;

    SELECT status_id INTO v_assigned_status_id
    FROM issue_status
    WHERE status_name = 'assigned'
    LIMIT 1;

    -- Update issue status; trg_issue_status_log logs the transition
    UPDATE issues
    SET status_id = v_assigned_status_id
    WHERE issue_id = NEW.issue_id;
END //

DELIMITER ;

-- =====================================================================
-- SECTION B: VIEWS
-- =====================================================================

-- ---------------------------------------------------------------------
-- View 1: v_open_issues_by_department
-- Summarizes workload across departments derived via default_department_id.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_open_issues_by_department AS
SELECT 
    d.department_id,
    d.department_name,
    COUNT(CASE WHEN s.status_name = 'open' THEN 1 END) AS open_issues,
    COUNT(CASE WHEN s.status_name = 'in_progress' THEN 1 END) AS in_progress_issues,
    COUNT(CASE WHEN s.status_name IN ('open', 'assigned', 'in_progress') THEN 1 END) AS total_unresolved_issues
FROM departments d
JOIN issue_categories ic ON d.department_id = ic.default_department_id
LEFT JOIN issues i ON ic.category_id = i.category_id
LEFT JOIN issue_status s ON i.status_id = s.status_id
GROUP BY d.department_id, d.department_name;

-- ---------------------------------------------------------------------
-- View 2: v_overdue_issues
-- Lists all issues exceeding SLA resolution targets that remain unresolved.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_overdue_issues AS
SELECT 
    i.issue_id,
    i.title,
    i.created_at,
    p.level_name AS priority_level,
    p.sla_hours,
    s.status_name AS current_status,
    d.department_name,
    TIMESTAMPDIFF(HOUR, i.created_at, NOW()) AS hours_elapsed,
    TIMESTAMPDIFF(HOUR, i.created_at, NOW()) - p.sla_hours AS hours_overdue,
    u.name AS reporter_name,
    u.email AS reporter_email,
    loc.building_name,
    loc.room_number
FROM issues i
JOIN priority_levels p ON i.priority_id = p.priority_id
JOIN issue_status s ON i.status_id = s.status_id
JOIN issue_categories ic ON i.category_id = ic.category_id
JOIN departments d ON ic.default_department_id = d.department_id
JOIN users u ON i.reported_by = u.user_id
JOIN locations loc ON i.location_id = loc.location_id
WHERE s.status_name NOT IN ('resolved', 'closed', 'rejected')
  AND TIMESTAMPDIFF(HOUR, i.created_at, NOW()) > p.sla_hours;

-- ---------------------------------------------------------------------
-- View 3: v_technician_workload
-- Technician active workload excluding completed or closed tasks.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_technician_workload AS
SELECT 
    u.user_id AS technician_id,
    u.name AS technician_name,
    u.email AS technician_email,
    d.department_name,
    COUNT(CASE 
        WHEN a.assignment_id IS NOT NULL 
         AND a.completed_at IS NULL 
         AND s.status_name NOT IN ('resolved', 'closed', 'rejected')
        THEN 1 
        ELSE NULL 
    END) AS active_task_count
FROM users u
JOIN departments d ON u.department_id = d.department_id
LEFT JOIN assignments a ON u.user_id = a.assigned_to
LEFT JOIN issues i ON a.issue_id = i.issue_id
LEFT JOIN issue_status s ON i.status_id = s.status_id
WHERE u.role = 'technician' AND u.is_active = TRUE
GROUP BY u.user_id, u.name, u.email, d.department_name;

-- ---------------------------------------------------------------------
-- View 4: v_issue_details
-- Comprehensive joined view supporting UI tables, detail modals, and management.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_issue_details AS
SELECT 
    i.issue_id,
    i.title,
    i.description,
    i.created_at,
    i.updated_at,
    i.resolved_at,
    
    -- Reporter details
    u.user_id AS reporter_id,
    u.name AS reporter_name,
    u.email AS reporter_email,
    u.phone AS reporter_phone,
    u.role AS reporter_role,
    
    -- Category & Responsible Department
    ic.category_id,
    ic.category_name,
    d.department_id,
    d.department_name,
    
    -- Location details
    loc.location_id,
    loc.building_name,
    loc.floor,
    loc.room_number,
    loc.location_type,
    
    -- Priority & SLA
    p.priority_id,
    p.level_name AS priority_level,
    p.sla_hours,
    
    -- Status
    s.status_id,
    s.status_name,
    
    -- Active Assignment (if assigned)
    act_assign.assignment_id,
    tech.user_id AS assigned_technician_id,
    tech.name AS assigned_technician_name,
    tech.email AS assigned_technician_email,
    act_assign.assigned_at,
    act_assign.expected_completion
FROM issues i
JOIN users u ON i.reported_by = u.user_id
JOIN issue_categories ic ON i.category_id = ic.category_id
JOIN departments d ON ic.default_department_id = d.department_id
JOIN locations loc ON i.location_id = loc.location_id
JOIN priority_levels p ON i.priority_id = p.priority_id
JOIN issue_status s ON i.status_id = s.status_id
LEFT JOIN assignments act_assign ON i.issue_id = act_assign.issue_id AND act_assign.completed_at IS NULL
LEFT JOIN users tech ON act_assign.assigned_to = tech.user_id;

-- =====================================================================
-- SECTION C: STORED PROCEDURE
-- =====================================================================

DELIMITER //

DROP PROCEDURE IF EXISTS assign_least_loaded_technician //
CREATE PROCEDURE assign_least_loaded_technician(
    IN p_issue_id INT,
    IN p_admin_id INT,
    OUT p_technician_id INT
)
proc_label: BEGIN
    DECLARE v_category_id INT;
    DECLARE v_status_id INT;
    DECLARE v_status_name VARCHAR(50);
    DECLARE v_dept_id INT;
    DECLARE v_sla_hours INT;
    DECLARE v_admin_role VARCHAR(50);
    DECLARE v_chosen_tech_id INT DEFAULT NULL;
    DECLARE v_expected_completion TIMESTAMP;
    DECLARE v_active_assignments INT DEFAULT 0;

    -- Error handler for rollback on unexpected SQL exception
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 1. Validate Admin Authorization
    SELECT role INTO v_admin_role
    FROM users
    WHERE user_id = p_admin_id AND is_active = TRUE;

    IF v_admin_role IS NULL OR v_admin_role <> 'admin' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Unauthorized: User is not an active administrator';
    END IF;

    -- 2. Lock & Validate Issue
    SELECT category_id, status_id
    INTO v_category_id, v_status_id
    FROM issues
    WHERE issue_id = p_issue_id
    FOR UPDATE;

    IF v_category_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Validation Error: Issue does not exist';
    END IF;

    -- Check issue status
    SELECT status_name INTO v_status_name
    FROM issue_status
    WHERE status_id = v_status_id;

    IF v_status_name IN ('resolved', 'closed', 'rejected') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Validation Error: Cannot assign an issue that is already resolved, closed, or rejected';
    END IF;

    -- 3. Check for existing active assignment
    SELECT COUNT(*) INTO v_active_assignments
    FROM assignments
    WHERE issue_id = p_issue_id AND completed_at IS NULL;

    IF v_active_assignments > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Validation Error: Issue already has an active technician assignment';
    END IF;

    -- 4. Find Responsible Department
    SELECT default_department_id INTO v_dept_id
    FROM issue_categories
    WHERE category_id = v_category_id;

    -- 5. Find Least-Loaded Active Technician in the responsible department
    -- Uses deterministic tie-breaker: active_task_count ASC, user_id ASC
    SELECT u.user_id INTO v_chosen_tech_id
    FROM users u
    LEFT JOIN assignments a ON u.user_id = a.assigned_to AND a.completed_at IS NULL
    LEFT JOIN issues i ON a.issue_id = i.issue_id
    LEFT JOIN issue_status s ON i.status_id = s.status_id AND s.status_name NOT IN ('resolved', 'closed', 'rejected')
    WHERE u.role = 'technician' 
      AND u.is_active = TRUE 
      AND u.department_id = v_dept_id
    GROUP BY u.user_id
    ORDER BY COUNT(a.assignment_id) ASC, u.user_id ASC
    LIMIT 1;

    IF v_chosen_tech_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Assignment Error: No active technician available in the responsible department';
    END IF;

    -- 6. Calculate Expected Completion Time from SLA
    SELECT p.sla_hours INTO v_sla_hours
    FROM priority_levels p
    JOIN issues iss ON p.priority_id = iss.priority_id
    WHERE iss.issue_id = p_issue_id;

    SET v_expected_completion = DATE_ADD(NOW(), INTERVAL IFNULL(v_sla_hours, 24) HOUR);

    -- 7. Audit variables for trg_issue_status_log
    SET @current_user_id = p_admin_id;
    SET @current_remarks = CONCAT('Auto-assigned to technician ID #', v_chosen_tech_id, ' by administrator');

    -- 8. Insert Assignment
    -- trg_assignment_status will fire and set issues.status_id = 'assigned'
    -- trg_issue_status_log will fire and record the status history transition
    INSERT INTO assignments (
        issue_id,
        assigned_to,
        assigned_by,
        assigned_at,
        expected_completion
    ) VALUES (
        p_issue_id,
        v_chosen_tech_id,
        p_admin_id,
        NOW(),
        v_expected_completion
    );

    COMMIT;

    -- Return the selected technician ID to caller
    SET p_technician_id = v_chosen_tech_id;

END //

DELIMITER ;
