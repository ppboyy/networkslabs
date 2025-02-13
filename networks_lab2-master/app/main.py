from fastapi import FastAPI, Response, Depends, Header, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
import redis
from models import Pokemon, BatchPokeDelete
import pickle
from typing import Optional, List
import csv
import io
import json

app = FastAPI()

def get_redis_client():
    return redis.Redis(host='redis')

def get_all_pokemon_ids(redis_client):
    all_pokemon_ids = redis_client.smembers("/pokemon/id")
    all_pokemon_ids = [int(x.decode("utf-8")) for x in all_pokemon_ids]
    return all_pokemon_ids


@app.get("/")
async def read_root(redis_client: redis.Redis = Depends(get_redis_client)):
    if redis_client.exists("/pokemon/id"):
        return f"Welcome to the the world of Pokemon! There are {redis_client.scard('/pokemon/id')} pokemons in the world"
    else:
        return "Welcome to the the world of Pokemon! Please choose your starter Pokemon!"

@app.get("/pokemon")
async def read_pokemon_list(
    response: Response,
    redis_client: redis.Redis = Depends(get_redis_client),
    sortBy: Optional[str] = None,
    count: Optional[int] = None,
    offset: Optional[int] = None,
):
    all_pokemon_ids = get_all_pokemon_ids(redis_client)     
    pokemon_collection = []
    for pokemon_id in all_pokemon_ids:
        pokemon = pickle.loads(redis_client.get(f"/pokemon/{pokemon_id}"))
        pokemon_collection.append(pokemon)
    
    if len(pokemon_collection) == 0:
        response.status_code = 200
        return "No pokemons found in the world!"

    if sortBy:
        if sortBy == "id":
            pokemon_collection = sorted(pokemon_collection, key=lambda x: x.id)
        elif sortBy == "name":
            pokemon_collection = sorted(pokemon_collection, key=lambda x: x.name)
        elif sortBy == "hp":
            pokemon_collection = sorted(pokemon_collection, key=lambda x: x.hp)
        elif sortBy == "type":
            pokemon_collection = sorted(pokemon_collection, key=lambda x: x.type)
        elif sortBy == "level":
            pokemon_collection = sorted(pokemon_collection, key=lambda x: x.level)
        elif sortBy == "xp":
            pokemon_collection = sorted(pokemon_collection, key=lambda x: x.xp)
        else:
            response.status_code = 400
            return f"Invalid sortBy parameter: {sortBy}. Please choose from id, name, hp, type, level, xp"
    
    if count:
        if count <= len(pokemon_collection):
            pokemon_collection = pokemon_collection[:count]
        else:
            response.status_code = 400
            return "Invalid count value. Count value should be less than the number of pokemons in the world"
    
    if offset:
        if offset <= len(pokemon_collection):
            pokemon_collection = pokemon_collection[offset:]
        else:
            response.status_code = 400
            return "Invalid offset value. Offset value should be less than the number of pokemons in the world"

    response.status_code = 200
    return pokemon_collection

@app.get("/pokemon/{id}")
async def read_pokemon(
    id: int,
    response: Response,
    redis_client: redis.Redis = Depends(get_redis_client),
):
    if redis_client.sismember("/pokemon/id", id):
        pokemon = pickle.loads(redis_client.get(f"/pokemon/{id}"))
        response.status_code = 200
        return pokemon
    else:
        response.status_code = 404
        return f"Pokemon with id {id} not found!"

@app.post("/pokemon")
async def create_pokemon(
    pokemon: Pokemon,
    response: Response,
    redis_client: redis.Redis = Depends(get_redis_client),
):
        allpokemon = get_all_pokemon_ids(redis_client)
        if pokemon.id in allpokemon:
            response.status_code = 400
            return f"Pokemon with id {pokemon.id} already exists"
        else:
            redis_client.sadd("/pokemon/id", pokemon.id)
            redis_client.set(f"/pokemon/{pokemon.id}", pickle.dumps(pokemon))
            response.status_code = 201
            return f"Pokemon {pokemon.name} created!"
        
@app.delete("/pokemon/{pokemon_id}")
async def delete_pokemon(
    pokemon_id: int,
    response: Response,
    redis_client: redis.Redis = Depends(get_redis_client),
):
    if pokemon_id in get_all_pokemon_ids(redis_client):
        
        redis_client.srem("/pokemon/id", pokemon_id)
        redis_client.delete(f"/pokemon/{pokemon_id}")
        response.status_code = 200
        return f"Pokemon with id {pokemon_id} deleted!"
    else:
        response.status_code = 404
        return f"Pokemon with id {pokemon_id} not found!"

@app.delete("/pokemon-batch")
async def delete_multiple_pokemons(
    response: Response,
    batchinfo: BatchPokeDelete,
    redis_client: redis.Redis = Depends(get_redis_client),
):
    all_pokemon_ids = get_all_pokemon_ids(redis_client)
    pokemon_collection = []
    for pokemon_id in all_pokemon_ids:
        pokemon = pickle.loads(redis_client.get(f"/pokemon/{pokemon_id}"))
        pokemon_collection.append(pokemon)
    
    if not pokemon_collection:
        response.status_code = 404
        return "No pokemons found in the world!"

    if batchinfo.min_level >0 and batchinfo.max_level >0:
        deleted_pokemon = []
        for pokemon in pokemon_collection:
            if int(pokemon.level) >= batchinfo.min_level and int(pokemon.level) <= batchinfo.max_level:
                redis_client.delete(f"/pokemon/{pokemon.id}")
                redis_client.srem("/pokemon/id", pokemon.id)
                deleted_pokemon.append(pokemon.name)
        response.status_code = 200
        return f"Deleted {len(deleted_pokemon)} pokemons, pokemons deleted: {deleted_pokemon}"
    
    else:
        response.status_code = 400
        return "Invalid level values. Please provide a valid range 1-100"

@app.get("/pokemon-export")  # Remove response_class=FileResponse
async def export_pokemon(
    response: Response,
    redis_client: redis.Redis = Depends(get_redis_client)
):
    # Get all Pokemon
    all_pokemon_ids = get_all_pokemon_ids(redis_client)

    if len(all_pokemon_ids) == 0:
        return JSONResponse(
            status_code=404,
            content={"message": "No pokemons found in the world!"}
        )
    
    try:
        pokemon_collection = []
        for pokemon_id in all_pokemon_ids:
            pokemon = pickle.loads(redis_client.get(f"/pokemon/{pokemon_id}"))
            pokemon_collection.append(pokemon)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['id', 'name', 'level', 'hp', 'type', 'xp'])
        writer.writeheader()
        
        for pokemon in pokemon_collection:
            writer.writerow({
                'id': pokemon.id,
                'name': pokemon.name,
                'level': pokemon.level,
                'hp': pokemon.hp,
                'type': pokemon.type,
                'xp': pokemon.xp
            })
        
        # Return CSV response
        return Response(
            content=output.getvalue(),
            media_type='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename="pokemon_export.csv"'
            }
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error exporting Pokemon: {str(e)}"}
        )


