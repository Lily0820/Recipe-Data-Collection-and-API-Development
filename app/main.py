import mysql.connector
from mysql.connector import Error
from flask import Flask, request, jsonify
from flask_cors import CORS
import math
import json

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='root',
        database='recipesdb'
    )


@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM recipes")
        total_records = cursor.fetchone()['total']

        query = """
        SELECT 
            id, title, cuisine, rating, prep_time, cook_time, total_time,
            description, nutrients, serves
        FROM recipes
        ORDER BY rating DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, offset))
        recipes = cursor.fetchall()

        if not recipes:
            total_pages = math.ceil(total_records / limit)
            return jsonify({
                "status": "success",
                "query_params": {"page": page, "limit": limit, "offset": offset},
                "pagination": {
                    "total_records": total_records,
                    "total_pages": total_pages,
                    "current_page": page,
                    "per_page": limit
                },
                "message": "No recipes found for this page.",
                "recipes": []
            }), 200

        for recipe in recipes:
            nutrients_data = recipe.get('nutrients')
            if nutrients_data:
                try:
                    recipe['nutrients'] = json.loads(nutrients_data)
                except json.JSONDecodeError:
                    recipe['nutrients'] = None
            else:
                recipe['nutrients'] = None

            rating_value = recipe.get('rating')
            if rating_value is None:
                recipe['rating_trend'] = "N/A"
            else:
                recipe['rating_trend'] = "⬆" if rating_value >= 4.0 else "⬇"

        total_pages = math.ceil(total_records / limit)
        response = {
            "status": "success",
            "query_params": {
                "page": page,
                "limit": limit,
                "offset": offset
            },
            "pagination": {
                "total_records": total_records,
                "total_pages": total_pages,
                "current_page": page,
                "per_page": limit
            },
            "message": f"Showing recipes {offset+1} to {offset+len(recipes)}",
            "recipes": recipes
        }

        cursor.close()
        connection.close()
        return jsonify(response), 200

    except Error as e:
        return jsonify({"status": "error", "type": "Database", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "type": "Server", "message": str(e)}), 500


@app.route('/api/recipes/search', methods=['GET'])
def search_recipes():
    try:
        calories = request.args.get('calories')
        title = request.args.get('title')
        cuisine = request.args.get('cuisine')
        total_time = request.args.get('total_time')
        rating = request.args.get('rating')

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM recipes WHERE 1=1"
        params = []

        if calories:
            if '<=' in calories:
                value = calories.replace('<=', '')
                query += " AND JSON_EXTRACT(nutrients, '$.calories') <= %s"
                params.append(value)
            elif '>=' in calories:
                value = calories.replace('>=', '')
                query += " AND JSON_EXTRACT(nutrients, '$.calories') >= %s"
                params.append(value)
            elif '=' in calories:
                value = calories.replace('=', '')
                query += " AND JSON_EXTRACT(nutrients, '$.calories') = %s"
                params.append(value)

        if title:
            query += " AND title LIKE %s"
            params.append(f"%{title}%")

        if cuisine:
            query += " AND cuisine = %s"
            params.append(cuisine)

        if total_time:
            if '<=' in total_time:
                value = total_time.replace('<=', '')
                query += " AND total_time <= %s"
                params.append(value)
            elif '>=' in total_time:
                value = total_time.replace('>=', '')
                query += " AND total_time >= %s"
                params.append(value)
            elif '=' in total_time:
                value = total_time.replace('=', '')
                query += " AND total_time = %s"
                params.append(value)

        if rating:
            if '<=' in rating:
                value = rating.replace('<=', '')
                query += " AND rating <= %s"
                params.append(value)
            elif '>=' in rating:
                value = rating.replace('>=', '')
                query += " AND rating >= %s"
                params.append(value)
            elif '=' in rating:
                value = rating.replace('=', '')
                query += " AND rating = %s"
                params.append(value)

        count_query = f"SELECT COUNT(*) as total FROM ({query}) AS count_table"
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()['total']

        query += " ORDER BY rating DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        cursor.execute(query, params)
        recipes = cursor.fetchall()

        if not recipes:
            total_pages = math.ceil(total_records / limit)
            return jsonify({
                "status": "success",
                "query_params": {
                    "page": page,
                    "limit": limit,
                    "offset": offset,
                    "title": title,
                    "cuisine": cuisine,
                    "calories": calories,
                    "total_time": total_time,
                    "rating": rating
                },
                "pagination": {
                    "total_matches": total_records,
                    "total_pages": total_pages,
                    "current_page": page,
                    "per_page": limit
                },
                "message": "No recipes found for the given filters or page.",
                "recipes": []
            }), 200

        for recipe in recipes:
            nutrients_data = recipe.get('nutrients')
            if nutrients_data:
                try:
                    recipe['nutrients'] = json.loads(nutrients_data)
                except json.JSONDecodeError:
                    recipe['nutrients'] = None
            else:
                recipe['nutrients'] = None

            rating_value = recipe.get('rating')
            if rating_value is None:
                recipe['rating_trend'] = "N/A"
            else:
                recipe['rating_trend'] = "⬆" if rating_value >= 4.0 else "⬇"

        total_pages = math.ceil(total_records / limit)
        response = {
            "status": "success",
            "query_params": {
                "page": page,
                "limit": limit,
                "offset": offset,
                "title": title,
                "cuisine": cuisine,
                "calories": calories,
                "total_time": total_time,
                "rating": rating
            },
            "pagination": {
                "total_matches": total_records,
                "total_pages": total_pages,
                "current_page": page,
                "per_page": limit
            },
            "message": f"Found {total_records} recipes matching your filters.",
            "recipes": recipes
        }

        cursor.close()
        connection.close()
        return jsonify(response), 200

    except Error as e:
        return jsonify({"status": "error", "type": "Database", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "type": "Server", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=7001, debug=True)