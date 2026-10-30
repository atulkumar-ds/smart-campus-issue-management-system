-- =====================================================================
-- SMART CAMPUS ISSUE MANAGEMENT SYSTEM - ANALYTICAL SQL QUERIES
-- B.Tech DBMS Course Project
-- File: queries.sql
-- Contains 12 core analytical queries covering advanced joins, window functions,
-- aggregations, subqueries, date math, HAVING filters, and SLA calculations.
-- =====================================================================

USE smart_campus;

-- =====================================================================
-- Query 1: Issues per category and per building
-- Concepts Demonstrated: Multi-table INNER JOIN, GROUP BY with multiple dimensions, COUNT()
-- Purpose: Visualizes which facility domains fail most frequently across campus infrastructure.
-- =====================================================================
SELECT 
    ic.category_name,
    loc.building_name,
    COUNT(i.issue_id) AS total_issues
FROM issues i
INNER JOIN issue_categories ic ON i.category_id = ic.category_id
INNER JOIN locations loc ON i.location_id = loc.location_id
GROUP BY ic.category_name, loc.building_name
ORDER BY total_issues DESC, ic.category_name ASC;

-- =====================================================================
-- Query 2: Average resolution time per category (in hours)
-- Concepts Demonstrated: TIMESTAMPDIFF(HOUR, ...), AVG(), INNER JOIN, WHERE filter on resolved tickets
-- Purpose: Evaluates maintenance speed and efficiency for each operational domain.
-- =====================================================================
SELECT 
    ic.category_name,
    COUNT(i.issue_id) AS resolved_issue_count,
    ROUND(AVG(TIMESTAMPDIFF(MINUTE, i.created_at, i.resolved_at)) / 60.0, 2) AS avg_resolution_hours,
    MIN(TIMESTAMPDIFF(HOUR, i.created_at, i.resolved_at)) AS min_resolution_hours,
    MAX(TIMESTAMPDIFF(HOUR, i.created_at, i.resolved_at)) AS max_resolution_hours
FROM issues i
INNER JOIN issue_categories ic ON i.category_id = ic.category_id
WHERE i.resolved_at IS NOT NULL
GROUP BY ic.category_id, ic.category_name
ORDER BY avg_resolution_hours ASC;

-- =====================================================================
-- Query 3: Departments ranked by the number of unresolved issues
-- Concepts Demonstrated: Conditional aggregation SUM(CASE WHEN ...), multi-table JOIN, DENSE_RANK() window function
-- Purpose: Administrative prioritization of department backlogs and staffing needs.
-- =====================================================================
SELECT 
    d.department_name,
    COUNT(i.issue_id) AS total_logged,
    SUM(CASE WHEN s.status_name IN ('open', 'assigned', 'in_progress') THEN 1 ELSE 0 END) AS unresolved_count,
    SUM(CASE WHEN s.status_name = 'open' THEN 1 ELSE 0 END) AS pending_assignment_count,
    SUM(CASE WHEN s.status_name = 'in_progress' THEN 1 ELSE 0 END) AS active_repair_count,
    DENSE_RANK() OVER (ORDER BY SUM(CASE WHEN s.status_name IN ('open', 'assigned', 'in_progress') THEN 1 ELSE 0 END) DESC) AS backlog_rank
FROM departments d
INNER JOIN issue_categories ic ON d.department_id = ic.default_department_id
LEFT JOIN issues i ON ic.category_id = i.category_id
LEFT JOIN issue_status s ON i.status_id = s.status_id
GROUP BY d.department_id, d.department_name
ORDER BY unresolved_count DESC;

-- =====================================================================
-- Query 4: Technician with the highest number of resolved issues this month
-- Concepts Demonstrated: Date functions (YEAR(), MONTH()), INNER JOIN, GROUP BY, LIMIT 1 tie-breaking
-- Purpose: Monthly technician performance review and recognition.
-- =====================================================================
SELECT 
    u.user_id AS technician_id,
    u.name AS technician_name,
    d.department_name,
    COUNT(a.assignment_id) AS resolved_this_month
FROM assignments a
INNER JOIN users u ON a.assigned_to = u.user_id
INNER JOIN departments d ON u.department_id = d.department_id
INNER JOIN issues i ON a.issue_id = i.issue_id
WHERE a.completed_at IS NOT NULL
  AND YEAR(a.completed_at) = YEAR(NOW())
  AND MONTH(a.completed_at) = MONTH(NOW())
