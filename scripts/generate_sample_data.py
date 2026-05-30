#!/usr/bin/env python3
"""Generate realistic sample files for Breathe ESG prototype."""
import csv
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "sample_data"
OUT.mkdir(exist_ok=True)

# ── SAP ME2M flat export (semicolon, German client) ─────────────────────────
SAP_HEADER = [
    "MANDT", "BUKRS", "WERKS", "MATNR", "MATKL", "MENGE", "MEINS",
    "NETWR", "WAERS", "BLDAT", "BKTXT", "LIFNR",
]

sap_rows = [
    # Fuel Scope 1 — diesel DE plant
    ["100", "1000", "DE01", "10001234", "1680", "4250.75", "L", "8925.50", "EUR", "20240115", "Diesel Kraftstoff Werk Frankfurt", "0000100234"],
    ["100", "1000", "DE01", "10001234", "1680", "1.234,56", "L", "2589,12", "EUR", "15.02.2024", "Diesel Tankstelle Lieferung", "0000100234"],
    ["100", "1000", "DE01", "10005678", "1681", "850.000", "M3", "12450.00", "EUR", "20240228", "Erdgas Heizung Gebäude A", "0000100891"],
    ["100", "1000", "DE01", "10009901", "1682", "12.5", "TO", "18750.00", "EUR", "20240310", "Heizöl Notreserve", "0000100445"],
    # India plant — mixed units
    ["100", "1000", "IN02", "20001234", "1680", "12500", "L", "425000.00", "INR", "20240120", "HSD for DG sets Pune campus", "0000200112"],
    ["100", "1000", "IN02", "20003456", "1683", "450.5", "KG", "89200.00", "INR", "12.03.2024", "LPG cylinder bulk supply", "0000200334"],
    ["100", "1000", "IN02", "20007890", "1685", "0", "L", "0.00", "INR", "20240405", "Cancelled fuel requisition", "0000200112"],  # anomaly: zero qty
    # US plant
    ["100", "1000", "US03", "30001234", "1680", "3200.00", "L", "12800.00", "USD", "20240214", "On-road diesel fleet Houston", "0000300567"],
    ["100", "1000", "US03", "30004567", "1686", "125000", "KWH", "14500.00", "USD", "20240301", "Natural gas utility tie-in", "0000300789"],
    # Procurement Scope 3
    ["100", "1000", "DE01", "40001234", "2100", "500", "KG", "2450.00", "EUR", "20240125", "Stahlblech 2mm Lieferung", "0000400123"],
    ["100", "1000", "DE01", "40005678", "3400", "1200", "KG", "9600.00", "EUR", "15.01.2024", "Verpackungsmaterial Karton", "0000400567"],
    ["100", "1000", "IN02", "40009901", "4500", "85", "ST", "12750.00", "INR", "20240220", "IT Hardware Laptops batch", "0000400999"],  # anomaly: ST unit
    ["100", "1000", "US03", "40003333", "2100", "2500", "KG", "-1250.00", "USD", "20240318", "Credit memo steel return", "0000400333"],  # anomaly: negative
    ["100", "1000", "UK04", "40004444", "3400", "340", "KG", "1700.00", "GBP", "20240401", "Office supplies Q1", "0000400444"],
    ["100", "1000", "SG05", "40005555", "4500", "200", "KG", "8900.00", "SGD", "20240410", "Semiconductor components", "0000400555"],
]

# Pad to 50 rows with realistic variation
materials_fuel = [
    ("1680", "10001234", "L", "Diesel"),
    ("1681", "10005678", "M3", "Natural gas"),
    ("1682", "10009901", "TO", "Heating oil"),
    ("1683", "20003456", "KG", "LPG"),
]
materials_proc = [
    ("2100", "40001234", "KG", "Steel sheet"),
    ("3400", "40005678", "KG", "Packaging"),
    ("4500", "40009901", "KG", "Components"),
]
plants = ["DE01", "IN02", "US03", "UK04", "SG05"]
vendors = ["0000100234", "0000200112", "0000300567", "0000400123", "0000400567"]

import random
random.seed(42)
while len(sap_rows) < 50:
    i = len(sap_rows)
    plant = plants[i % len(plants)]
    is_fuel = i % 4 != 3
    if is_fuel:
        matkl, matnr, unit, desc = random.choice(materials_fuel)
    else:
        matkl, matnr, unit, desc = random.choice(materials_proc)
    qty = random.choice(["125.5", "890", "2.450,00", "1500", "75.25"])
    netwr = random.randint(500, 45000)
    bldat = random.choice(["20240315", "22.03.2024", "20240408", "08.04.2024"])
    sap_rows.append([
        "100", "1000", plant, matnr, matkl, qty, unit, str(netwr), "EUR",
        bldat, f"{desc} PO-{1000+i}", random.choice(vendors),
    ])

