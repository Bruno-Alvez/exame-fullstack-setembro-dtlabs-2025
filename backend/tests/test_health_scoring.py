import pytest
from app.services.health_scoring import (
    calculate_health_score,
    normalize_cpu_score,
    normalize_ram_score,
    normalize_temperature_score,
    normalize_disk_score,
    normalize_connectivity_score,
    get_health_status
)


class TestHealthScoring:
    
    def test_normalize_cpu_score(self):
        assert normalize_cpu_score(0) == 100.0
        assert normalize_cpu_score(20) == 100.0
        assert normalize_cpu_score(50) == 55.0
        assert normalize_cpu_score(80) == 25.0
        assert normalize_cpu_score(100) == 0.0
    
    def test_normalize_ram_score(self):
        assert normalize_ram_score(0) == 100.0
        assert normalize_ram_score(30) == 100.0
        assert normalize_ram_score(60) == 64.0
        assert normalize_ram_score(85) == 39.0
        assert normalize_ram_score(100) == 0.0
    
    def test_normalize_temperature_score(self):
        assert normalize_temperature_score(30) == 100.0  # Optimal range
        assert normalize_temperature_score(20) == 100.0  # Optimal range
        assert normalize_temperature_score(40) == 100.0  # Optimal range
        assert normalize_temperature_score(50) == 80.0   # Slightly high
        assert normalize_temperature_score(70) == 0.0    # Very high
    
    def test_normalize_disk_score(self):
        assert normalize_disk_score(100) == 100.0
        assert normalize_disk_score(50) == 100.0
        assert normalize_disk_score(30) == 80.0
        assert normalize_disk_score(20) == 60.0
        assert normalize_disk_score(10) == 30.0
        assert normalize_disk_score(0) == 0.0
    
    def test_normalize_connectivity_score(self):
        assert normalize_connectivity_score(True) == 100.0
        assert normalize_connectivity_score(False) == 0.0
    
    def test_calculate_health_score_healthy(self):
        score = calculate_health_score(
            cpu_usage=20,
            ram_usage=30,
            temperature=30,
            free_disk_space=80,
            connectivity=True
        )
        assert score >= 80
    
    def test_calculate_health_score_critical(self):
        score = calculate_health_score(
            cpu_usage=90,
            ram_usage=95,
            temperature=80,
            free_disk_space=5,
            connectivity=False
        )
        assert score < 40
    
    def test_calculate_health_score_warning(self):
        score = calculate_health_score(
            cpu_usage=60,
            ram_usage=70,
            temperature=50,
            free_disk_space=30,
            connectivity=True
        )
        assert 40 <= score < 80
    
    def test_get_health_status(self):
        assert get_health_status(90) == "healthy"
        assert get_health_status(70) == "warning"
        assert get_health_status(30) == "critical"
    
    def test_health_score_bounds(self):
        # Test edge cases
        score = calculate_health_score(
            cpu_usage=0,
            ram_usage=0,
            temperature=20,
            free_disk_space=100,
            connectivity=True
        )
        assert 0 <= score <= 100
        
        score = calculate_health_score(
            cpu_usage=100,
            ram_usage=100,
            temperature=100,
            free_disk_space=0,
            connectivity=False
        )
        assert 0 <= score <= 100
