import pandas as pd
import bq_functions

project_id = "analytics-449112"
dataset_id = "datalake"

# upload tables_descriptions dataset
# df = pd.read_csv("datasets/tables_descriptions/tables_descriptions.csv")

bq_functions.csv_to_bigquery(project_id=project_id, 
                             dataset_id=dataset_id, 
                             table_id="tables_descriptions", 
                             csv_path="datasets/tables_descriptions/tables_descriptions.csv", 
                             schema_path="datasets/tables_descriptions/schema.json")

# upload hotel_bookings dataset
# https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand
# df = pd.read_csv("datasets/hotel_bookings/hotel_bookings.csv")

bq_functions.csv_to_bigquery(project_id=project_id, 
                             dataset_id=dataset_id, 
                             table_id="hotel_bookings", 
                             csv_path="datasets/hotel_bookings/hotel_bookings.csv", 
                             schema_path="datasets/hotel_bookings/schema.json")




# upload supermarket_sales dataset
# https://www.kaggle.com/datasets/aungpyaeap/supermarket-sales
# df = pd.read_csv("datasets/supermarket_sales/supermarket_sales.csv")

bq_functions.csv_to_bigquery(project_id=project_id, 
                             dataset_id=dataset_id, 
                             table_id="supermarket_sales", 
                             csv_path="datasets/supermarket_sales/supermarket_sales.csv", 
                             schema_path="datasets/supermarket_sales/schema.json")


# upload netflix_movies_and_tv_shows dataset
# https://www.kaggle.com/datasets/shivamb/netflix-shows
# df = pd.read_csv("datasets/netflix_movies_and_tv_shows/netflix_movies_and_tv_shows.csv")

bq_functions.csv_to_bigquery(project_id=project_id, 
                             dataset_id=dataset_id, 
                             table_id="netflix_movies_and_tv_shows", 
                             csv_path="datasets/netflix_movies_and_tv_shows/netflix_movies_and_tv_shows.csv", 
                             schema_path="datasets/netflix_movies_and_tv_shows/schema.json")


# upload video_games_sales dataset
# https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents
# df = pd.read_csv("datasets/video_games_sales/video_games_sales.csv")

bq_functions.csv_to_bigquery(project_id=project_id, 
                             dataset_id=dataset_id, 
                             table_id="video_games_sales", 
                             csv_path="datasets/video_games_sales/video_games_sales.csv", 
                             schema_path="datasets/video_games_sales/schema.json")


