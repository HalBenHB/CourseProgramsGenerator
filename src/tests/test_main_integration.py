import pytest
import pandas as pd
import json
import os
import hashlib
from pathlib import Path


# Import the code we are testing
from src.main import run_program_generation
from src.config import Config

# --- Test Data Fixtures ---
# These fixtures just prepare our fake data.

@pytest.fixture
def sample_course_data_df():
    """A pytest fixture that provides a sample pandas DataFrame for our fake course file."""
    data = {
        'SUBJECT':    ['CS',  'CS',  'HIST', 'MATH'],
        'COURSENO':   ['101', '101', '200',  '102'],
        'SECTIONNO':  ['A',   'B',   'A',    'A'],
        'TITLE':      ['Intro to CS', 'Intro to CS', 'World History', 'Calculus I'],
        'CREDITS':    [6, 6, 6, 6],
        'FACULTY':    ['Engineering', 'Engineering', 'Arts', 'Sciences'], # <-- ADD THIS LINE
        'INSTRUCTORFULLNAME': ['Prof. Turing', 'Prof. Hopper', 'Prof. Herodotus', 'Prof. Newton'],
        'COREQUISITE': [None, None, None, None],
        'PREREQUISITE': [None, None, None, None],
        'DESCRIPTION': ['Desc', 'Desc', 'Desc', 'Desc'],
        'SCHEDULEFORPRINT': ['Pazartesi | 09.00 - 10.00', 'Salı | 09.00 - 10.00', 'Pazartesi | 09.30 - 10.30', 'Çarşamba | 11.00 - 12.00']
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_requirements_list():
    """A fixture that provides a sample requirements list."""
    return [
        {
            "name": "Compulsory CS",
            "needed": "=1",
            "candidates": ["CS 101.A", "CS 101.B"]  # A or B
        },
        {
            "name": "Compulsory Math",
            "needed": "=1",
            "candidates": ["MATH 102.A"]  # Must take
        }
    ]


# --- The Main Environment Fixture ---
# This is the powerful fixture that builds our entire fake environment.

@pytest.fixture
def test_environment(tmp_path, sample_course_data_df, sample_requirements_list):
    """
    Creates a temporary directory structure with fake data files and returns a
    fully configured Config object pointing to this environment.
    """
    # 1. Create the fake directory structure
    root_dir = tmp_path
    input_dir = root_dir / "data" / "input"
    reqs_dir = input_dir / "reqs"
    cache_dir = input_dir / "caches"
    output_dir = root_dir / "data" / "output"

    for d in [reqs_dir, cache_dir, output_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 2. Create the fake data files
    courses_path = input_dir / "test_courses.xls"
    reqs_path = reqs_dir / "test_reqs.json"
    sample_course_data_df.to_excel(courses_path, index=False)
    with open(reqs_path, 'w') as f:
        json.dump(sample_requirements_list, f)

    # 3. Create a Config object
    config = Config()
    config.paths['root'] = str(root_dir)
    config.input['courses']['basename'] = "test_courses.xls"
    config.input['requirements']['basename'] = "test_reqs.json"
    config.generation_params['min_credit'] = 10
    config.generation_params['max_credit'] = 15
    config.output['report']['enabled'] = False
    config.display_params['sort_key'] = 'total_courses'

    # --- START OF THE FIX ---
    # 4. Dynamically generate and set the cache filepath, just like the GUI does.
    #    This is the crucial step we were missing.
    req_string = json.dumps(sample_requirements_list, sort_keys=True, separators=(',', ':'))
    req_hash = hashlib.sha256(req_string.encode('utf-8')).hexdigest()[:16]
    min_cred = config.generation_params["min_credit"]
    max_cred = config.generation_params["max_credit"]
    cache_filename = f"cache_test_courses_reqs_{req_hash}_cr_{min_cred}-{max_cred}.pkl"

    # Set the FULL cache file path in the config object
    config.input["cache"]["filepath"] = str(cache_dir / cache_filename)
    # --- END OF THE FIX ---

    # 5. Update the config to build all other full paths
    config.update()

    yield config


# --- The Actual Test Functions ---

def test_run_generation_cache_miss(test_environment):
    """
    Tests the main generation logic when no cache exists.
    It should generate the correct, non-conflicting programs.

    - CS 101.A conflicts with HIST 200.A.
    - So, the only valid programs are:
      1. CS 101.A + MATH 102.A
      2. CS 101.B + MATH 102.A
    """
    # ARRANGE: The test_environment fixture has already done all the setup for us!
    config = test_environment
    config.input['cache']['enabled'] = True  # Enable caching

    # ACT: Run the main function
    summarized_programs, log_output, _ = run_program_generation(config)

    # ASSERT: Check the results
    assert "Generating possible programs..." in log_output
    assert "Found 2 possible programs" in log_output
    assert len(summarized_programs) == 2

    # Check that a cache file was actually created
    cache_dir_path = Path(config.paths['cache_dir'])
    cache_files = list(cache_dir_path.glob("*.pkl"))

    assert len(cache_files) == 1


def test_run_generation_cache_hit(test_environment):
    """
    Tests that the application correctly uses the cache on a second run.
    """
    # ARRANGE
    config = test_environment
    config.input['cache']['enabled'] = True

    # ACT - First Run (to generate the cache)
    print("First run (populating cache)...")
    run_program_generation(config)

    # ACT - Second Run (should hit the cache)
    print("Second run (testing cache hit)...")
    summarized_programs, log_output, _ = run_program_generation(config)

    # ASSERT
    assert "Generating possible programs..." not in log_output  # Should NOT generate again
    assert "Cache is valid. Loading programs from cache." in log_output
    assert "Total programs found: 2" in log_output
    assert len(summarized_programs) == 2