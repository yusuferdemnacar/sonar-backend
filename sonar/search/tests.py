from django.test import TestCase
from django.test import Client

#use double quotes insted of single quotes
class SearchTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_search_success(self):
        response = self.client.get("/search/s2ag_search/", {"search_query": "click chemistry", "offset": 1})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.json().keys(), ["search_results", "total_page_count", "search_query", "offset"])
        self.assertEqual(response.json()["search_query"], "click chemistry")

# Create your tests here.
