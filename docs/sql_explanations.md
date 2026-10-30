# Database SQL Architecture & Implementation Explanations

This document details the database-side architectural objects developed for the **AI-Powered Smart Campus Issue Management System**, including triggers, views, stored procedures, transaction management, and analytical queries.

---

## 1. Database Triggers

### Trigger 1: `trg_issue_status_log`
- **Timing & Event**: `AFTER UPDATE ON issues FOR EACH ROW`
- **Objective**: Guarantee audit trail immutability in `issue_status_history`.
- **Logic**:
  - Compares `OLD.status_id` against `NEW.status_id`.
  - If the status has changed, it automatically records a row into `issue_status_history` capturing `issue_id`, `old_status_id`, `new_status_id`, changed timestamp (`NOW()`), the actor (`@current_user_id`), and contextual remarks (`@current_remarks`).
  - **Single Source of Truth**: Because status changes can be triggered by direct updates, technician progress, admin closing, or assignment triggers, this trigger captures every state change centrally without requiring Python code to manually insert history logs.

### Trigger 2: `trg_issue_resolved_time`
- **Timing & Event**: `BEFORE UPDATE ON issues FOR EACH ROW`
- **Objective**: Maintain timestamp fidelity for SLA calculations.
- **Logic**:
  - Updates `NEW.updated_at = NOW()`.
  - Checks if `NEW.status_id` corresponds to `resolved`. If transitioning to resolved and `OLD.resolved_at` is `NULL`, it assigns `NEW.resolved_at = NOW()`.
  - Avoids overwriting the original resolution timestamp on subsequent edits or re-closing.

### Trigger 3: `trg_assignment_status`
- **Timing & Event**: `AFTER INSERT ON assignments FOR EACH ROW`
- **Objective**: Synchronize issue lifecycle state with technician assignment.
- **Logic**:
  - Whenever a new technician assignment is created (via admin manual dispatch or auto-assign procedure), the trigger executes:
    ```sql
    UPDATE issues SET status_id = (SELECT status_id FROM issue_status WHERE status_name = 'assigned')
    WHERE issue_id = NEW.issue_id;
    ```
  - **Cascading Trigger Coordination**: This `UPDATE` statement automatically invokes `trg_issue_status_log`, which writes the transition history. No secondary duplicate history insert is performed.

---

## 2. Relational Database Views

### View 1: `v_open_issues_by_department`
- **Purpose**: High-level departmental operations and backlog visibility.
- **Derivation**: Computes unresolved tickets by joining `departments` through `issue_categories.default_department_id` to `issues`.
- **Metrics**: Open issues, In-Progress issues, and Total Unresolved issues.

### View 2: `v_overdue_issues`
- **Purpose**: Real-time SLA breach detection.
- **Derivation**: Compares `TIMESTAMPDIFF(HOUR, i.created_at, NOW())` against `priority_levels.sla_hours` for all non-closed/resolved tickets.
- **Metrics**: Actual hours elapsed, hours overdue, responsible department, and location.

### View 3: `v_technician_workload`
- **Purpose**: Technician capacity planning and tie-breaking.
- **Derivation**: Counts currently active tasks (`completed_at IS NULL` and ticket status not in `('resolved', 'closed', 'rejected')`) per technician.
- **Exclusions**: Excludes resolved and closed tasks to guarantee accurate workload reflection.

### View 4: `v_issue_details`
- **Purpose**: Canonical de-normalized presentation layer for Streamlit grids and modals.
- **Joins**: Joins `issues` with `users` (reporter), `issue_categories`, `departments`, `locations`, `priority_levels`, `issue_status`, and `assignments` (active technician).

---

## 3. Stored Procedure: `assign_least_loaded_technician`

### Procedure Signature
```sql
CALL assign_least_loaded_technician(IN p_issue_id INT, IN p_admin_id INT, OUT p_technician_id INT);
```

