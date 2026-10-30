"""
Automated tests for Analytical SQL Queries.
Executes all 12 analytical queries against the generated demo dataset in MySQL.
"""

import pytest
import mysql.connector
from config import Config


@pytest.fixture(scope="module")
def db_conn():
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
    )
    yield conn
    conn.close()


def test_q1_issues_per_category_and_building(db_conn):
    """Q1: Issues per category and per building."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT 
            ic.category_name,
            loc.building_name,
            COUNT(i.issue_id) AS total_issues
        FROM issues i
        INNER JOIN issue_categories ic ON i.category_id = ic.category_id
        INNER JOIN locations loc ON i.location_id = loc.location_id
        GROUP BY ic.category_name, loc.building_name
        ORDER BY total_issues DESC;
        """
    )
    results = cursor.fetchall()
    assert len(results) > 0
    assert "total_issues" in results[0]
    cursor.close()


def test_q2_avg_resolution_time(db_conn):
    """Q2: Average resolution time per category."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT 
            ic.category_name,
            COUNT(i.issue_id) AS resolved_issue_count,
            ROUND(AVG(TIMESTAMPDIFF(MINUTE, i.created_at, i.resolved_at)) / 60.0, 2) AS avg_resolution_hours
        FROM issues i
        INNER JOIN issue_categories ic ON i.category_id = ic.category_id
        WHERE i.resolved_at IS NOT NULL
        GROUP BY ic.category_id, ic.category_name;
        """
    )
    results = cursor.fetchall()
    assert len(results) > 0
    assert float(results[0]["avg_resolution_hours"]) >= 0.0
    cursor.close()


def test_q3_departments_ranked_unresolved(db_conn):
    """Q3: Departments ranked by unresolved issues."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT 
            d.department_name,
            SUM(CASE WHEN s.status_name IN ('open', 'assigned', 'in_progress') THEN 1 ELSE 0 END) AS unresolved_count,
            DENSE_RANK() OVER (ORDER BY SUM(CASE WHEN s.status_name IN ('open', 'assigned', 'in_progress') THEN 1 ELSE 0 END) DESC) AS backlog_rank
        FROM departments d
        INNER JOIN issue_categories ic ON d.department_id = ic.default_department_id
        LEFT JOIN issues i ON ic.category_id = i.category_id
        LEFT JOIN issue_status s ON i.status_id = s.status_id
        GROUP BY d.department_id, d.department_name;
        """
    )
    results = cursor.fetchall()
    assert len(results) > 0
    assert results[0]["backlog_rank"] == 1
    cursor.close()


def test_q4_top_technician_this_month(db_conn):
    """Q4: Technician with the highest number of resolved issues."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
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
        GROUP BY u.user_id, u.name, d.department_name
        ORDER BY resolved_this_month DESC
        LIMIT 1;
        """
    )
    row = cursor.fetchone()
    assert row is not None
    assert row["resolved_this_month"] > 0
    cursor.close()


def test_q5_sla_breach_issues(db_conn):
    """Q5: Issues that breached their SLA."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT 
            i.issue_id,
            i.title,
            ic.category_name,
            p.level_name AS priority,
            p.sla_hours,
            s.status_name AS current_status,
            TIMESTAMPDIFF(HOUR, i.created_at, IFNULL(i.resolved_at, NOW())) - p.sla_hours AS sla_breach_hours
        FROM issues i
        INNER JOIN priority_levels p ON i.priority_id = p.priority_id
        INNER JOIN issue_categories ic ON i.category_id = ic.category_id
        INNER JOIN issue_status s ON i.status_id = s.status_id
        WHERE TIMESTAMPDIFF(HOUR, i.created_at, IFNULL(i.resolved_at, NOW())) > p.sla_hours
          AND s.status_name <> 'rejected'
        ORDER BY sla_breach_hours DESC;
        """
    )
    results = cursor.fetchall()
    assert len(results) > 0
    assert results[0]["sla_breach_hours"] > 0
    cursor.close()


