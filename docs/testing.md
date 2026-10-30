# Verification and Testing Report

This document records the automated and manual testing scenarios executed against the **AI-Powered Smart Campus Issue Management System** on MySQL 8.0 and Python 3.13.

---

## 1. Automated Test Suite Summary

- **Total Test Cases**: 61
- **Passing**: 61 (100%)
- **Failing**: 0
- **Execution Time**: ~6.4 seconds
- **Test Framework**: `pytest 9.2.0`

### Test Suite Execution Command
```bash
pytest tests/ -v
```

---

## 2. Test Scenarios & Results Matrix

| Test ID | Test Scenario | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| **TC-01** | Student account login (`aarav.sharma@campus.edu`) | Returns student profile, authenticates session | Verified authenticated | **PASS** |
| **TC-02** | Administrator account login (`admin@campus.edu`) | Returns admin profile with privileged permissions | Verified authenticated | **PASS** |
| **TC-03** | Technician account login (`tech.electrical@campus.edu`) | Returns technician profile with department mapping | Verified authenticated | **PASS** |
| **TC-04** | Invalid password verification | Authentication fails, returns `None` | Rejected as expected | **PASS** |
| **TC-05** | Deactivated account login | Rejected even with valid password | Rejected as expected | **PASS** |
| **TC-06** | Student unauthorized access to admin screen | Guard blocks execution with `Access Denied` | Access blocked | **PASS** |
| **TC-07** | Technician unauthorized access to admin screen | Guard blocks execution with `Access Denied` | Access blocked | **PASS** |
| **TC-08** | Student data isolation | Query filters by `reported_by = user_id` | Isolated to reporter | **PASS** |
| **TC-09** | Empty issue submission validation | Title/desc length checks fail with descriptive notice | Blocked before DB write | **PASS** |
| **TC-10** | Valid issue submission | Creates row in `issues`, creates initial row in `issue_status_history` | Issue created in `open` state | **PASS** |
| **TC-11** | Invalid category submission | Foreign key and service validator reject invalid category | Rejected with notice | **PASS** |
| **TC-12** | Feedback rating boundary enforcement (0 and 6) | CHECK constraint & service validator reject ratings outside 1–5 | Rejected as expected | **PASS** |
| **TC-13** | Duplicate feedback on same issue | `UNIQUE(issue_id)` on `feedback` rejects second submission | Second attempt rejected | **PASS** |
| **TC-14** | Single status history row per transition | `trg_issue_status_log` logs exactly 1 row when `status_id` changes | Exactly 1 history row logged | **PASS** |
| **TC-15** | Resolution timestamp setting | `trg_issue_resolved_time` populates `resolved_at` on transition to `resolved` | Timestamp populated | **PASS** |
| **TC-16** | Assignment trigger updates issue status | `trg_assignment_status` automatically sets `issues.status_id = 'assigned'` | Status updated | **PASS** |
| **TC-17** | Auto-assignment stored procedure (`assign_least_loaded_technician`) | Deterministically selects least-loaded technician in responsible department | Least-loaded tech selected | **PASS** |
| **TC-18** | Department-isolated technician allocation | IT issue only assigned to CS/IT technician, not Electrical | Correct department isolated | **PASS** |
| **TC-19** | Failed assignment transaction rollback | Non-admin caller causes immediate rollback; zero partial rows written | Rolled back completely | **PASS** |
| **TC-20** | Completed assignments excluded from workload | `v_technician_workload` ignores assignments where `completed_at IS NOT NULL` | Excluded accurately | **PASS** |
| **TC-21** | Delete referenced user integrity guard | Foreign key `ON DELETE RESTRICT` aborts deletion of active reporter | MySQL error 1451 raised | **PASS** |
| **TC-22** | Dashboard metric parity | Total issues card matches manual `SELECT COUNT(*) FROM issues` | Exact count match | **PASS** |
| **TC-23** | Analytical query execution | All 12 analytical queries return non-empty datasets on generated demo data | All 12 queries passed | **PASS** |
| **TC-24** | AI category suggestion for varied descriptions | Tested across 14 facility failure scenarios | 14/14 correctly categorized | **PASS** |
| **TC-25** | AI invalid/short description handling | Rejects inputs < 10 characters | Handled cleanly | **PASS** |
| **TC-26** | Report form works without Bedrock credentials | Fallback heuristic engine classifies and suggests titles locally | 100% functional offline | **PASS** |

---

## 3. Known Limitations & Production Recommendations
1. **Local Media Storage**: Image attachments are currently stored on the local filesystem (`uploads/`) with relative paths stored in MySQL. In a multi-server production deployment, an S3 bucket (or compatible object store) should replace local file storage.
2. **Session Persistence**: Streamlit manages session state in memory per browser tab. User sessions do not persist across full server restarts.
3. **Email Notifications**: The current system audits all status changes in `issue_status_history`. Outbound SMTP email/SMS notification hooks can be attached to the triggers or repository layer for real-time mobile alerts.
