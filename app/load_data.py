import json
import pandas as pd
import mysql.connector
import numpy as np

def safe_convert(value, convert_func):
    try:
        if pd.isna(value) or value is None:
            return None
        return convert_func(value)
    except:
        return None

with open('/Users/likit/recipe_api/US_recipes_null.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
recipes = list(data.values())
df = pd.DataFrame(recipes)
df = df.replace([np.nan, pd.NA], [None, None])

connection = mysql.connector.connect(
    host="localhost",
    user="root",             
    password="root",
    database="recipesdb"    
)
cursor = connection.cursor()
insert_query = """
INSERT INTO recipes (
    cuisine, title, rating, prep_time, cook_time,
    total_time, description, nutrients, serves
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
inserted_count = 0
for _, row in df.iterrows():
    try:
        rating = safe_convert(row.get('rating'), float)
        prep_time = safe_convert(row.get('prep_time'), int)
        cook_time = safe_convert(row.get('cook_time'), int)
        total_time = safe_convert(row.get('total_time'), int)
        nutrients = row.get('nutrients')
        if pd.isna(nutrients) or nutrients is None:
            nutrients_json = None
        else:
            nutrients_json = json.dumps(nutrients)
        cursor.execute(insert_query, (
            row.get('cuisine'),
            row.get('title'),
            rating,
            prep_time,
            cook_time,
            total_time,
            row.get('description'),
            nutrients_json,
            row.get('serves')
        ))
        inserted_count += 1
    except Exception as e:
        print(f"Skipping record due to error: {e}")
connection.commit()
cursor.close()
connection.close()
print(f" Successfully inserted {inserted_count} recipes into MySQL!")