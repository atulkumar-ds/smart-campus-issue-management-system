"""
Analytics Service Layer.
Executes live SQL queries and views to compute metrics and chart data for Admin Dashboard.
"""

from typing import Dict, Any, List
from db import get_db_cursor
import pandas as pd


class AnalyticsService:
    """Service providing aggregated dashboard metrics and chart datasets."""

    @staticmethod
    def get_summary_metrics() -> Dict[str, int]:
        """Calculates top-level KPI metrics using live SQL counts."""
        query = """
            SELECT 
                COUNT(*) AS total_issues,
                COUNT(CASE WHEN s.status_name = 'open' THEN 1 END) AS open_issues,
                COUNT(CASE WHEN s.status_name = 'assigned' THEN 1 END) AS assigned_issues,
                COUNT(CASE WHEN s.status_name = 'in_progress' THEN 1 END) AS in_progress_issues,
                COUNT(CASE WHEN s.status_name = 'resolved' THEN 1 END) AS resolved_issues,
                COUNT(CASE WHEN s.status_name = 'closed' THEN 1 END) AS closed_issues,
                COUNT(CASE WHEN s.status_name = 'rejected' THEN 1 END) AS rejected_issues
            FROM issues i
            JOIN issue_status s ON i.status_id = s.status_id;
        """

        overdue_query = "SELECT COUNT(*) AS overdue_count FROM v_overdue_issues;"

        with get_db_cursor() as cursor:
            cursor.execute(query)
            metrics = cursor.fetchone() or {}

            cursor.execute(overdue_query)
            overdue_res = cursor.fetchone()
            metrics["overdue_issues"] = overdue_res["overdue_count"] if overdue_res else 0

        return metrics

    @staticmethod
    def get_issues_by_category() -> pd.DataFrame:
        query = """
            SELECT ic.category_name, COUNT(i.issue_id) AS issue_count
            FROM issue_categories ic
            LEFT JOIN issues i ON ic.category_id = i.category_id
            GROUP BY ic.category_id, ic.category_name
            ORDER BY issue_count DESC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
        return pd.DataFrame(data)

    @staticmethod
    def get_issues_by_building() -> pd.DataFrame:
        query = """
            SELECT loc.building_name, COUNT(i.issue_id) AS issue_count
            FROM locations loc
            JOIN issues i ON loc.location_id = i.location_id
            GROUP BY loc.building_name
            ORDER BY issue_count DESC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
        return pd.DataFrame(data)

    @staticmethod
    def get_reported_vs_resolved_trend() -> pd.DataFrame:
        query = """
            SELECT 
                DATE_FORMAT(calendar_date, '%Y-%m') AS month_year,
                SUM(reported_flag) AS reported,
                SUM(resolved_flag) AS resolved
            FROM (
                SELECT created_at AS calendar_date, 1 AS reported_flag, 0 AS resolved_flag FROM issues
                UNION ALL
                SELECT resolved_at AS calendar_date, 0 AS reported_flag, 1 AS resolved_flag 
                FROM issues WHERE resolved_at IS NOT NULL
            ) AS timeline
            GROUP BY DATE_FORMAT(calendar_date, '%Y-%m')
            ORDER BY month_year ASC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
        return pd.DataFrame(data)

    @staticmethod
    def get_avg_resolution_by_department() -> pd.DataFrame:
        query = """
            SELECT 
                d.department_name,
                ROUND(AVG(TIMESTAMPDIFF(MINUTE, i.created_at, i.resolved_at)) / 60.0, 1) AS avg_hours
            FROM departments d
            JOIN issue_categories ic ON d.department_id = ic.default_department_id
            JOIN issues i ON ic.category_id = i.category_id
            WHERE i.resolved_at IS NOT NULL
            GROUP BY d.department_id, d.department_name
            ORDER BY avg_hours ASC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
        return pd.DataFrame(data)

    @staticmethod
    def get_technician_workload() -> pd.DataFrame:
        """Queries v_technician_workload view."""
        query = """
            SELECT technician_name, department_name, active_task_count
            FROM v_technician_workload
            ORDER BY active_task_count DESC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
        return pd.DataFrame(data)

    @staticmethod
    def get_priority_distribution() -> pd.DataFrame:
        query = """
            SELECT p.level_name AS priority, COUNT(i.issue_id) AS issue_count
            FROM priority_levels p
            LEFT JOIN issues i ON p.priority_id = i.priority_id
            GROUP BY p.priority_id, p.level_name
            ORDER BY p.sla_hours ASC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
        return pd.DataFrame(data)

    @staticmethod
    def get_department_backlog_view() -> pd.DataFrame:
        """Queries v_open_issues_by_department view."""
        query = "SELECT * FROM v_open_issues_by_department ORDER BY total_unresolved_issues DESC;"
        with get_db_cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
        return pd.DataFrame(data)

    @staticmethod
    def get_overdue_issues_list() -> List[Dict[str, Any]]:
        """Queries v_overdue_issues view."""
        query = "SELECT * FROM v_overdue_issues ORDER BY hours_overdue DESC LIMIT 10;"
        with get_db_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
