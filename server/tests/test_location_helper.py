from src.utils.location_helper import normalize_job_location

def test_normalize_job_location():
    # 1. Remote cases
    assert normalize_job_location("Remote") == (None, True, False)
    assert normalize_job_location("Remote, US") == ("US", True, False)
    assert normalize_job_location("Work from home") == (None, True, False)
    assert normalize_job_location("WFH - US") == ("US", True, False)
    
    # 2. Hybrid cases
    assert normalize_job_location("Hybrid - Bangalore") == ("Bangalore", False, True)
    assert normalize_job_location("hybrid, Bengaluru, India") == ("Bengaluru India", False, True)
    
    # 3. On-site cases
    assert normalize_job_location("New York, NY (On-site)") == ("New York NY", False, False)
    assert normalize_job_location("Boston, MA") == ("Boston MA", False, False)
    
    # 4. Hybrid Remote mixed
    # If it lists hybrid and remote, it should identify both flags
    assert normalize_job_location("Remote/Hybrid - Boston") == ("Boston", True, True)

    # 5. Empty and None cases
    assert normalize_job_location(None) == (None, False, False)
    assert normalize_job_location("") == (None, False, False)
    assert normalize_job_location("   ") == (None, False, False)
    assert normalize_job_location("-") == (None, False, False)
