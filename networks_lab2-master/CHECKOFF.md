# SUTD 50.012 Networks Lab 2 Checkoff Submission README Document

> Chan Wei Ping / 1007195

## Setup Usage Instructions

First, ensure that [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/)  are installed on your machine.

Next, navigate to the directory containing the CHECKOFF.md file and run the command ```pip install -r requirements.txt``` to install package dependencies.

Afterwards, run the command ```docker-compose up``` to start the REST API server. Once it's running, visit http://127.0.0.1:8000 in your browser to see the output.

## Endpoints Documentation

Below is a list of endpoints available in this REST API, along with their usage details and expected responses. They are categorized based on their respective HTTP method

### GET

All of these endpoints under this section are idempotent as they produce the same effect on the server and return the same response (assuming no external change occurs). All query parameters can be combined and used together.

Refer to get_request.http file for sample GET requests. 

1. `/`

Homepage. Displays ""Welcome to the the world of Pokemon! Please choose your starter Pokemon!" when there are no pokemon created. Whereas it displays the number of pokemons if there are pokemons created in the database

2. `/pokemon`

Displays the entire Pokémon database as an array of objects in JSON format. If no Pokémon exist in the database, it shows "No Pokémon found in the world!"

3. `/pokemon/{id}`

Retrieves the Pokémon corresponding to the given ID and returns it as an array of objects in JSON format. If the specified ID does not exist in the database, it displays "Pokémon with ID {id} not found!"

4. `/pokemon?sortBy=id`

Sorts pokemon by id in acsending order.

5. `/pokemon?sortBy=name`

Sorts pokemon by id in alphabetical order.

6. `/pokemon?sortBy=hp`

Sorts pokemon by hp in acsending order.

7. `/pokemon?sortBy=type`

Sorts pokemon by type in alphabetical order.

8. `/pokemon?sortBy=level`

Sorts pokemon by levl in acsending order.

9. `/pokemon?sortBy=xp`

Sorts pokemon by xp in acsending order.

10. `/pokemon?count=<number_of_pokemons>`

Display maximum number of N pokemons.

11. `/pokemon?offset=<number_of_offset>`

Display pokemons with a front offset of N. 


### POST
Generally, a POST request is non-idempotent. However, the implementation of this endpoint allows us to preserve idempotency since it checks for existing Pokemon in the database.


1. `/pokemon`

Creates a new pokemon. All respective json fields must be provided.
{
    name: str
    id: int
    hp: int
    type: str 
    level: int 
    xp: int
}

This results in a new pokemon created in the Redis database. 

### DELETE

All of these endpoints under this section are idempotent. Validation checks are in place to check for duplicated deletion.

1. `/pokemon/{id}`

Delete a pokemon by its ID. Entry will be deleted in Redis database.

2. `/pokemon-batch`

Delete multiple pokemons within a range of pokemon level. Requires the specific json format.
{
    min_level: int
    max_level: int
}

All pokemons within the range will be deleted in Redis database.

## Future Improvements
Currently, the server may be under low load due to the limited amount of data in the database and the small number of client requests. However, as the database expands and server traffic increases, implementing caching can significantly improve performance and efficiency. For example, we can cache the common queries such as "/pokemon?sortBy=name" to avoid recomputation and speeds up repeated requests and set a short TTL to ensure data freshness.

Furthermore, instead of fetching all pokemons and sorting in python, we can try to perform sorting and filtering directly in Redis if possible. This will speed up the fetching process.