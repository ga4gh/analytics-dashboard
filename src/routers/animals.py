from fastapi import APIRouter, Header, HTTPException, Response

from src.models.animal import Animal, AnimalRequest
from src.services.animals import Animals as AnimalsService


class Animals:
    def __init__(self, animals_service: AnimalsService) -> None:
        self.router = APIRouter()
        self.animals_service = animals_service
        self._setup_routes()

    def _setup_routes(self) -> None:

        @self.router.get("/animals/{animal_id}", response_model=Animal)
        async def get_animal(animal_id: int) -> Animal:
            animal = self.animals_service.get_animal_by_id(animal_id)
            if animal is None:
                raise HTTPException(status_code=404, detail="Animal not found")
            return animal

        @self.router.get("/animals/name/{name}", response_model=list[Animal])
        async def get_animals_by_name(name: str) -> list[Animal]:
            animals = self.animals_service.get_animals_by_name(name)
            if not animals:
                raise HTTPException(status_code=404, detail="No animals found with that name")
            return animals

        @self.router.post("/animals")
        async def create_animal(animal: AnimalRequest, user: str = Header(...)) -> Response:
            self.animals_service.create_animal(animal, user)
            return Response(status_code=200)

        @self.router.put("/animals/{animal_id}", response_model=Animal)
        async def update_animal(animal_id: int, updates: dict, user: str = Header(...)) -> Animal | None:
            updated_animal = self.animals_service.update_animal(animal_id, updates, user)
            if updated_animal is None:
                raise HTTPException(status_code=404, detail="Animal not found")
            return updated_animal

        @self.router.post("/animals/cat/breeds")
        async def create_cats_by_breed(user: str = Header(...)) -> Response:
            self.animals_service.create_animals_from_breeds(user)
            return Response(status_code=200)
