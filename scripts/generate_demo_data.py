"""
Demo Data Generation Script for Smart Campus Issue Management System.
Populates 350+ realistic issue records spread across the last 90 days,
complete with status histories, technician assignments, resolution remarks,
and student feedback.
Uses a fixed random seed for 100% reproducible demo datasets.
"""

import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import Config
import mysql.connector

# Set fixed seed for reproducibility
random.seed(42)

# Department to Technician mapping based on seed.sql
# 1: Electrical -> user_id 2 (Ramesh Sharma)
# 2: Civil & Plumbing -> user_id 3 (Suresh Patel)
# 3: Computer Science & IT -> user_id 4 (Amit Verma)
# 4: Mechanical -> user_id 6 (Rajesh Rao)
# 5: Housekeeping -> user_id 5 (Sunita Devi)
# 6: Administration -> user_id 1 (Admin) or 3
DEPT_TECHNICIANS = {
    1: [2],
    2: [3],
    3: [4],
    4: [6],
    5: [5],
    6: [2, 3, 4, 5, 6],
}

# Realistic campus issue templates per category_id
ISSUE_TEMPLATES = {
    1: [  # Electrical
        ("Ceiling fan making rattling noise", "Fan in room oscillates with heavy noise and wobbles dangerous speed.", 2),
        ("Flickering tube light", "The front fluorescent tube light keeps flickering continuously, causing eye strain.", 1),
        ("Power socket burned out", "Wall electrical socket sparked when plugging in laptop and is now blackened and dead.", 3),
        ("Switchboard spark", "Master switch on the classroom board emitted sparks when turned on.", 4),
        ("AC remote not responding and display off", "Split AC unit in the computer lab is completely unresponsive.", 2),
        ("Projector power cable loose", "Ceiling mount projector keeps losing power during lectures.", 3),
        ("UPS beeping continuously", "Backup UPS in the server room is giving a continuous alarm tone.", 4),
        ("Corridor light bulb fused", "Entire 2nd floor east wing corridor is completely dark at night.", 1),
    ],
    2: [  # Plumbing
        ("Water cooler tap leaking continuously", "Drinking water cooler on 1st floor has a broken tap dripping clean water.", 2),
        ("Washroom flush tank not filling", "Flush cistern in washroom does not refill with water after flush.", 2),
        ("Low water pressure in taps", "Very slow trickle of water in all third floor handwash basins.", 1),
        ("Drainage blockage causing overflow", "Sink drainage is completely choked with debris and overflowing onto floor.", 3),
        ("Overhead tank pipe burst", "Major water leakage from main supply pipe near hostel terrace.", 4),
        ("Restroom tap knob broken off", "Water tap knob snapped off completely, unable to stop the water flow.", 3),
        ("Foul smell from floor trap", "Floor drain trap dry and emitting sewer odor into laboratory area.", 2),
    ],
    3: [  # Internet / Wi-Fi
        ("Wi-Fi dead zone in corner area", "Signal drops to zero bars near rows 4 and 5 in the reading room.", 2),
        ("LAN port physically damaged", "RJ45 ethernet wall port has bent pins and cannot hold network cable.", 2),
        ("High packet loss and latency", "Lab 2 network has 40% packet loss making practical coding submissions fail.", 3),
        ("Wi-Fi authentication gateway timeout", "Campus portal login page does not load when connected to student Wi-Fi.", 3),
        ("Access Point blinking red LED", "Ceiling mounted AP in library 2nd floor is offline.", 4),
        ("DNS resolution failure", "Cannot access internal college intranet or moodle server over LAN.", 3),
        ("Slow bandwidth during peak hours", "Speed test shows under 500kbps during 2PM-5PM lab sessions.", 1),
    ],
    4: [  # Cleaning
        ("Overflowing dustbins in corridor", "Trash bin outside lecture hall is overflowing with plastic bottles and cups.", 1),
        ("Washroom floor wet and muddy", "Washroom floor has not been mopped today and has footprints and mud.", 2),
        ("Staircase dusty and littered", "Stairwell between 2nd and 3rd floor needs thorough sweeping and cleanup.", 1),
        ("Soap dispensers empty in washroom", "All liquid soap dispensers in the main academic block restrooms are dry.", 1),
        ("Window glass panes stained and dusty", "Classroom windows accumulated thick dust layers blocking daylight.", 1),
        ("Food waste spilled near canteen stairs", "Spilled gravy and food packets attracting stray animals near canteen.", 2),
    ],
    5: [  # Civil Maintenance
        ("Window latch broken", "Classroom window swings open violently in wind because the latch is missing.", 2),
        ("Ceiling plaster peeling off", "Small chunks of ceiling plaster fell onto desk during heavy rain.", 3),
        ("Door hinge loose and jamming", "Room wooden door scrapes against floor tile and cannot be closed properly.", 2),
        ("Broken floor tile hazard", "Cracked floor tile near lab entrance has sharp edge posing tripping risk.", 3),
        ("Rainwater seepage on external wall", "Damp water stains and moisture bubbling the paint on North wall.", 2),
        ("Door lock cylinder jammed", "Key gets stuck inside the lock cylinder of laboratory storage cupboard.", 2),
    ],
    6: [  # Laboratory Equipment
        ("Microscope optical lens clouded", "Stage adjustment knob on compound microscope #4 is jammed and lens is dirty.", 2),
        ("Digital multimeter giving erratic readings", "Multimeter in ECE lab shows fluctuating voltages regardless of circuit.", 2),
        ("Soldering station temperature control broken", "Station heats up to maximum uncontrollably, burning test boards.", 3),
        ("Centrifuge machine excessive vibration", "Lab centrifuge shakes violently when spun above 2000 RPM.", 4),
        ("Oscilloscope channel 2 probe dead", "Channel 2 BNC connector loose, signal flatlines intermittently.", 3),
        ("Weighing balance calibration off", "Electronic analytical balance shows 5g offset and fails tare calibration.", 2),
    ],
    7: [  # Furniture
        ("Desk bench leg screw missing", "Student bench wobbles significantly and tilts when sat on.", 1),
        ("Lectern podium mic holder snapped", "Wooden podium in seminar hall has cracked surface and broken mount.", 2),
        ("Library ergonomic chair height adjustment broken", "Gas cylinder of revolving study chair collapsed to lowest height.", 1),
        ("Whiteboard frame detached from wall", "Magnetic whiteboard top right mounting screw pulled out of wall.", 3),
        ("Lab stool wooden seat split", "Wooden stool top in physics lab has a long crack that pinches clothing.", 1),
    ],
    8: [  # Other
        ("Notice board glass slider locked without key", "Cannot pin new exam schedule on the departmental notice board.", 1),
        ("Classroom wall clock stopped working", "Wall clock stuck at 10:15, needs battery replacement.", 1),
        ("Lost and found item reported", "Student found a scientific calculator left behind on desk LH-101.", 1),
        ("Air cooler water pump not turning on", "Cooler fan works but water circulation pump is dead.", 2),
    ],
}

