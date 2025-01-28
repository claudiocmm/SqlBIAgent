from google.cloud import bigquery
import pandas as pd
import bq_functions

project_id = "analytics-449112"
dataset_id = "datawarehouse"


# upload hotel_bookings dataset
# https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand
df = pd.read_csv("/home/claudiocm/Git/SQLAgentReportCreator/datasets/hotel_bookings/hotel_bookings.csv")

bq_functions.csv_to_bigquery(project_id=project_id, 
                             dataset_id=dataset_id, 
                             table_id="hotel_bookings", 
                             csv_path="datasets/hotel_bookings/hotel_bookings.csv", 
                             schema_path="datasets/hotel_bookings/schema.json")




# upload supermarket_sales dataset
# https://www.kaggle.com/datasets/aungpyaeap/supermarket-sales
df = pd.read_csv("/home/claudiocm/Git/SQLAgentReportCreator/datasets/supermarket_sales/supermarket_sales.csv")

bq_functions.csv_to_bigquery(project_id=project_id, 
                             dataset_id=dataset_id, 
                             table_id="supermarket_sales", 
                             csv_path="datasets/supermarket_sales/supermarket_sales.csv", 
                             schema_path="datasets/supermarket_sales/schema.json")


