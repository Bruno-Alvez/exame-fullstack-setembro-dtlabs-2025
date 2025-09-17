from dataclasses import dataclass
from typing import Optional
import structlog

from app.core.config import settings

logger = structlog.get_logger()


@dataclass
class HealthScoreWeights:
    cpu_weight: float = settings.HEALTH_CPU_WEIGHT
    ram_weight: float = settings.HEALTH_RAM_WEIGHT
    temp_weight: float = settings.HEALTH_TEMP_WEIGHT
    disk_weight: float = settings.HEALTH_DISK_WEIGHT
    connectivity_weight: float = settings.HEALTH_CONNECTIVITY_WEIGHT

    def __post_init__(self):
        total_weight = (
            self.cpu_weight + 
            self.ram_weight + 
            self.temp_weight + 
            self.disk_weight + 
            self.connectivity_weight
        )
        
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(
                "Health score weights do not sum to 1.0",
                total_weight=total_weight,
                weights={
                    "cpu": self.cpu_weight,
                    "ram": self.ram_weight,
                    "temp": self.temp_weight,
                    "disk": self.disk_weight,
                    "connectivity": self.connectivity_weight
                }
            )


def normalize_cpu_score(cpu_usage: float) -> float:
    """
    Normalize CPU usage to health score (0-100)
    Lower CPU usage = higher health score
    """
    if cpu_usage <= 20:
        return 100.0
    elif cpu_usage <= 50:
        return 100.0 - (cpu_usage - 20) * 1.5
    elif cpu_usage <= 80:
        return 55.0 - (cpu_usage - 50) * 1.0
    else:
        return max(0.0, 25.0 - (cpu_usage - 80) * 1.25)


def normalize_ram_score(ram_usage: float) -> float:
    """
    Normalize RAM usage to health score (0-100)
    Lower RAM usage = higher health score
    """
    if ram_usage <= 30:
        return 100.0
    elif ram_usage <= 60:
        return 100.0 - (ram_usage - 30) * 1.2
    elif ram_usage <= 85:
        return 64.0 - (ram_usage - 60) * 1.0
    else:
        return max(0.0, 39.0 - (ram_usage - 85) * 2.6)


def normalize_temperature_score(temperature: float) -> float:
    """
    Normalize temperature to health score (0-100)
    Optimal temperature range = higher health score
    """
    if 20 <= temperature <= 40:
        return 100.0
    elif 15 <= temperature < 20:
        return 100.0 - (20 - temperature) * 2.0
    elif 40 < temperature <= 50:
        return 100.0 - (temperature - 40) * 2.0
    elif 10 <= temperature < 15:
        return 90.0 - (15 - temperature) * 3.0
    elif 50 < temperature <= 60:
        return 80.0 - (temperature - 50) * 3.0
    elif 5 <= temperature < 10:
        return 75.0 - (10 - temperature) * 5.0
    elif 60 < temperature <= 70:
        return 50.0 - (temperature - 60) * 5.0
    else:
        return max(0.0, 25.0 - abs(temperature - 35) * 0.5)


def normalize_disk_score(free_disk_space: float) -> float:
    """
    Normalize free disk space to health score (0-100)
    Higher free space = higher health score
    """
    if free_disk_space >= 50:
        return 100.0
    elif free_disk_space >= 30:
        return 100.0 - (50 - free_disk_space) * 1.0
    elif free_disk_space >= 20:
        return 80.0 - (30 - free_disk_space) * 2.0
    elif free_disk_space >= 10:
        return 60.0 - (20 - free_disk_space) * 3.0
    else:
        return max(0.0, 30.0 - (10 - free_disk_space) * 3.0)


def normalize_connectivity_score(connectivity: bool) -> float:
    """
    Normalize connectivity to health score (0-100)
    Online = 100, Offline = 0
    """
    return 100.0 if connectivity else 0.0


def calculate_health_score(
    cpu_usage: float,
    ram_usage: float,
    temperature: float,
    free_disk_space: float,
    connectivity: bool,
    weights: Optional[HealthScoreWeights] = None
) -> float:
    """
    Calculate overall health score based on device metrics
    
    Args:
        cpu_usage: CPU usage percentage (0-100)
        ram_usage: RAM usage percentage (0-100)
        temperature: Temperature in Celsius
        free_disk_space: Free disk space percentage (0-100)
        connectivity: Device connectivity status (True/False)
        weights: Custom weights for each metric
    
    Returns:
        Health score between 0 and 100
    """
    if weights is None:
        weights = HealthScoreWeights()
    
    try:
        # Normalize each metric to 0-100 scale
        cpu_score = normalize_cpu_score(cpu_usage)
        ram_score = normalize_ram_score(ram_usage)
        temp_score = normalize_temperature_score(temperature)
        disk_score = normalize_disk_score(free_disk_space)
        connectivity_score = normalize_connectivity_score(connectivity)
        
        # Calculate weighted average
        health_score = (
            cpu_score * weights.cpu_weight +
            ram_score * weights.ram_weight +
            temp_score * weights.temp_weight +
            disk_score * weights.disk_weight +
            connectivity_score * weights.connectivity_weight
        )
        
        # Ensure score is within bounds
        health_score = max(0.0, min(100.0, health_score))
        
        logger.debug(
            "Health score calculated",
            cpu_usage=cpu_usage,
            ram_usage=ram_usage,
            temperature=temperature,
            free_disk_space=free_disk_space,
            connectivity=connectivity,
            cpu_score=cpu_score,
            ram_score=ram_score,
            temp_score=temp_score,
            disk_score=disk_score,
            connectivity_score=connectivity_score,
            final_score=health_score
        )
        
        return round(health_score, 2)
        
    except Exception as e:
        logger.error(
            "Failed to calculate health score",
            error=str(e),
            cpu_usage=cpu_usage,
            ram_usage=ram_usage,
            temperature=temperature,
            free_disk_space=free_disk_space,
            connectivity=connectivity
        )
        return 0.0


def get_health_status(health_score: float) -> str:
    """
    Get health status based on health score
    
    Args:
        health_score: Health score between 0 and 100
    
    Returns:
        Health status: 'healthy', 'warning', 'critical'
    """
    if health_score >= 80:
        return "healthy"
    elif health_score >= 60:
        return "warning"
    else:
        return "critical"