RESOLUTION_REMARKS = [
    "Replaced faulty component with a new certified unit from departmental inventory. Tested and verified normal operation.",
    "Repaired loose wiring contact, tightened terminal screws, and confirmed voltage stability under full load.",
    "Unclogged the drainage line using mechanical auger and chemical descaler. Full water flow restored.",
    "Firmware reset and re-terminated RJ45 connector. Ping test shows 1ms latency and zero packet loss.",
    "Deep cleaned and sanitized the entire area with disinfectant. Trash emptied and fresh bin liners placed.",
    "Replaced damaged door hinge and adjusted alignment. Latch now secures smoothly.",
    "Calibrated instrument against standard reference sample. Verified all channels functional.",
    "Tightened frame bolts and added reinforcement bracket. Weight tested safely.",
    "Resolved quickly and confirmed working with the reporting department faculty.",
]

FEEDBACK_COMMENTS = [
    (5, "Very prompt service! The technician arrived within hours and fixed it completely."),
    (5, "Excellent work. Fully satisfied with the repair and technician's polite behavior."),
    (4, "Good job. Resolved on the same day as promised."),
    (4, "Working properly now. Appreciate the swift turnaround time."),
    (3, "Fixed adequately, but it took a bit longer than the expected SLA time."),
    (3, "Work was completed, but some cleanup was left for students to handle."),
    (2, "Took over three days to get assigned and resolved. Please speed up response."),
    (1, "The repair was poorly done; problem recurred within two days."),
]