### Execution Steps
1. **Transaction Initialization**: Begins an explicit `START TRANSACTION`.
2. **Admin Authorization Guard**: Queries `users` to verify `p_admin_id` has `role = 'admin'` and `is_active = TRUE`. If unauthorized, throws `SQLSTATE '45000'`.
3. **Pessimistic Row Locking (`FOR UPDATE`)**: Queries the target issue row using `SELECT ... FOR UPDATE` to prevent concurrent assignment race conditions.
4. **Lifecycle Validation**: Ensures the issue is not already resolved, closed, or rejected.
5. **Duplicate Assignment Guard**: Verifies no active uncompleted assignment already exists for this `issue_id`.
6. **Department Resolution**: Traverses `issue_categories.default_department_id` to identify the responsible operational department.
7. **Least-Loaded Technician Selection**:
   - Queries active technicians belonging strictly to that department.
   - Calculates their current open tasks.
   - Orders by `active_task_count ASC`, with `user_id ASC` as a deterministic tie-breaker.
   - Restricts to `LIMIT 1`.
8. **Expected SLA Target Calculation**: Computes expected completion timestamp by adding `priority_levels.sla_hours` to `NOW()`.
9. **Assignment Insertion**: Inserts into `assignments`.
10. **Trigger Invocation**: The database trigger `trg_assignment_status` automatically transitions the issue status to `assigned`, and `trg_issue_status_log` logs the audit entry.
11. **Transaction Commit & Return**: Commits transaction and sets `p_technician_id = v_chosen_tech_id`.
12. **Exception Handler**: `DECLARE EXIT HANDLER FOR SQLEXCEPTION` executes `ROLLBACK; RESIGNAL;` on any runtime failure.

---

## 4. Transaction Management & Atomicity Demonstration

All multi-step operational writes in the application use ACID transactions:
```sql
START TRANSACTION;

-- Step 1: Insert assignment record
INSERT INTO assignments (issue_id, assigned_to, assigned_by, assigned_at, expected_completion)
VALUES (10, 3, 1, NOW(), DATE_ADD(NOW(), INTERVAL 24 HOUR));

-- Step 2: Assignment trigger fires, updating issues.status_id = 'assigned'
-- Step 3: Issues trigger fires, recording row in issue_status_history

COMMIT;
```

If any constraint fails (e.g., non-existent technician, duplicate active assignment, or network interrupt), `ROLLBACK` executes, ensuring that no orphaned assignment or partial status change persists in the database.

---

## 5. Summary of 12 Analytical Queries

| Query # | Analytical Focus | Core SQL Concepts Demonstrated |
|---|---|---|
| **Q1** | Issues per Category & Building | Multi-table `INNER JOIN`, multi-dimensional `GROUP BY`, `COUNT()` |
| **Q2** | Average Resolution Time per Category | `TIMESTAMPDIFF()`, `AVG()`, date conversions, numeric rounding |
| **Q3** | Departments Ranked by Unresolved Backlog | Conditional `SUM(CASE ...)`, `DENSE_RANK()` window function |
| **Q4** | Top Technician of the Month | Date filtering (`YEAR()`, `MONTH()`), `LIMIT 1`, tie-breaking |
| **Q5** | SLA Breach Audit | Multi-table joins, elapsed time differential vs. SLA threshold |
| **Q6** | Average Feedback Rating per Technician | Multi-table traversal (technician -> assignment -> issue -> feedback), `HAVING` |
| **Q7** | Building Hotspots (> N issues in 30 days) | `DATE_SUB()`, `NOW()`, `HAVING COUNT() >= N` |
| **Q8** | Most Frequent Issue Reporters | `GROUP BY`, aggregate `COUNT()`, reporter identification |
| **Q9** | Neglected Issues Unassigned > 24 Hours | `LEFT OUTER JOIN` with `IS NULL` check, date threshold filter |
| **Q10** | Monthly Reported vs. Resolved Velocity | Common Table / `UNION ALL` activity stream, `DATE_FORMAT()` |
| **Q11** | Categories with Average Rating Below 3.0 | 3-table join, `AVG()`, `HAVING` clause comparison |
| **Q12** | Recurrent Failures in Same Location | Multi-column `GROUP BY`, `HAVING COUNT() > 1`, `GROUP_CONCAT()` |
