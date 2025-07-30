import random
from datetime import datetime
from typing import List, Optional
from src.repositories.animals import Animals as AnimalsRepo
from src.models.animal import Animal, AnimalRequest
from src.clients.cats import Cats as CatsClient

class Animals:
    def __init__(self, repo: AnimalsRepo, cats_client: CatsClient):
        self.animals_repo = repo
        self.cats_client = cats_client

    def get_animal_by_id(self, animal_id: int) -> Optional[Animal]:
        return self.animals_repo.get_animal_by_id(animal_id)

    def get_animals_by_name(self, name: str) -> List[Animal]:
        return self.animals_repo.get_animal_by_name(name)

    def create_animal(self, animal: AnimalRequest, user: str) -> Animal:
        complete_animal_model = Animal(
            id=0, #temp
            name=animal.name,
            age=animal.age,
            species=animal.species,
            breed=animal.breed,
            owner=animal.owner,
            created_at=datetime.now(),
            created_by=user,
            updated_at=datetime.now(),
            updated_by=user,
            version=1
        )
        self.animals_repo.create_animal(complete_animal_model)
        return animal

    def update_animal(self, animal_id: int, updates: dict, user: str) -> Optional[Animal]:
        # Get existing animal
        existing_animal = self.animals_repo.get_animal_by_id(animal_id)
        if existing_animal is None:
            return None

        # Update only the fields provided in the request
        existing_data = existing_animal.model_dump()
        existing_data.update(updates)

        # Create updated animal model
        updated_animal = Animal(**existing_data)
        updated_animal.updated_at = datetime.now()
        updated_animal.updated_by = user
        updated_animal.version = existing_animal.version + 1

        # Persist the updated animal
        self.animals_repo.update_animal(updated_animal)
        return updated_animal

    def create_animals_from_breeds(self, user: str):
        breeds = self.cats_client.get_cat_breeds()
        animals_to_create = self.get_animals_for_breeds(breeds, user)
        for a in animals_to_create: # should be done in a transaction but this is an example
            self.animals_repo.create_animal(a)

    @staticmethod
    def get_animals_for_breeds(breeds: List, user: str) -> List[Animal]:
        animals = []

        for i, b in enumerate(breeds):
            animal = Animal(
                id = 0, #temp for now
                name=f"Automated_Animal_{i}",
                age=random.randint(1, 25),
                species='Kitties',
                breed=b.get('name', 'unknown'),
                created_at=datetime.now(),
                created_by=user,
                updated_at=datetime.now(),
                updated_by=user,
                version=1
            )
            animals.append(animal)
        return animals