def generate_demo_dataset(target_count: int = 360):
    """Generates realistic demo dataset directly into smart_campus MySQL database."""
    print(f"Connecting to MySQL ({Config.DB_NAME})...")
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=False,
    )
    cursor = conn.cursor(dictionary=True)

    # 1. Fetch categories and default departments
    cursor.execute("SELECT category_id, default_department_id FROM issue_categories;")
    categories = cursor.fetchall()
    cat_dept_map = {c["category_id"]: c["default_department_id"] for c in categories}

    # 2. Fetch locations
    cursor.execute("SELECT location_id FROM locations;")
    location_ids = [r["location_id"] for r in cursor.fetchall()]

    # 3. Fetch students
    cursor.execute("SELECT user_id FROM users WHERE role = 'student';")
    student_ids = [r["user_id"] for r in cursor.fetchall()]

    # 4. Fetch admin
    cursor.execute("SELECT user_id FROM users WHERE role = 'admin' LIMIT 1;")
    admin_id = cursor.fetchone()["user_id"]

    # 5. Fetch priority SLAs
    cursor.execute("SELECT priority_id, sla_hours FROM priority_levels;")
    priority_slas = {r["priority_id"]: r["sla_hours"] for r in cursor.fetchall()}

    now = datetime.now()
    start_date = now - timedelta(days=80)

    print(f"Generating {target_count} realistic issues distributed across past 80 days...")

    # We want realistic status distribution:
    # ~50% resolved
    # ~20% closed
    # ~12% in_progress
    # ~10% assigned
    # ~5% open
    # ~3% rejected
    status_weights = [
        ("open", 1, 0.06),
        ("assigned", 2, 0.10),
        ("in_progress", 3, 0.12),
        ("resolved", 4, 0.50),
        ("closed", 5, 0.18),
        ("rejected", 6, 0.04),
    ]

    statuses_choices = []
    for s_name, s_id, weight in status_weights:
        statuses_choices.extend([(s_name, s_id)] * int(weight * 100))

    # Disable assignment trigger temporarily for bulk history control so we can inject historical timestamps accurately
    cursor.execute("SET @disable_triggers = 1;")

    inserted_count = 0
    for i in range(target_count):
        cat_id = random.choice(list(ISSUE_TEMPLATES.keys()))
        templates = ISSUE_TEMPLATES[cat_id]
        title, desc, default_priority = random.choice(templates)
        dept_id = cat_dept_map[cat_id]
        loc_id = random.choice(location_ids)
        reporter_id = random.choice(student_ids)

        # Spread created_at across past 80 days
        random_days_ago = random.uniform(0.1, 78)
        created_at = now - timedelta(days=random_days_ago, hours=random.uniform(0, 23))

        # Priority (allow slight variance)
        priority_id = random.choices(
            [1, 2, 3, 4],
            weights=[0.30, 0.40, 0.20, 0.10],
            k=1,
        )[0]
        sla_hours = priority_slas[priority_id]

        status_name, status_id = random.choice(statuses_choices)

        # For very recent issues (< 1 day old), favor open/assigned/in_progress
        if random_days_ago < 1.0 and status_id in (4, 5):
            status_name, status_id = random.choice([("open", 1), ("assigned", 2), ("in_progress", 3)])

        resolved_at = None
        if status_id in (4, 5):
            # Resolved or closed: resolve after realistic time (sometimes within SLA, sometimes breach)
            breach = random.random() < 0.22  # 22% breach rate
            if breach:
                duration_hours = sla_hours + random.uniform(2, 48)
            else:
                duration_hours = random.uniform(1.0, sla_hours * 0.85)

            resolved_time = created_at + timedelta(hours=duration_hours)
            if resolved_time > now:
                resolved_time = now - timedelta(minutes=random.randint(10, 120))
            resolved_at = resolved_time

        updated_at = resolved_at if resolved_at else created_at + timedelta(hours=random.uniform(0.5, 4))
        if updated_at > now:
            updated_at = now

        # Insert issue
        cursor.execute(
            """
            INSERT INTO issues (title, description, reported_by, category_id, location_id, priority_id, status_id, created_at, updated_at, resolved_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                title,
                desc,
                reporter_id,
                cat_id,
                loc_id,
                priority_id,
                status_id,
                created_at,
                updated_at,
                resolved_at,
            ),
        )
        issue_id = cursor.lastrowid

        # 1. Initial Status History: 'open'
        cursor.execute(
            """
            INSERT INTO issue_status_history (issue_id, old_status_id, new_status_id, changed_by, changed_at, remarks)
            VALUES (%s, NULL, 1, %s, %s, 'Issue logged by student.');
            """,
            (issue_id, reporter_id, created_at),
        )

        # Eligible technicians for this department
        eligible_techs = DEPT_TECHNICIANS.get(dept_id, [2])
        assigned_tech = random.choice(eligible_techs)

        # If issue advanced beyond open
        if status_id in (2, 3, 4, 5):
            assigned_time = created_at + timedelta(hours=random.uniform(0.5, 6))
            expected_comp = assigned_time + timedelta(hours=sla_hours)
            completed_time = resolved_at if status_id in (4, 5) else None

            # Insert Assignment
            cursor.execute(
                """
                INSERT INTO assignments (issue_id, assigned_to, assigned_by, assigned_at, expected_completion, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (issue_id, assigned_tech, admin_id, assigned_time, expected_comp, completed_time),
            )

            # History: open -> assigned
            cursor.execute(
                """
                INSERT INTO issue_status_history (issue_id, old_status_id, new_status_id, changed_by, changed_at, remarks)
                VALUES (%s, 1, 2, %s, %s, 'Assigned to departmental technician.');
                """,
                (issue_id, admin_id, assigned_time),
            )

            # If in_progress, resolved, or closed, update the issue status to reflect lifecycle progression
            if status_id == 3:  # in_progress
                cursor.execute(
                    "UPDATE issues SET status_id = 3, updated_at = %s WHERE issue_id = %s;",
                    (created_at + timedelta(hours=1), issue_id)
                )
            elif status_id in (4, 5):  # resolved or closed
                cursor.execute(
                    "UPDATE issues SET status_id = %s, updated_at = %s, resolved_at = %s WHERE issue_id = %s;",
                    (status_id, updated_at, resolved_at, issue_id)
                )
                progress_time = assigned_time + timedelta(hours=random.uniform(0.5, 3))
                cursor.execute(
                    """
                    INSERT INTO issue_status_history (issue_id, old_status_id, new_status_id, changed_by, changed_at, remarks)
                    VALUES (%s, 2, 3, %s, %s, 'Technician began inspection and repair.');
                    """,
                    (issue_id, assigned_tech, progress_time),
                )

            # If resolved or closed
            if status_id in (4, 5):
                res_remark = random.choice(RESOLUTION_REMARKS)
                cursor.execute(
                    """
                    INSERT INTO issue_status_history (issue_id, old_status_id, new_status_id, changed_by, changed_at, remarks)
                    VALUES (%s, 3, 4, %s, %s, %s);
                    """,
                    (issue_id, assigned_tech, resolved_at, res_remark),
                )

                # If closed
                if status_id == 5:
                    closed_time = resolved_at + timedelta(hours=random.uniform(1, 12))
                    if closed_time > now:
                        closed_time = now
                    cursor.execute(
                        """
                        INSERT INTO issue_status_history (issue_id, old_status_id, new_status_id, changed_by, changed_at, remarks)
                        VALUES (%s, 4, 5, %s, %s, 'Issue verified and ticket officially closed by campus administrator.');
                        """,
                        (issue_id, admin_id, closed_time),
                    )

                # Feedback: ~70% of resolved/closed issues have student feedback
                if random.random() < 0.72:
                    rating, fb_comment = random.choice(FEEDBACK_COMMENTS)
                    fb_time = resolved_at + timedelta(hours=random.uniform(1, 24))
                    if fb_time > now:
                        fb_time = now
                    cursor.execute(
                        """
                        INSERT INTO feedback (issue_id, user_id, rating, feedback_text, submitted_at)
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        (issue_id, reporter_id, rating, fb_comment, fb_time),
                    )

        elif status_id == 6:  # rejected
            reject_time = created_at + timedelta(hours=random.uniform(1, 8))
            cursor.execute(
                """
                INSERT INTO issue_status_history (issue_id, old_status_id, new_status_id, changed_by, changed_at, remarks)
                VALUES (%s, 1, 6, %s, %s, 'Issue rejected: Duplicate entry or insufficient detail provided.');
                """,
                (issue_id, admin_id, reject_time),
            )

        # Optional comments (~25% of issues)
        if random.random() < 0.28:
            comment_time = created_at + timedelta(hours=random.uniform(0.2, 5))
            comment_user = random.choice([reporter_id, assigned_tech if status_id != 1 else admin_id])
            comments_pool = [
                "Could you please expedite this? It's affecting classroom lectures.",
                "Technician visited the site to inspect the required parts.",
                "Replacement parts have been requested from central stores.",
                "Please ensure the room is unlocked during afternoon inspection.",
                "Thank you for the quick follow up on this ticket.",
            ]
            cursor.execute(
                """
                INSERT INTO comments (issue_id, user_id, comment_text, created_at)
                VALUES (%s, %s, %s, %s);
                """,
                (issue_id, comment_user, random.choice(comments_pool), comment_time),
            )

        inserted_count += 1
        if inserted_count % 50 == 0:
            print(f"  Inserted {inserted_count} / {target_count} issues...")

    conn.commit()

    # Verify counts
    cursor.execute("SELECT COUNT(*) AS total_issues FROM issues;")
    tot_issues = cursor.fetchone()["total_issues"]

    cursor.execute("SELECT s.status_name, COUNT(*) AS count FROM issues i JOIN issue_status s ON i.status_id = s.status_id GROUP BY s.status_name;")
    status_breakdown = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total_assignments FROM assignments;")
    tot_assign = cursor.fetchone()["total_assignments"]

    cursor.execute("SELECT COUNT(*) AS total_feedback FROM feedback;")
    tot_fb = cursor.fetchone()["total_feedback"]

    cursor.execute("SELECT COUNT(*) AS total_history FROM issue_status_history;")
    tot_hist = cursor.fetchone()["total_history"]

    print("\n" + "="*50)
    print("DEMO DATASET GENERATION COMPLETE")
    print("="*50)
    print(f"Total Issues in Database:      {tot_issues}")
    print(f"Total Assignments Created:     {tot_assign}")
    print(f"Total Status History Entries:  {tot_hist}")
    print(f"Total Feedback Records:        {tot_fb}")
    print("\nStatus Breakdown:")
    for row in status_breakdown:
        print(f"  - {row['status_name']:<15}: {row['count']}")
    print("="*50)

    cursor.close()
    conn.close()
    return True


if __name__ == "__main__":
    count = 360
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    generate_demo_dataset(count)