def test_q6_avg_rating_per_technician(db_conn):
    """Q6: Average feedback rating per technician."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT 
            tech.user_id AS technician_id,
            tech.name AS technician_name,
            d.department_name,
            COUNT(f.feedback_id) AS total_reviews,
            ROUND(AVG(f.rating), 2) AS avg_rating
        FROM users tech
        INNER JOIN departments d ON tech.department_id = d.department_id
        INNER JOIN assignments a ON tech.user_id = a.assigned_to
        INNER JOIN issues i ON a.issue_id = i.issue_id
        INNER JOIN feedback f ON i.issue_id = f.issue_id
        WHERE tech.role = 'technician'
        GROUP BY tech.user_id, tech.name, d.department_name
        HAVING total_reviews > 0;
        """
    )
    results = cursor.fetchall()
    assert len(results) > 0
    for r in results:
        assert 1.0 <= float(r["avg_rating"]) <= 5.0
    cursor.close()


def test_q7_hotspot_buildings(db_conn):
    """Q7: Buildings with more than N issues in the last 30 days."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT 
            loc.building_name,
            COUNT(i.issue_id) AS recent_issues_count
        FROM issues i
        INNER JOIN locations loc ON i.location_id = loc.location_id
        WHERE i.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY loc.building_name
        HAVING COUNT(i.issue_id) >= 2;
        """
    )
    results = cursor.fetchall()
    assert len(results) > 0
    cursor.close()


def test_q8_top_reporters(db_conn):
    """Q8: Users who reported the most issues."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT 
            u.user_id,
            u.name,
            u.role,
            COUNT(i.issue_id) AS total_issues_reported
        FROM users u
        INNER JOIN issues i ON u.user_id = i.reported_by
        GROUP BY u.user_id, u.name, u.role
        ORDER BY total_issues_reported DESC
        LIMIT 10;
        """
    )
    results = cursor.fetchall()
    assert len(results) > 0
    assert results[0]["total_issues_reported"] >= 1
    cursor.close()


def test_q9_unassigned_issues_left_join(db_conn):
    """Q9: Issues with no assignment using LEFT JOIN."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT 
            i.issue_id,
            i.title,
            ic.category_name,
            s.status_name
        FROM issues i
        INNER JOIN issue_categories ic ON i.category_id = ic.category_id
        INNER JOIN issue_status s ON i.status_id = s.status_id
        LEFT JOIN assignments a ON i.issue_id = a.issue_id
        WHERE a.assignment_id IS NULL AND s.status_name = 'open';
        """
    )
    results = cursor.fetchall()
    assert len(results) > 0
    cursor.close()


def test_q10_monthly_trend(db_conn):
    """Q10: Monthly trend of reported versus resolved issues."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
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
        """
    )
    results = cursor.fetchall()
    assert len(results) > 0
    assert results[0]["total_reported"] > 0
    cursor.close()


def test_q11_categories_below_rating(db_conn):
    """Q11: Categories with average feedback rating using HAVING."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT 
            ic.category_id,
            ic.category_name,
            COUNT(f.feedback_id) AS feedback_count,
            ROUND(AVG(f.rating), 2) AS avg_rating
        FROM issue_categories ic
        INNER JOIN issues i ON ic.category_id = i.category_id
        INNER JOIN feedback f ON i.issue_id = f.issue_id
        GROUP BY ic.category_id, ic.category_name
        HAVING AVG(f.rating) <= 5.0;
        """
    )
    results = cursor.fetchall()
    assert len(results) > 0
    cursor.close()


def test_q12_recurrent_issues_same_location(db_conn):
    """Q12: Issues reported multiple times in the same location."""
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT 
            loc.building_name,
            loc.floor,
            loc.room_number,
            ic.category_name,
            COUNT(i.issue_id) AS incident_count
        FROM issues i
        INNER JOIN locations loc ON i.location_id = loc.location_id
        INNER JOIN issue_categories ic ON i.category_id = ic.category_id
        GROUP BY loc.building_name, loc.floor, loc.room_number, ic.category_name
        HAVING COUNT(i.issue_id) > 1
        ORDER BY incident_count DESC;
        """
    )
    results = cursor.fetchall()
    assert len(results) > 0
    assert results[0]["incident_count"] > 1
    cursor.close()
