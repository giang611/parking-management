"""Business rules only: validation, fee calculation and revenue periods."""
import math
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import database

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
VALID_TYPES = {"CAR", "MOTORCYCLE", "BICYCLE"}


class BusinessError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


def validate_vehicle(ticket, plate, vehicle_type, require_plate=True):
    if not isinstance(ticket, int) or isinstance(ticket, bool) or ticket <= 0:
        raise BusinessError(400, "ticket must be a positive integer")
    if vehicle_type not in VALID_TYPES:
        raise BusinessError(400, "invalid vehicle type")
    if vehicle_type == "BICYCLE":
        if plate not in (None, ""):
            raise BusinessError(422, "bicycle must not have a plate")
    elif not isinstance(plate, str) or not plate.strip():
        raise BusinessError(422, "car and motorcycle require a plate")
    if not require_plate and plate is not None and not isinstance(plate, str):
        raise BusinessError(400, "invalid plate")


def park(data):
    ticket, plate, vehicle_type = data.get("ticket"), data.get("plate"), data.get("type")
    validate_vehicle(ticket, plate, vehicle_type)
    if database.get(ticket):
        raise BusinessError(409, "ticket already active")
    if not database.post(ticket, plate, vehicle_type, int(datetime.now(TZ).timestamp())):
        raise BusinessError(409, "ticket already active")
    return {"status": 204, "body": {}}


def quote(data, rates):
    ticket, plate, vehicle_type = data.get("ticket"), data.get("plate"), data.get("type")
    validate_vehicle(ticket, plate, vehicle_type)
    vehicle = database.get(ticket)
    if not vehicle or vehicle["type"] != vehicle_type or vehicle["plate"] != plate:
        raise BusinessError(404, "vehicle not found or details do not match")
    now = int(datetime.now(TZ).timestamp())
    seconds = max(0, now - vehicle["in_time"])
    hours = max(1, math.ceil(seconds / 3600))
    return {"status": 200, "body": {
        "ticket": ticket, "hours": hours,
        "charge": hours * rates[vehicle_type], "currency": "VND"
    }}


def collect(data, rates):
    result = quote(data, rates)
    ticket, vehicle_type = data["ticket"], data["type"]
    ok = database.settle(ticket, vehicle_type, result["body"]["charge"],
                         int(datetime.now(TZ).timestamp()))
    if not ok:
        raise BusinessError(404, "vehicle not found")
    return {"status": 204, "body": {}}


def revenue_period(period):
    now = datetime.now(TZ)
    today = now.date()
    if period == "today":
        start_date, end_date = today, today + timedelta(days=1)
    elif period == "yesterday":
        start_date, end_date = today - timedelta(days=1), today
    elif period == "this-week":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
    elif period == "last-week":
        end_date = today - timedelta(days=today.weekday())
        start_date = end_date - timedelta(days=7)
    elif period == "this-month":
        start_date = today.replace(day=1)
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    elif period == "last-month":
        end_date = today.replace(day=1)
        start_date = (end_date - timedelta(days=1)).replace(day=1)
    else:
        raise BusinessError(400, "invalid period")

    start = int(datetime.combine(start_date, time.min, TZ).timestamp())
    end = int(datetime.combine(end_date, time.min, TZ).timestamp())
    return {"status": 200, "body": {
        "revenue": database.revenue(start, end), "currency": "VND"
    }}