GROUP BY u.user_id, u.name, d.department_name
ORDER BY resolved_this_month DESC, u.name ASC
LIMIT 1;

-- =====================================================================
-- Query 5: Issues that breached their SLA
-- Concepts Demonstrated: Date arithmetic, multi-table JOINs, conditional status checking
-- Purpose: Identifies tickets where time-to-resolution or current elapsed time exceeded target SLA.
-- =====================================================================
SELECT 
    i.issue_id,
    i.title,
    ic.category_name,
    p.level_name AS priority,
    p.sla_hours,
    s.status_name AS current_status,
    i.created_at,
    IFNULL(i.resolved_at, NOW()) AS benchmark_time,
    TIMESTAMPDIFF(HOUR, i.created_at, IFNULL(i.resolved_at, NOW())) AS actual_hours_taken,
    TIMESTAMPDIFF(HOUR, i.created_at, IFNULL(i.resolved_at, NOW())) - p.sla_hours AS sla_breach_hours,
    u.name AS reported_by_name
FROM issues i
INNER JOIN priority_levels p ON i.priority_id = p.priority_id
INNER JOIN issue_categories ic ON i.category_id = ic.category_id
INNER JOIN issue_status s ON i.status_id = s.status_id
INNER JOIN users u ON i.reported_by = u.user_id
WHERE TIMESTAMPDIFF(HOUR, i.created_at, IFNULL(i.resolved_at, NOW())) > p.sla_hours
  AND s.status_name <> 'rejected'
ORDER BY sla_breach_hours DESC;

-- =====================================================================
-- Query 6: Average feedback rating per technician
-- Concepts Demonstrated: Multi-table JOIN linking assignments -> issues -> feedback, AVG(), COUNT()
-- Purpose: Quality-of-service auditing based on student and staff ratings.
-- =====================================================================
SELECT 
    tech.user_id AS technician_id,
    tech.name AS technician_name,
    d.department_name,
    COUNT(f.feedback_id) AS total_reviews,
    ROUND(AVG(f.rating), 2) AS avg_rating,
    SUM(CASE WHEN f.rating >= 4 THEN 1 ELSE 0 END) AS positive_reviews,
    SUM(CASE WHEN f.rating <= 2 THEN 1 ELSE 0 END) AS negative_reviews
FROM users tech
INNER JOIN departments d ON tech.department_id = d.department_id
INNER JOIN assignments a ON tech.user_id = a.assigned_to
INNER JOIN issues i ON a.issue_id = i.issue_id
INNER JOIN feedback f ON i.issue_id = f.issue_id
WHERE tech.role = 'technician'
GROUP BY tech.user_id, tech.name, d.department_name
HAVING total_reviews > 0
ORDER BY avg_rating DESC, total_reviews DESC;

-- =====================================================================
-- Query 7: Buildings with more than N issues in the last 30 days
-- Concepts Demonstrated: DATE_SUB(), NOW(), HAVING clause with COUNT(), GROUP BY
-- Purpose: Infrastructure hotspot detection (e.g., threshold N = 3 issues).
-- =====================================================================
SELECT 
    loc.building_name,
    COUNT(i.issue_id) AS recent_issues_count,
    COUNT(DISTINCT i.category_id) AS distinct_problem_types
FROM issues i
INNER JOIN locations loc ON i.location_id = loc.location_id
WHERE i.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY loc.building_name
HAVING COUNT(i.issue_id) >= 3
ORDER BY recent_issues_count DESC;

-- =====================================================================
-- Query 8: Users who reported the most issues
-- Concepts Demonstrated: Aggregate COUNT(), GROUP BY, INNER JOIN, filtering students/staff
-- Purpose: Identifies most active reporters across campus.
-- =====================================================================
SELECT 
    u.user_id,
    u.name,
    u.email,
    u.role,
    COUNT(i.issue_id) AS total_issues_reported,
    SUM(CASE WHEN s.status_name IN ('resolved', 'closed') THEN 1 ELSE 0 END) AS resolved_count
