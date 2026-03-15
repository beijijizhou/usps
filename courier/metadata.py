# This acts as a global singleton store
ORDER_ID_LOOKUP = {}

def set_order_map(df):
    global ORDER_ID_LOOKUP
    ORDER_ID_LOOKUP = dict(zip(df["Tracking Number"], df["Order ID"]))

def get_order_id(tracking_number):
    return ORDER_ID_LOOKUP.get(tracking_number, "N/A")