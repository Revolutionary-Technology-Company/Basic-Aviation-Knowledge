# schema_validator.py
from pydantic import BaseModel, Field, validator
from typing import Dict

class VehicleConfig(BaseModel):
    vehicle_mass: float = Field(gt=0)
    wing_area: float = Field(gt=0)
    cd0: float = Field(gt=0)
    induced_drag_k: float = Field(gt=0)
    nose_radius: float = Field(gt=0)

class PlanetaryProfile(BaseModel):
    R_p: float = Field(gt=0)
    g0: float = Field(gt=0)
    rho0: float = Field(ge=0) # Can be 0 for space
    H: float = Field(gt=0)

def validate_configuration(config_data: Dict):
    """
    Parses and validates configuration maps.
    Raises ValueError for non-positive numbers or formatting errors.
    """
    # Example validation for vehicle config
    validated = VehicleConfig(**config_data["Starship_Class"])
    return validated
