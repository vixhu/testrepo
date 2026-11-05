from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

def get_utc_now() -> datetime:
    """Returns the current UTC datetime."""
    return datetime.now(timezone.utc)

def today_ist() -> date:
    return datetime.now(IST).date()

def format_datetime_ist(dt: datetime | None, format_string: str = "%d/%b/%Y") -> str | None:
    """
    Converts a UTC datetime to IST (+05:30) and formats it.
    If the datetime is naive, it assumes it is UTC.
    """
    if not dt:
        return None
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
        
    dt_ist = dt.astimezone(IST)
    
    return dt_ist.strftime(format_string)

def format_datetime_ist_full(dt: datetime | None) -> str | None:
    """Convenience method for full datetime format"""
    return format_datetime_ist(dt, "%d/%b/%Y %H:%M:%S")
