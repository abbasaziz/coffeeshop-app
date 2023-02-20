import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
app.app_context().push()
CORS(app)

'''
@TODO uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():

    # Here, we try to retrieve all the drinks from the database and order them by ID:
    try:
        drinks = Drink.query.order_by(Drink.id).all()

    # If successful, we return a JSON response that includes the 'success' flag and a list of all the drinks in the database, where each drink is represented as a short version of itself:
        return jsonify({
            'success': True,
            'drinks': [drink.short() for drink in drinks]
        })

    # If an error occurs, we log the error and return a 404 error response:
    except Exception as e:
        print(e)
        abort(404)


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    try:
        # Get all drinks from the database and order by id
        drinks = Drink.query.order_by(Drink.id).all()

        # Return a response containing all drinks as a list, using the long() method to display all details about the drinks.
        return jsonify({
            'success': True,
            'drinks': [drink.long() for drink in drinks]
        })

    except Exception as e:
        # Print the error message and abort with a 404 error
        print(e)
        abort(404)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_new_drinks(jwt):
    # Get the request body
    body = request.get_json()
    
    # Check if the title and recipe are present in the body
    if not ('title' in body and 'recipe' in body):
        print("body", body)
        # If title or recipe is missing, abort with error code 422 (unprocessable)
        abort(422)

    # Extract the title and recipe from the request body
    title = body.get('title')
    recipe = body.get('recipe')

    try:
        # Create a new drink instance with the extracted title and recipe
        drink = Drink(
            title=title,
            recipe=json.dumps(recipe))

        # Add the new drink to the database
        drink.insert()

        # Return the success message along with the details of the newly added drink
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })

    except Exception as e:
        # If there is an error in the process, abort with error code 422 (unprocessable)
        print(e)
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, id):
    # get the drink with the given id
    drink = Drink.query.get(id)

    # check if the drink exists
    if drink:
        try:
            # get the data from the request body
            body = request.get_json()

            # update the drink title and recipe if they exist in the request body
            title = body.get('title')
            recipe = body.get('recipe')

            if title:
                drink.title = title
            if recipe:
                drink.recipe = json.dumps(recipe)

            # update the drink in the database
            drink.update()

            # return the updated drink
            return jsonify({
                'success': True,
                'drinks': [drink.long()]
            })
        except Exception as e:
            # if there is an error updating the drink, abort with a 422 Unprocessable Entity error
            print(e)
            abort(422)

    # if the drink doesn't exist, abort with a 404 Not Found error
    else:
        abort(404)



'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    # get the drink from the database based on the id
    drink = Drink.query.get(id)

    if drink:
        try:
            # delete the drink from the database
            drink.delete()

            # return a success message indicating the drink has been deleted
            return jsonify({
                'success': True,
                'delete': id,
            })
        except Exception as e:
            # if there was an error deleting the drink, raise a 422 error
            print(e)
            abort(422)

    else:
        # if the drink with the specified id was not found, raise a 404 error
        abort(404)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'not found',
    }), 404
    

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def handle_auth_error(x):
    return jsonify({
        'success': False,
        'error': x.status_code,
        'message': x.error,
    })