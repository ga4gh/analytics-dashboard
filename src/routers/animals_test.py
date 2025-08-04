import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.models.animal import Animal, AnimalRequest
from src.routers.animals import Animals
from src.services.animals import Animals as AnimalsService


@pytest.fixture
def mock_animals_service():
    return Mock(spec=AnimalsService)


@pytest.fixture
def animals_router(mock_animals_service):
    return Animals(mock_animals_service)


@pytest.fixture
def test_client(animals_router):
    app = FastAPI()
    app.include_router(animals_router.router)
    return TestClient(app)


@pytest.fixture
def sample_animal():
    return Animal(
        id=1,
        name="Baloo",
        age=3,
        species="Cat",
        breed="American Shorthair",
        owner="Deeptha Srirangam",
        created_at="2025-08-01T00:00:00Z",
        created_by="deeptha",
        updated_at="2025-08-01T00:00:00Z",
        updated_by="deeptha",
        deleted_at=None,
        deleted_by=None,
        version=1
    )


@pytest.fixture
def sample_animal_request():
    return AnimalRequest(
        name="Koda",
        age=2,
        species="Dog",
        breed="Samoyed",
        owner="Deeptha Srirangam"
    )


class TestGetAnimalById:
    @pytest.mark.parametrize("animal_id,expected_status", [
        (1, 200),
        (999, 404),
    ])
    def test_get_animal_by_id(self, test_client, mock_animals_service, sample_animal, animal_id, expected_status):
        if expected_status == 200:
            mock_animals_service.get_animal_by_id.return_value = sample_animal
        else:
            mock_animals_service.get_animal_by_id.return_value = None
        
        response = test_client.get(f"/animals/{animal_id}")
        
        assert response.status_code == expected_status
        mock_animals_service.get_animal_by_id.assert_called_once_with(animal_id)
        
        if expected_status == 200:
            assert response.json()["id"] == sample_animal.id
            assert response.json()["name"] == sample_animal.name
        else:
            assert response.json()["detail"] == "Animal not found"

    @pytest.mark.parametrize("animal_id,service_exception", [
        (1, Exception("Database error")),
        (2, ValueError("Invalid ID")),
    ])
    def test_get_animal_by_id_service_exceptions(self, test_client, mock_animals_service, animal_id, service_exception):
        mock_animals_service.get_animal_by_id.side_effect = service_exception
        
        with pytest.raises(type(service_exception)):
            test_client.get(f"/animals/{animal_id}")


class TestGetAnimalsByName:
    @pytest.mark.parametrize("name,animals_count,expected_status", [
        ("Koda", 1, 200),
        ("Baloo", 3, 200),
        ("NonExistent", 0, 404),
    ])
    def test_get_animals_by_name(self, test_client, mock_animals_service, sample_animal, name, animals_count, expected_status):
        if animals_count > 0:
            animals = [sample_animal] * animals_count
            mock_animals_service.get_animals_by_name.return_value = animals
        else:
            mock_animals_service.get_animals_by_name.return_value = []
        
        response = test_client.get(f"/animals/name/{name}")
        
        assert response.status_code == expected_status
        mock_animals_service.get_animals_by_name.assert_called_once_with(name)
        
        if expected_status == 200:
            assert len(response.json()) == animals_count
        else:
            assert response.json()["detail"] == "No animals found with that name"