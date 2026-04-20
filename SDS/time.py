from datetime import datetime, timedelta

def get_dynamic_time_range(days_before=1, days_after=1):
    """
    Generates a dictionary with startTime and endTime based on the current date.
    Default is from the start of yesterday to the end of tomorrow.
    """
    now = datetime.now()
    
    # Calculate start (00:00:00) and end (23:59:59)
    start_dt = (now - timedelta(days=days_before)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = (now + timedelta(days=days_after)).replace(hour=23, minute=59, second=59, microsecond=0)
    
    return {
        "startTime": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "endTime": end_dt.strftime("%Y-%m-%d %H:%M:%S")
    }