# 🏛️ AI-Powered Smart Campus Issue Management System

> **A Complete B.Tech DBMS Course Project demonstrating Advanced Relational Database Design, Normalization (1NF–3NF), Integrity Constraints, Triggers, Views, Stored Procedures, ACID Transactions, and AI Integration with MySQL 8.0 & Streamlit.**

---

## 📖 Table of Contents
1. [Project Overview & Problem Statement](#-project-overview--problem-statement)
2. [Key System Features](#-key-system-features)
3. [Technology Stack](#-technology-stack)
4. [System Architecture & Folder Structure](#-system-architecture--folder-structure)
5. [Database Architecture & Schema (12 Core Tables)](#-database-architecture--schema-12-core-tables)
6. [SQL Features: Triggers, Views & Stored Procedures](#-sql-features-triggers-views--stored-procedures)
7. [AI Module: AWS Bedrock & Structured Output](#-ai-module-aws-bedrock--structured-output)
8. [Installation & Setup Guide](#-installation--setup-guide)
9. [Database Initialization & Demo Data](#-database-initialization--demo-data)
10. [Running the Application](#-running-the-application)
11. [Demo Accounts & Credentials](#-demo-accounts--credentials)
12. [Automated Testing Suite (61 Test Cases)](#-automated-testing-suite-61-test-cases)
13. [Documentation Index & Viva Preparation](#-documentation-index--viva-preparation)

---

## 🎯 Project Overview & Problem Statement

In university environments, infrastructure breakdowns (broken classroom fans, plumbing leaks, laboratory equipment faults, Wi-Fi outages, and washroom sanitation issues) are typically reported via fragmented channels like WhatsApp messages, paper registers, or verbal complaints.

These scattered reporting channels cause:
- Lost and un-tracked facility issues.
- Confusion regarding responsible maintenance departments.
- Unbalanced technician workloads and lack of dispatch accountability.
- Inability to monitor Resolution Service Level Agreements (SLAs).
- Lack of data analytics to identify recurring equipment failures.

The **AI-Powered Smart Campus Issue Management System** provides a centralized, database-driven web platform with role-based access control (Student, Administrator, Technician), automated SLA monitoring, intelligent technician dispatching, and AI-assisted classification.

---

## ✨ Key System Features

### 👨‍🎓 Student & Staff Portal
- **AI-Assisted Issue Reporting**: Students type a complaint; AI analyzes the text and suggests a standardized title and category.
- **Dynamic Department Derivation**: Responsible department is derived strictly from the database schema; never invented by the LLM.
- **Incident Tracking**: Real-time status badges (Open, Assigned, In Progress, Resolved, Closed, Rejected).
- **Audit Timeline**: Inspection of every state change and remarks recorded in `issue_status_history`.
- **Photo Evidence Attachment**: Upload image files (JPG, PNG, WEBP) safely stored on disk.
- **Post-Resolution Feedback**: 1–5 star rating with comments (restricted to reporting student, enforced 1:0..1 cardinality).

### 👨‍💼 Campus Administrator Portal
- **Operations Dashboard**: Live KPI cards and 6 interactive Plotly charts queried directly from MySQL tables and views.
- **SLA Breach Monitoring**: Real-time detection of overdue tickets via database view `v_overdue_issues`.
- **Automated Technician Allocation**: One-click execution of MySQL stored procedure `assign_least_loaded_technician` using pessimistic row locking (`FOR UPDATE`).
- **Manual Dispatch & Reassignment**: Assign specific technicians with transactional integrity.
- **Lifecycle Auditing**: Formally close or reject tickets with recorded justifications.

### 🔧 Technician Work Order Portal
- **Personalized Work Queue**: View tasks assigned to the authenticated technician filtered from `assignments`.
- **Workload Indicator**: Active open tasks gauge derived via `v_technician_workload`.
- **Status Lifecycle Control**: Update ticket to *In Progress* upon arrival, and *Resolved* with mandatory resolution remarks.
- **Automated Resolution Timestamps**: Database trigger automatically records `resolved_at` and task completion time.

---

## 💻 Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend UI** | Python, Streamlit, Plotly Express, Plotly Graph Objects |
| **Backend & ORM** | Python 3.13, MySQL Connector Python, PyMySQL, SQLAlchemy |
| **Database** | MySQL 8.0 (InnoDB Engine, 3NF Normalized, 12 Core Tables) |
| **Security & Auth** | bcrypt (12 salt rounds), Parameterized SQL, Role-Based Access Control |
| **AI Integration** | AWS Bedrock (`Claude 3 Haiku`), LangChain (`langchain-aws`), Pydantic v2 |
| **Testing** | Pytest (61 Automated Tests) |

---

## 📁 System Architecture & Folder Structure

```text
DBMS_project/
│
├── app.py                          # Streamlit application gateway & login screen
├── config.py                       # Central environment variable manager
├── db.py                           # Thread-safe MySQL connection pool & transaction context managers
├── auth.py                         # Bcrypt hashing, session management, and role guards
├── requirements.txt                # Production Python dependencies
├── README.md                       # Comprehensive project documentation
├── .env.example                    # Environment variable template
├── .env                            # Local configuration (Git ignored)
├── .gitignore                      # Git exclusion rules
│
├── pages/                          # Multi-page Streamlit portal
│   ├── 1_Report_Issue.py           # Student complaint submission with AI suggest
│   ├── 2_My_Issues.py              # Student ticket tracking, audit history & feedback
│   ├── 3_Admin_Dashboard.py        # Executive KPI dashboard with Plotly charts
│   ├── 4_Manage_Issues.py          # Admin dispatch, auto-assign proc, close/reject
│   └── 5_Technician_Tasks.py       # Technician work orders & resolution workflow
│
├── ai/                             # AI integration package
│   ├── __init__.py
│   └── suggest.py                  # Bedrock LangChain structured output & local fallback
│
├── services/                       # Business logic service layer
│   ├── __init__.py
│   ├── user_service.py             # User lookup & technician routing
│   ├── issue_service.py            # Issue creation, feedback, and lifecycle validation
│   ├── assignment_service.py       # Manual & auto-dispatch transactions
│   └── analytics_service.py        # SQL aggregations & dataframes for dashboard
│
├── repositories/                   # Data Access Layer (Parameterized SQL)
│   ├── __init__.py
│   ├── user_repository.py          # User queries
│   ├── issue_repository.py         # Issue queries, views, history, feedback
│   └── assignment_repository.py    # Assignment queries & stored procedure runner
│
├── utils/                          # Cross-cutting utilities
│   ├── __init__.py
│   ├── validators.py               # Form, rating & file upload validators
│   ├── file_handler.py             # Secure image upload handler
│   └── ui_helpers.py               # CSS styles, status badges, metrics cards, sidebar
│
├── sql/                            # Database SQL scripts (MySQL 8.0)
│   ├── schema.sql                  # DDL schema for all 12 tables & constraints
│   ├── seed.sql                    # Base master data, departments, locations & users
│   ├── triggers_views_procs.sql    # 3 triggers, 4 views, and auto-assign procedure
│   └── queries.sql                 # 12 analytical DBMS queries
│
├── scripts/                        # Database management & CLI tools
│   ├── db_init.py                  # Automated MySQL migration runner
│   ├── generate_demo_data.py       # Realistic 380+ demo issues generator
│   └── create_admin.py             # CLI admin user creator
│
├── uploads/                        # Image attachments directory (.gitkeep)
│   └── .gitkeep
│
├── docs/                           # University submission & viva documentation
│   ├── database_design.md          # ER diagram, table dictionaries, foreign keys
│   ├── normalization.md            # 1NF, 2NF, 3NF proofs & functional dependencies
│   ├── sql_explanations.md         # Triggers, views, procedures & transaction mechanics
│   ├── ai_architecture.md          # Bedrock prompt design, validation & cost controls
│   ├── testing.md                  # Test scenarios, results matrix & limitations
│   └── viva_questions.md           # 28 comprehensive DBMS viva Q&A
│
└── tests/                          # Automated Pytest suite (61 tests)
    ├── test_sql_objects.py         # Triggers, views, and stored procedure tests
    ├── test_analytics.py           # 12 analytical SQL queries tests
    ├── test_auth.py                # Bcrypt authentication & credential tests
    ├── test_issues.py              # Issue submission & feedback tests
    ├── test_assignments.py         # Manual & technician workflow tests
    ├── test_ai_validation.py       # AI classification & fallback tests
    └── test_e2e_integration.py     # 26 mandatory DBMS requirements tests
```

---

## 🗄️ Database Architecture & Schema (12 Core Tables)

The database strictly satisfies **Third Normal Form (3NF)** with single-attribute surrogate keys, zero transitive dependencies, and enforced foreign keys:

1. **`departments`**: Master table for operational and academic campus units.
2. **`locations`**: Infrastructure master table (`building_name`, `floor`, `room_number`, `location_type`).
3. **`issue_categories`**: Complaint domains mapped via foreign key to default responsible departments.
4. **`priority_levels`**: SLA resolution targets (`Low`: 72 hrs, `Medium`: 48 hrs, `High`: 24 hrs, `Critical`: 6 hrs).
5. **`issue_status`**: Lifecycle states (`open`, `assigned`, `in_progress`, `resolved`, `closed`, `rejected`).
6. **`users`**: Campus actors with bcrypt passwords, active checks, and departmental links for technicians.
7. **`issues`**: Central complaint table with location, category, priority, reporter, and timestamps.
8. **`assignments`**: Technician dispatch records with expected SLA completion and completion timestamps.
9. **`issue_status_history`**: Immutable audit log capturing every state transition, actor, and remarks.
10. **`comments`**: Multi-user discussion thread per issue ticket.
11. **`attachments`**: Evidence photos and image paths linked to complaints (`ON DELETE CASCADE`).
12. **`feedback`**: Post-resolution reporter reviews with `CHECK(rating BETWEEN 1 AND 5)` and `UNIQUE(issue_id)`.

---

## ⚡ SQL Features: Triggers, Views & Stored Procedures

### Triggers
- **`trg_issue_status_log` (`AFTER UPDATE ON issues`)**: Automatically inserts an audit record into `issue_status_history` whenever `status_id` changes.
- **`trg_issue_resolved_time` (`BEFORE UPDATE ON issues`)**: Automatically populates `resolved_at = NOW()` when transitioning to resolved status.
- **`trg_assignment_status` (`AFTER INSERT ON assignments`)**: Automatically synchronizes `issues.status_id = 'assigned'`, which in turn cascades into `trg_issue_status_log`.

### Views
- **`v_open_issues_by_department`**: Departmental backlog summary derived through category mappings.
- **`v_overdue_issues`**: Real-time SLA breach monitor comparing elapsed time against `sla_hours`.
- **`v_technician_workload`**: Active workload calculation per technician excluding resolved and closed tasks.
- **`v_issue_details`**: 7-table joined presentation view used by UI grids and filters.

### Stored Procedure: `assign_least_loaded_technician`
- Accepts `(issue_id, admin_id, OUT technician_id)`.
- Validates administrator authorization.
- Locks the issue row with pessimistic row locking (`SELECT ... FOR UPDATE`).
- Identifies the issue's responsible department.
- Queries active technicians in that department and allocates the technician with the lowest active task count (tie-breaking by `user_id ASC`).
- Commits transaction; automatically rolls back (`ROLLBACK`) on any failure.

---

## 🤖 AI Module: AWS Bedrock & Structured Output

- **Model**: Anthropic Claude 3 Haiku via `ChatBedrockConverse` in `langchain-aws`.
- **Pydantic Schema**:
  ```python
  class IssueSuggestion(BaseModel):
      category: str  # Must match allowed MySQL category
      title: str     # Max 10 words
  ```
- **Strict Department Derivation**: The AI never selects the department. The department is resolved deterministically from MySQL:
  $$\text{issue\_categories} \xrightarrow{\text{default\_department\_id}} \text{departments}$$
- **Prompt Injection Defense**: Untrusted user text is classified as complaint data, neutralizing prompt overrides.
- **Offline Fallback Engine**: If AWS Bedrock is unconfigured or unreachable, a built-in heuristic classifier ensures 100% form uptime.

---

## 🚀 Installation & Setup Guide

### 1. Prerequisites
- Python 3.11, 3.12, or 3.13 installed.
- MySQL Server 8.0 running on `localhost:3306`.
- Git installed.

### 2. Clone Repository & Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/atulkumar-ds/DBMS_project.git
cd DBMS_project

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and enter your MySQL credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=smart_campus
DB_USER=root
DB_PASSWORD=YourMySQLPasswordHere

# AWS Bedrock (Optional - fallback operates if disabled or empty)
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AI_ENABLED=false
```

---

## 💾 Database Initialization & Demo Data

Run the initialization script to create the database, all 12 tables, constraints, indexes, triggers, views, and stored procedures:
```bash
python scripts/db_init.py
```

Generate 380 realistic demo issues spread across the past 80 days with technician assignments, status history timelines, and student feedback:
```bash
python scripts/generate_demo_data.py 380
```

---

## 🖥️ Running the Application

Launch the Streamlit web platform:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🔑 Demo Accounts & Credentials

All seeded demo accounts are hashed using bcrypt. The default password for all demo accounts is:
**`Password@123`**

| Role | Email Address | Department / Notes |
|---|---|---|
| **Administrator** | `admin@campus.edu` | Campus Administration (Full Access) |
| **Technician (Electrical)** | `tech.electrical@campus.edu` | Electrical Dept (User #2) |
| **Technician (Plumbing/Civil)** | `tech.civil@campus.edu` | Civil Dept (User #3) |
| **Technician (IT & Network)** | `tech.network@campus.edu` | Computer Science Dept (User #4) |
| **Technician (Sanitation)** | `tech.cleaning@campus.edu` | Housekeeping Dept (User #5) |
| **Technician (Mechanical)** | `tech.mechanical@campus.edu` | Mechanical Dept (User #6) |
| **Student** | `aarav.sharma@campus.edu` | Student Reporter (User #101) |
| **Student** | `aditi.rao@campus.edu` | Student Reporter (User #102) |

*(An additional 28 student accounts `student1@campus.edu` through `student30@campus.edu` are available with password `Password@123`).*

---

## 🧪 Automated Testing Suite (61 Test Cases)

Run the full automated test suite covering all units, database triggers, views, procedures, analytical queries, authentication, and the 26 mandatory project requirements:

```bash
pytest tests/ -v
```

### Test Coverage Breakdown
- `tests/test_sql_objects.py`: Triggers, views, and stored procedure execution (6 tests).
- `tests/test_analytics.py`: 12 analytical SQL queries verified against live dataset (12 tests).
- `tests/test_auth.py`: Bcrypt hashing, role authentication, invalid credentials (7 tests).
- `tests/test_issues.py`: Issue submission, validation, feedback rules (3 tests).
- `tests/test_assignments.py`: Manual assignment, auto-dispatch, and technician workflows (2 tests).
- `tests/test_ai_validation.py`: 14 varied facility complaint predictions and fallback tests (17 tests).
- `tests/test_e2e_integration.py`: End-to-end verification of all 26 mandatory requirements (14 tests).

**Result**: **61 / 61 tests PASSED** in ~6.4 seconds.

---

## 📚 Documentation Index & Viva Preparation

Comprehensive academic documentation has been prepared in the `docs/` folder:
- **`docs/database_design.md`**: Complete ER diagram (Mermaid), table dictionary, constraints, indexes.
- **`docs/normalization.md`**: Formal 1NF, 2NF, 3NF decomposition and functional dependency proofs.
- **`docs/sql_explanations.md`**: In-depth explanations of all triggers, views, procedures, and transactions.
- **`docs/ai_architecture.md`**: AWS Bedrock integration, prompt defense, and cloud cost management.
- **`docs/testing.md`**: Test cases, expected results, and actual verified test matrix.
- **`docs/viva_questions.md`**: 28 anticipated DBMS viva questions with expert answers.
