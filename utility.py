def get_data_metrics(df):
    """
    Calculates counts for valid Order IDs and Tracking Numbers.
    """
    if df is None or df.empty:
        return 0, 0
        
    # Ensure we treat everything as strings and handle NaNs
    temp_df = df.fillna("").astype(str)
   
    count_orders = len(temp_df[temp_df["Order ID"].str.strip() != ""])
    count_tracking = len(temp_df[temp_df["Tracking Number"].str.strip() != ""])
    
    return count_orders, count_tracking