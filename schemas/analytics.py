from pydantic import BaseModel


class SummaryOut(BaseModel):
    total_lanes:      int
    ok_lanes:         int
    warn_lanes:       int
    bad_lanes:        int
    avg_risk:         float | None
    total_nodes:      int
    total_carriers:   int
    total_caretakers: int
    total_users:      int

class RiskDistributionOut(BaseModel):
    low:    int
    medium: int
    high:   int

class ModeBreakdownOut(BaseModel):
    Air:  int
    Road: int
    Sea:  int

class CargoBreakdownOut(BaseModel):
    pharma: int = 0
    hazmat: int = 0
    cold:   int = 0
    air:    int = 0

class CaretakerBreakdownOut(BaseModel):
    Stevedore:         int = 0
    Ground_Handler:    int = 0
    Terminal_Operator: int = 0
    Warehouse_Keeper:  int = 0
    Customs_Agent:     int = 0
    Cold_Store:        int = 0