# Python Recipe API

This is a simple Recipe API made in Python for week 4 of [Resolution's](https://resolution.hackclub.com/) Python Pathway

# Usage

The package is on [TestPyPi](https://test.pypi.org/project/Py_Recipe_API/)

To install, you can use
```
pip install -i https://test.pypi.org/simple/ Py_Recipe_API
```

# Routes

## Register (POST /register)

Creates and returns your API key and links it to a username set in a body of:
```
{
    "name": "username"
}
```
where "username" is your username

## Change Username (PUT /user/name)

Limited to twice per hour and requiring an API key, this route changes your name with a request body of 

```
{
    "name": "username"
}
```
where "username" is your new username

## Delete Account (DELETE /user)

Requiring an API key, this route will delete the user who the API key belongs to

## Create a Recipe (POST /recipes)

Requring an API key and limited to 5 times a minute, this route will create a recipe with a request body of

```
{
    "title": "string",
    "description": "string",
    "ingredients": "string",
    "instructions": "string",
    "is_public": true,
    "image_url": "string"
}
``` 
*Note that "description", "is_public", and "image_url" are optional

## Updating a Recipe (PATCH /recipes/{recipe_id})

Requring an API key and limited to 5 times a minute, this route will update a recipe with a request body of

```
{
    "title": "string",
    "description": "string",
    "ingredients": "string",
    "instructions": "string",
    "is_public": true,
    "image_url": "string"
}
``` 
*Note that all fields are optional

## Deleting a Recipe (DELETE /recipes/{recipe_id})

Requiring an API key, this deletes your recipe at the given id

## List Public Recipes (GET /recipes/public)

This lists all public recipes on a given page (integer > 0 with a default of 1) with a max count per page between 1 and 200, defaulting to 50

## List Your Recipes (GET /recipes/me)

Requring an API key, this lists all of your public and private recipes on a given page (integer > 0 with a default of 1) with a max count per page between 1 and 200, defaulting to 50

## List a Users Recipes (GET /recipes/user/{user_id})

This lists a users public recipes on a given page (integer > 0 with a default of 1) with a max count per page between 1 and 200, defaulting to 50

## Get a Specific Recipe (GET /recipes/{recipe_id})

Requiring an API key, this gets the specified recipe, as long as you have the proper authorization

## Recipe Searching (GET /recipes/search)

This searches all public recipes titles and ingredients for a given query and lists the results on a given page (integer > 0 with a default of 1) with a max count per page between 1 and 200, defaulting to 50