with open(OUT / "sap_me2m_export.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(SAP_HEADER)
    w.writerows(sap_rows)

# ── Utility portal CSV (PG&E / National Grid / Tata style) ───────────────────
UTIL_HEADER = [
    "account_number", "meter_id", "service_address", "billing_period_start",
    "billing_period_end", "kwh_consumed", "on_peak_kwh", "off_peak_kwh",
    "demand_kw", "tariff_code", "total_charges_usd", "state_region",
]

meters = [
    ("482-0192-8841", "E-4829182-A", "1200 Technology Blvd, Austin TX 78701", "US-TX", "E-19 TOU"),
    ("019-4421-0038", "NG-NYC-88421", "350 Fifth Avenue, New York NY 10118", "US-NY", "SC-9 General"),
    ("TP-MH-8847291", "TATA-PUN-01", "Hinjawadi Phase 2, Pune MH 411057", "IN", "LT-Industrial"),
]

urows = []
base = date(2024, 1, 1)
for m_idx, (acct, mid, addr, region, tariff) in enumerate(meters):
    period_start = base
    for month in range(12):
        if month == 6 and m_idx == 0:
            period_end = period_start + timedelta(days=37)  # long period anomaly
        elif month == 11:
            period_end = date(2025, 1, 4)  # cross calendar year
        else:
            period_end = period_start + timedelta(days=random.randint(28, 32))

        base_kwh = 14500 + month * 180 + m_idx * 800
        if month == 9 and m_idx == 0:
            kwh = 78200  # spike anomaly (~5x)
        else:
            kwh = base_kwh

        on_peak = int(kwh * 0.62)
        off_peak = kwh - on_peak
        demand = random.randint(38, 125)
        charges = round(kwh * 0.12 + demand * 8.5, 2)

        urows.append([
            acct, mid, addr,
            period_start.isoformat(), period_end.isoformat(),
            str(kwh), str(on_peak), str(off_peak),
            str(demand), tariff, str(charges), region,
        ])
        period_start = period_end + timedelta(days=1)

with open(OUT / "utility_meter_export.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(UTIL_HEADER)
    w.writerows(urows)

# ── Concur Expense TRX extract ───────────────────────────────────────────────
TRAVEL_HEADER = [
    "EmployeeID", "ReportID", "ExpenseType", "TransactionDate", "Amount", "Currency",
    "VendorName", "Origin_Airport", "Destination_Airport", "CabinClass", "CarrierCode",
    "TripType", "PropertyName", "City", "CheckIn", "CheckOut", "RoomNights",
    "VendorType", "Distance_km", "PickupCity", "DropCity",
]

travel = [
    # Flights
    ["E10294", "RPT-2024-00821", "Airfare", "2024-01-22", "1248.50", "USD", "United Airlines", "SFO", "ORD", "Economy", "UA", "One-Way", "", "", "", "", "", "", "", "", ""],
    ["E10294", "RPT-2024-00821", "Airfare", "2024-01-28", "1189.00", "USD", "United Airlines", "ORD", "SFO", "Economy", "UA", "Return", "", "", "", "", "", "", "", "", ""],
    ["E20441", "RPT-2024-01204", "Airfare", "2024-02-14", "4892.00", "USD", "Lufthansa", "FRA", "SIN", "Business", "LH", "One-Way", "", "", "", "", "", "", "", "", ""],
    ["E20441", "RPT-2024-01204", "Airfare", "2024-02-28", "892.00", "USD", "Singapore Airlines", "SIN", "DEL", "Premium Economy", "SQ", "One-Way", "", "", "", "", "", "", "", "", ""],
    ["E30102", "RPT-2024-01567", "Airfare", "2024-03-05", "756.00", "USD", "British Airways", "LHR", "JFK", "", "BA", "One-Way", "", "", "", "", "", "", "", "", ""],  # missing cabin
    ["E30102", "RPT-2024-01567", "Airfare", "2024-03-05", "756.00", "USD", "British Airways", "JFK", "JFK", "Economy", "BA", "Return", "", "", "", "", "", "", "", "", ""],  # same-day return anomaly
    ["E10294", "RPT-2024-02001", "Airfare", "2024-04-18", "2100.00", "USD", "Emirates", "DXB", "LHR", "First", "EK", "One-Way", "", "", "", "", "", "", "", "", ""],
    ["E20441", "RPT-2024-02234", "Airfare", "2024-05-02", "445.00", "USD", "IndiGo", "DEL", "BOM", "Economy", "6E", "One-Way", "", "", "", "", "", "", "", "", ""],
    ["E30102", "RPT-2024-02456", "Airfare", "2024-06-10", "1680.00", "USD", "Delta", "ATL", "LAX", "Economy", "DL", "One-Way", "", "", "", "", "", "", "", "", ""],
    ["E10294", "RPT-2024-02890", "Airfare", "2024-07-22", "920.00", "USD", "American Airlines", "DFW", "MIA", "Economy", "AA", "One-Way", "", "", "", "", "", "", "", "", ""],
    ["E20441", "RPT-2024-03102", "Airfare", "2024-08-15", "1340.00", "USD", "Air France", "CDG", "JFK", "Business", "AF", "One-Way", "", "", "", "", "", "", "", "", ""],
    ["E30102", "RPT-2024-03345", "Airfare", "2024-09-08", "580.00", "USD", "Southwest", "DEN", "PHX", "Economy", "WN", "One-Way", "", "", "", "", "", "", "", "", ""],
    # Hotels
    ["E10294", "RPT-2024-00821", "Hotel", "2024-01-23", "892.40", "USD", "Marriott", "", "", "", "", "", "Chicago Marriott Downtown", "Chicago", "2024-01-22", "2024-01-25", "3", "", "", "", ""],
    ["E20441", "RPT-2024-01204", "Hotel", "2024-02-15", "2450.00", "USD", "Raffles", "", "", "", "", "", "Raffles Singapore", "Singapore", "2024-02-14", "2024-02-17", "3", "", "", "", ""],
    ["E30102", "RPT-2024-01567", "Lodging", "2024-03-06", "3200.00", "USD", "Four Seasons", "", "", "", "", "", "Four Seasons NYC", "New York", "2024-03-05", "2024-03-07", "2", "", "", "", ""],  # high spend
    ["E10294", "RPT-2024-02001", "Hotel", "2024-04-19", "445.00", "USD", "Hilton", "", "", "", "", "", "Hilton Munich City", "Munich", "2024-04-18", "2024-04-20", "", "", "", "", ""],  # missing room nights
    ["E20441", "RPT-2024-02234", "Hotel", "2024-05-03", "156.00", "USD", "OYO", "", "", "", "", "", "OYO Townhouse", "Mumbai", "2024-05-02", "2024-05-03", "1", "", "", "", ""],
    ["E30102", "RPT-2024-02456", "Lodging", "2024-06-11", "678.00", "USD", "Hyatt", "", "", "", "", "", "Hyatt Regency LA", "Los Angeles", "2024-06-10", "2024-06-12", "2", "", "", "", ""],
    ["E10294", "RPT-2024-02890", "Hotel", "2024-07-23", "534.00", "USD", "Westin", "", "", "", "", "", "Westin Boston", "Boston", "2024-07-22", "2024-07-24", "2", "", "", "", ""],
    # Ground
    ["E10294", "RPT-2024-00821", "Taxi", "2024-01-22", "45.80", "USD", "Uber", "", "", "", "", "", "", "", "", "", "", "TAXI", "18", "Chicago O'Hare", "Chicago Downtown"],
    ["E20441", "RPT-2024-01204", "Rail", "2024-02-16", "89.00", "USD", "Deutsche Bahn", "", "", "", "", "", "", "", "", "", "", "RAIL", "340", "Frankfurt", "Munich"],
    ["E30102", "RPT-2024-01567", "Car Rental", "2024-03-07", "234.00", "USD", "Hertz", "", "", "", "", "", "", "", "", "", "", "RENTAL", "", "New York", "Newark"],  # no distance
    ["E10294", "RPT-2024-02001", "Taxi", "2024-04-18", "62.50", "USD", "Lyft", "", "", "", "", "", "", "", "", "", "", "RIDESHARE", "24", "Munich Airport", "City Center"],
    ["E20441", "RPT-2024-02234", "Taxi", "2024-05-02", "12.00", "USD", "Uber India", "", "", "", "", "", "", "", "", "", "", "TAXI", "8", "Mumbai Airport", "BKC"],
    ["E30102", "RPT-2024-02456", "Ground", "2024-06-10", "78.00", "USD", "SuperShuttle", "", "", "", "", "", "", "", "", "", "", "SHUTTLE", "42", "LAX", "Downtown LA"],
    ["E10294", "RPT-2024-02890", "Rail", "2024-07-22", "156.00", "USD", "Amtrak", "", "", "", "", "", "", "", "", "", "", "RAIL", "450", "Boston", "New York"],
    ["E20441", "RPT-2024-03102", "Car Rental", "2024-08-16", "312.00", "USD", "Enterprise", "", "", "", "", "", "", "", "", "", "", "RENTAL", "280", "Paris CDG", "Lille"],
    ["E30102", "RPT-2024-03345", "Taxi", "2024-09-08", "38.00", "USD", "Yellow Cab", "", "", "", "", "", "", "", "", "", "", "TAXI", "", "Denver", "Denver"],  # no distance, spend fallback
    ["E10294", "RPT-2024-03500", "Airfare", "2024-10-12", "890.00", "USD", "JetBlue", "BOS", "SEA", "Economy", "B6", "One-Way", "", "", "", "", "", "", "", "", ""],
    ["E20441", "RPT-2024-03500", "Hotel", "2024-10-13", "445.00", "USD", "Kimpton", "", "", "", "", "", "Kimpton Seattle", "Seattle", "2024-10-12", "2024-10-14", "2", "", "", "", ""],
    ["E30102", "RPT-2024-03500", "Taxi", "2024-10-12", "55.00", "USD", "Uber", "", "", "", "", "", "", "", "", "", "", "TAXI", "22", "Seattle Tacoma", "Downtown"],
]

with open(OUT / "travel_concur_export.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(TRAVEL_HEADER)
    w.writerows(travel)

print(f"Generated {len(sap_rows)} SAP, {len(urows)} utility, {len(travel)} travel rows in {OUT}")
