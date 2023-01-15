from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import *
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

class CatalogBaseTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="test_user", password="test_password", email="test@test.com")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_catalog_base_get_success(self):
        test_catalog_base = CatalogBase.objects.create(catalog_name="test_catalog_base", owner=self.user)
        response = self.client.get("/catalog/base/", data={"catalog_name": "test_catalog_base"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ["owner", "catalog_name", "article_identifiers"])
        self.assertEqual(response.data["catalog_name"], test_catalog_base.catalog_name)
        self.assertEqual(response.data["owner"], {"id": self.user.id, "username": self.user.username, "email": self.user.email})

    def test_catalog_base_get_failure_catalog_base_not_found(self):
        test_catalog_base = CatalogBase.objects.create(catalog_name="test_catalog_base", owner=self.user)
        response = self.client.get("/catalog/base/", data={"catalog_name": "test_catalog_base_2"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_base_post_success(self):
        response = self.client.post("/catalog/base/", data={"catalog_name": "test_catalog_base"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ["info", "catalog_id"])
        self.assertEqual(response.data["info"], "catalog base creation successful")

    def test_catalog_base_post_failure_catalog_base_already_exists(self):
        test_catalog_base = CatalogBase.objects.create(catalog_name="test_catalog_base", owner=self.user)
        response = self.client.post("/catalog/base/", data={"catalog_name": "test_catalog_base"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertCountEqual(response.data.keys(), ["error"])
        self.assertEqual(response.data["error"], "catalog base already exists")

    def test_catalog_base_delete_success(self):
        test_catalog_base = CatalogBase.objects.create(catalog_name="test_catalog_base", owner=self.user)
        response = self.client.delete("/catalog/base/", data={"catalog_name": "test_catalog_base"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ["info"])
        self.assertEqual(response.data["info"], "catalog base deleted")

    def test_catalog_base_delete_failure_catalog_base_not_found(self):
        test_catalog_base = CatalogBase.objects.create(catalog_name="test_catalog_base", owner=self.user)
        response = self.client.delete("/catalog/base/", data={"catalog_name": "test_catalog_base_2"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# Create your tests here.
