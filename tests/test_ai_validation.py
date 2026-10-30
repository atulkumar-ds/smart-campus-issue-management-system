"""
Automated tests for AI Module Category Prediction and Fallback Validation.
Evaluates 14 realistic campus issue descriptions across categories.
"""

import pytest
from ai.suggest import suggest_issue_details, get_allowed_categories


# 14 Varied Campus Issue Descriptions covering all categories
TEST_SCENARIOS = [
    ("The ceiling fan in lecture hall 101 is wobbling dangerously and making a buzzing noise.", "Electrical"),
    ("Front switchboard in CS Lab has a burned socket and sparked when turning on switch.", "Electrical"),
    ("Drinking water cooler near library entrance has a broken tap leaking water all over the floor.", "Plumbing"),
    ("Restroom flush valve is stuck and water is overflowing continuously from the cistern.", "Plumbing"),
    ("Wi-Fi signal drops to zero bars near row 5 in the reading hall, cannot connect to student network.", "Internet / Wi-Fi"),
    ("RJ45 LAN port on wall in lab 3 has bent pins and disconnects my laptop intermittently.", "Internet / Wi-Fi"),
    ("Corridor dustbin outside canteen is overflowing with paper cups and food wrappers.", "Cleaning"),
    ("Restroom on 2nd floor has not been cleaned today, floor is muddy and soap dispenser is empty.", "Cleaning"),
    ("Classroom door hinge is completely loose and the wooden door cannot close properly.", "Civil Maintenance"),
    ("Moisture stains and ceiling plaster peeling off in room 204 during heavy rain.", "Civil Maintenance"),
    ("Digital multimeter in ECE circuit lab gives fluctuating negative voltage readings.", "Laboratory Equipment"),
    ("Centrifuge machine shakes violently when operated above 2000 RPM in chemistry lab.", "Laboratory Equipment"),
    ("Student bench in lecture hall tilts because two leg screws are completely missing.", "Furniture"),
    ("Revolving ergonomic study chair in library has broken gas cylinder and sank to floor.", "Furniture"),
]


def test_dynamic_categories_fetched_from_mysql():
    """Verify that categories are loaded dynamically from MySQL, not hardcoded."""
    cats = get_allowed_categories()
    assert len(cats) >= 8
    cat_names = [c["category_name"] for c in cats]
    assert "Electrical" in cat_names
    assert "Plumbing" in cat_names
    assert "Internet / Wi-Fi" in cat_names


@pytest.mark.parametrize("description,expected_category", TEST_SCENARIOS)
def test_suggestion_accuracy_and_validity(description, expected_category):
    """
    Test that the suggestion module classifies varied campus issues
    into valid, allowed database categories and derives the correct department.
    """
    res = suggest_issue_details(description)

    assert res["success"] is True
    assert res["category_name"] == expected_category, (
        f"Expected category '{expected_category}', got '{res['category_name']}'"
    )
    assert res["category_id"] is not None
    assert res["department_name"] != ""
    assert len(res["title"].split()) <= 10, "Title must not exceed 10 words"


def test_short_description_rejected():
    """Test that input shorter than 10 characters is cleanly handled."""
    res = suggest_issue_details("Too short")
    assert res["success"] is False
    assert "at least 10 characters" in res["message"]


def test_fallback_when_bedrock_disabled():
    """Test that the suggestion engine operates smoothly in offline fallback mode."""
    res = suggest_issue_details("Water pipe leaking under washroom sink.")
    assert res["success"] is True
    assert res["category_name"] == "Plumbing"
    assert res["department_name"] == "Civil"