FROM users u
INNER JOIN issues i ON u.user_id = i.reported_by
INNER JOIN issue_status s ON i.status_id = s.status_id
GROUP BY u.user_id, u.name, u.email, u.role
ORDER BY total_issues_reported DESC
LIMIT 10;

-- =====================================================================
-- Query 9: Issues with no assignment after 24 hours
-- Concepts Demonstrated: LEFT OUTER JOIN, IS NULL check, date difference filter
-- Purpose: Escalation query to detect neglected or bottlenecked issues awaiting admin dispatch.
-- =====================================================================
SELECT 
    i.issue_id,
    i.title,
    ic.category_name,
    d.department_name AS responsible_department,
    loc.building_name,
    loc.room_number,
    i.created_at,
    TIMESTAMPDIFF(HOUR, i.created_at, NOW()) AS unassigned_hours
FROM issues i
INNER JOIN issue_categories ic ON i.category_id = ic.category_id
INNER JOIN departments d ON ic.default_department_id = d.department_id
INNER JOIN locations loc ON i.location_id = loc.location_id
INNER JOIN issue_status s ON i.status_id = s.status_id
LEFT JOIN assignments a ON i.issue_id = a.issue_id
WHERE a.assignment_id IS NULL
  AND s.status_name = 'open'
  AND TIMESTAMPDIFF(HOUR, i.created_at, NOW()) > 24
ORDER BY unassigned_hours DESC;

-- =====================================================================
-- Query 10: Monthly trend of reported versus resolved issues
-- Concepts Demonstrated: DATE_FORMAT(), conditional COUNT(), UNION or cross aggregation
-- Purpose: High-level operational throughput and backlog velocity over time.
-- =====================================================================
SELECT 
    DATE_FORMAT(calendar_date, '%Y-%m') AS month_year,
    SUM(reported_flag) AS total_reported,
    SUM(resolved_flag) AS total_resolved
FROM (
    SELECT created_at AS calendar_date, 1 AS reported_flag, 0 AS resolved_flag FROM issues
    UNION ALL
    SELECT resolved_at AS calendar_date, 0 AS reported_flag, 1 AS resolved_flag FROM issues WHERE resolved_at IS NOT NULL
) AS activity_stream
GROUP BY DATE_FORMAT(calendar_date, '%Y-%m')
ORDER BY month_year ASC;

-- =====================================================================
-- Query 11: Categories whose average feedback rating is below 3 using HAVING
-- Concepts Demonstrated: INNER JOIN across 3 tables, AVG(), HAVING clause with numeric comparison
-- Purpose: Identifies departments/categories needing process intervention due to poor user satisfaction.
-- =====================================================================
SELECT 
    ic.category_id,
    ic.category_name,
    d.department_name,
    COUNT(f.feedback_id) AS feedback_count,
    ROUND(AVG(f.rating), 2) AS avg_rating
FROM issue_categories ic
INNER JOIN departments d ON ic.default_department_id = d.department_id
INNER JOIN issues i ON ic.category_id = i.category_id
INNER JOIN feedback f ON i.issue_id = f.issue_id
GROUP BY ic.category_id, ic.category_name, d.department_name
HAVING AVG(f.rating) < 3.0
ORDER BY avg_rating ASC;

-- =====================================================================
-- Query 12: Issues reported multiple times in the same location (Recurrent Failures)
-- Concepts Demonstrated: Multi-level aggregation, GROUP BY (category_id, location_id), HAVING COUNT() > 1
-- Purpose: Root-cause analysis identifying chronic infrastructure failures in specific rooms.
-- =====================================================================
SELECT 
    loc.building_name,
    loc.floor,
    loc.room_number,
    ic.category_name,
    COUNT(i.issue_id) AS incident_count,
    GROUP_CONCAT(CONCAT('#', i.issue_id, ':', i.title) SEPARATOR ' | ') AS incident_samples,
    MIN(i.created_at) AS first_reported,
    MAX(i.created_at) AS latest_reported
FROM issues i
INNER JOIN locations loc ON i.location_id = loc.location_id
INNER JOIN issue_categories ic ON i.category_id = ic.category_id
GROUP BY loc.building_name, loc.floor, loc.room_number, ic.category_name
HAVING COUNT(i.issue_id) > 1
ORDER BY incident_count DESC;
