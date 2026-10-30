-- =====================================================================
-- SMART CAMPUS ISSUE MANAGEMENT SYSTEM - SEED DATA
-- B.Tech DBMS Course Project Master Seed Data
-- =====================================================================

USE smart_campus;

-- 1. Departments
INSERT INTO departments (department_id, department_name) VALUES
(1, 'Electrical'),
(2, 'Civil'),
(3, 'Computer Science & IT'),
(4, 'Mechanical'),
(5, 'Housekeeping'),
(6, 'Administration')
ON DUPLICATE KEY UPDATE department_name = VALUES(department_name);

-- 2. Issue Categories (mapped to responsible default departments)
INSERT INTO issue_categories (category_id, category_name, description, default_department_id) VALUES
(1, 'Electrical', 'Power failure, faulty switches, fans, lights, UPS, wiring', 1),
(2, 'Plumbing', 'Water leakage, pipe burst, tap damage, water cooler issues', 2),
(3, 'Internet / Wi-Fi', 'LAN port broken, Wi-Fi outage, router malfunction, slow network', 3),
(4, 'Cleaning', 'Unclean washrooms, trash overflow, corridor sanitation', 5),
(5, 'Civil Maintenance', 'Wall cracks, broken tiles, ceiling leakage, door/window issues', 2),
(6, 'Laboratory Equipment', 'Damaged lab instruments, workbench power, machine malfunction', 4),
(7, 'Furniture', 'Broken desks, chairs, lecture hall benches, podiums', 6),
(8, 'Other', 'General campus maintenance and administrative requests', 6)
ON DUPLICATE KEY UPDATE category_name = VALUES(category_name), description = VALUES(description), default_department_id = VALUES(default_department_id);

-- 3. Priority Levels (with realistic SLA resolution hours)
INSERT INTO priority_levels (priority_id, level_name, sla_hours) VALUES
(1, 'Low', 72),
(2, 'Medium', 48),
(3, 'High', 24),
(4, 'Critical', 6)
ON DUPLICATE KEY UPDATE level_name = VALUES(level_name), sla_hours = VALUES(sla_hours);

-- 4. Issue Statuses
INSERT INTO issue_status (status_id, status_name, description) VALUES
(1, 'open', 'Issue logged by student or staff; awaiting assignment'),
(2, 'assigned', 'Technician assigned to inspect and resolve'),
(3, 'in_progress', 'Work is actively underway by the technician'),
(4, 'resolved', 'Technician marked task as completed with remarks'),
(5, 'closed', 'Admin or reporter verified and closed the issue ticket'),
(6, 'rejected', 'Issue ticket rejected due to invalid report or duplicate')
ON DUPLICATE KEY UPDATE status_name = VALUES(status_name), description = VALUES(description);

-- 5. Campus Locations (18 realistic campus points)
INSERT INTO locations (location_id, building_name, floor, room_number, location_type) VALUES
(1, 'Aryabhatta Academic Block', 1, 'LH-101', 'classroom'),
(2, 'Aryabhatta Academic Block', 2, 'LH-204', 'classroom'),
(3, 'Aryabhatta Academic Block', 3, 'CS-Lab-1', 'lab'),
(4, 'Aryabhatta Academic Block', 3, 'CS-Lab-2', 'lab'),
(5, 'Visvesvaraya Engineering Block', 0, 'Workshop-A', 'lab'),
(6, 'Visvesvaraya Engineering Block', 1, 'ECE-Lab-3', 'lab'),
(7, 'Visvesvaraya Engineering Block', 2, 'Mech-Lab-2', 'lab'),
(8, 'Central Library', 1, 'Reading Hall A', 'library'),
(9, 'Central Library', 2, 'Digital Resource Lab', 'library'),
(10, 'Boys Hostel 1 (Ganga)', 1, 'Room 112', 'hostel'),
(11, 'Boys Hostel 1 (Ganga)', 3, 'Common Washroom 3F', 'hostel'),
(12, 'Boys Hostel 2 (Yamuna)', 2, 'Room 218', 'hostel'),
(13, 'Girls Hostel (Kaveri)', 1, 'Room 105', 'hostel'),
(14, 'Girls Hostel (Kaveri)', 2, 'Common Washroom 2F', 'hostel'),
(15, 'Student Canteen', 0, 'Dining Area Ground', 'canteen'),
(16, 'Student Canteen', 1, 'Kitchen / Wash Counter', 'canteen'),
(17, 'Sports Complex', 0, 'Indoor Badminton Hall', 'ground'),
(18, 'Administrative Block', 1, 'Dean Office Lounge', 'other')
ON DUPLICATE KEY UPDATE building_name = VALUES(building_name);

-- 6. Users
-- Default password for all seeded users: Password@123
-- Bcrypt Hash: $2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW

-- Admin User
INSERT INTO users (user_id, name, email, password_hash, phone, role, department_id, is_active) VALUES
(1, 'Campus Admin', 'admin@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9876543210', 'admin', 6, TRUE)
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Technicians (across different departments)
INSERT INTO users (user_id, name, email, password_hash, phone, role, department_id, is_active) VALUES
(2, 'Ramesh Sharma (Electrical)', 'tech.electrical@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9876500001', 'technician', 1, TRUE),
(3, 'Suresh Patel (Civil & Plumbing)', 'tech.civil@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9876500002', 'technician', 2, TRUE),
(4, 'Amit Verma (Network & IT)', 'tech.network@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9876500003', 'technician', 3, TRUE),
(5, 'Sunita Devi (Sanitation)', 'tech.cleaning@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9876500004', 'technician', 5, TRUE),
(6, 'Rajesh Rao (Mechanical)', 'tech.mechanical@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9876500005', 'technician', 4, TRUE)
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- 30 Students
INSERT INTO users (user_id, name, email, password_hash, phone, role, department_id, is_active) VALUES
(101, 'Aarav Sharma', 'aarav.sharma@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000101', 'student', NULL, TRUE),
(102, 'Aditi Rao', 'aditi.rao@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000102', 'student', NULL, TRUE),
(103, 'Akash Verma', 'akash.verma@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000103', 'student', NULL, TRUE),
(104, 'Ananya Iyer', 'ananya.iyer@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000104', 'student', NULL, TRUE),
(105, 'Aniket Singh', 'aniket.singh@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000105', 'student', NULL, TRUE),
(106, 'Bhavya Nair', 'bhavya.nair@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000106', 'student', NULL, TRUE),
(107, 'Chirag Mehta', 'chirag.mehta@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000107', 'student', NULL, TRUE),
(108, 'Devika Joshi', 'devika.joshi@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000108', 'student', NULL, TRUE),
(109, 'Gaurav Kulkarni', 'gaurav.k@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000109', 'student', NULL, TRUE),
(110, 'Ishita Gupta', 'ishita.gupta@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000110', 'student', NULL, TRUE),
(111, 'Karan Malhotra', 'karan.m@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000111', 'student', NULL, TRUE),
(112, 'Kavya Pillai', 'kavya.p@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000112', 'student', NULL, TRUE),
(113, 'Manish Tiwari', 'manish.t@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000113', 'student', NULL, TRUE),
(114, 'Neha Deshmukh', 'neha.d@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000114', 'student', NULL, TRUE),
(115, 'Nikhil Pandey', 'nikhil.p@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000115', 'student', NULL, TRUE),
(116, 'Pooja Reddy', 'pooja.r@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000116', 'student', NULL, TRUE),
(117, 'Pranav Bhat', 'pranav.b@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000117', 'student', NULL, TRUE),
(118, 'Priya Soni', 'priya.s@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000118', 'student', NULL, TRUE),
(119, 'Rahul Saxena', 'rahul.s@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000119', 'student', NULL, TRUE),
(120, 'Rhea Sen', 'rhea.sen@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000120', 'student', NULL, TRUE),
(121, 'Rohan Kapoor', 'rohan.k@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000121', 'student', NULL, TRUE),
(122, 'Sakshi Jain', 'sakshi.j@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000122', 'student', NULL, TRUE),
(123, 'Siddharth Roy', 'siddharth.r@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000123', 'student', NULL, TRUE),
(124, 'Sneha Mukherjee', 'sneha.m@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000124', 'student', NULL, TRUE),
(125, 'Tanmay Bhatt', 'tanmay.b@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000125', 'student', NULL, TRUE),
(126, 'Trisha Das', 'trisha.d@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000126', 'student', NULL, TRUE),
(127, 'Utkarsh Mishra', 'utkarsh.m@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000127', 'student', NULL, TRUE),
(128, 'Varun Chawla', 'varun.c@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000128', 'student', NULL, TRUE),
(129, 'Vanya Bansal', 'vanya.b@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000129', 'student', NULL, TRUE),
(130, 'Yash Vardhan', 'yash.v@campus.edu', '$2b$12$qJjpKcWuuU4GqVkjJ/QZzu1u26ulv1ddat62rxNRF8Y2MUMZZ7CkW', '+91 9900000130', 'student', NULL, TRUE)
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Update Department heads
UPDATE departments SET head_user_id = 1 WHERE department_id = 6;
UPDATE departments SET head_user_id = 2 WHERE department_id = 1;
UPDATE departments SET head_user_id = 3 WHERE department_id = 2;
UPDATE departments SET head_user_id = 4 WHERE department_id = 3;
UPDATE departments SET head_user_id = 6 WHERE department_id = 4;
UPDATE departments SET head_user_id = 5 WHERE department_id = 5;
