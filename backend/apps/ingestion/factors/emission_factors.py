"""
Emission factors frozen at ingestion time (DEFRA 2023 defaults where cited).
Values are illustrative kgCO2e per activity unit for the prototype.
"""
from decimal import Decimal

EMISSION_FACTOR_SOURCE_DEFRA = "DEFRA 2023"
EMISSION_FACTOR_SOURCE_EGRID = "EPA eGRID 2023"
EMISSION_FACTOR_SOURCE_IEA = "IEA 2022"

# Plant code → ISO country (5 plants per spec)
PLANT_COUNTRY = {
    "DE01": "DE",
    "IN02": "IN",
    "US03": "US",
    "UK04": "GB",
    "SG05": "SG",
}

# SAP material groups treated as Scope 1 fuel (MM fuel-related MATKL examples)
SAP_FUEL_MATKL = frozenset({"1680", "1681", "1682", "1683", "1685", "1686"})

# kgCO2e per litre / kg / m3 by country (DEFRA 2023-style diesel/gas averages)
FUEL_FACTORS_KG_PER_UNIT = {
    "DE": {
        "L": Decimal("2.51230"),   # diesel litres
        "KG": Decimal("2.93320"),
        "M3": Decimal("1.85800"),  # natural gas m3
        "TO": Decimal("2570.0"),   # tonnes
    },
    "IN": {
        "L": Decimal("2.68000"),
        "KG": Decimal("3.01000"),
        "M3": Decimal("1.92000"),
        "TO": Decimal("2650.0"),
    },
    "US": {
        "L": Decimal("2.68710"),
        "KG": Decimal("2.95000"),
        "M3": Decimal("1.90100"),
        "TO": Decimal("2580.0"),
    },
    "GB": {
        "L": Decimal("2.51230"),
        "KG": Decimal("2.93320"),
        "M3": Decimal("1.85800"),
        "TO": Decimal("2570.0"),
    },
    "SG": {
        "L": Decimal("2.62000"),
        "KG": Decimal("2.88000"),
        "M3": Decimal("1.87000"),
        "TO": Decimal("2600.0"),
    },
}

# Scope 3 purchased goods — spend proxy kg/EUR (quantity-only rows use generic factor)
PROCUREMENT_FACTOR_KG_PER_EUR = Decimal("0.00042")

SAP_UNIT_TO_PINT = {
    "L": "liter",
    "KG": "kilogram",
    "M3": "cubic_meter",
    "KWH": "kilowatt_hour",
    "TO": "tonne",
}

# Grid kgCO2e/kWh — location-based (eGRID / IEA style)
GRID_FACTORS_KG_PER_KWH = {
    "US-CA": (Decimal("0.225"), EMISSION_FACTOR_SOURCE_EGRID),
    "US-TX": (Decimal("0.413"), EMISSION_FACTOR_SOURCE_EGRID),
    "US-NY": (Decimal("0.288"), EMISSION_FACTOR_SOURCE_EGRID),
    "US-FL": (Decimal("0.386"), EMISSION_FACTOR_SOURCE_EGRID),
    "US-IL": (Decimal("0.390"), EMISSION_FACTOR_SOURCE_EGRID),
    "IN": (Decimal("0.708"), EMISSION_FACTOR_SOURCE_IEA),
    "GB": (Decimal("0.207"), EMISSION_FACTOR_SOURCE_DEFRA),
}

# Travel — DEFRA 2023
FLIGHT_KG_PER_KM = Decimal("0.15603")  # economy, with RF multiplier embedded
CABIN_MULTIPLIERS = {
    "ECONOMY": Decimal("1.0"),
    "PREMIUM_ECONOMY": Decimal("1.33"),
    "BUSINESS": Decimal("1.54"),
    "FIRST": Decimal("2.40"),
}
HOTEL_SPEND_FACTOR_KG_PER_USD = Decimal("0.507")  # spend-based hotels
GROUND_DISTANCE_FACTOR_KG_PER_KM = Decimal("0.16713")
GROUND_SPEND_FACTOR_KG_PER_USD = Decimal("0.362")
