from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from billing.models import Provider, Barrel

User = get_user_model()

class BarrelCreationTests(APITestCase):
  def test_create_barrel_ignores_provider_payload(self):
    providerA = Provider.objects.create(name = "Provider A")
    providerB = Provider.objects.create(name = "Provider B")

    userA = User.objects.create_user(username = "userA", password = "password")
    userA.provider = providerA
    userA.save()

    self.client.force_authenticate(user = userA)

    url = "/api/barrels/"

    payload = {
      "number": "B-04",
      "oil_type": "Olive",
      "liters": 100,
      "provider": providerB.id
    }

    response = self.client.post(url, payload, format = "json")

    self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    created_barrel = Barrel.objects.get(number = "B-04")

    self.assertEqual(created_barrel.provider, providerA)
    self.assertEqual(created_barrel.provider_id, providerA.id)


class BarrelDeletionTests(APITestCase):
  def test_cannot_delete_billed_barrel(self):
    providerA = Provider.objects.create(name = "Provider A")

    userA = User.objects.create_user(username = "userA", password = "password")
    userA.provider = providerA
    userA.save()

    self.client.force_authenticate(user = userA)

    barrel = Barrel.objects.create(
      provider = providerA,
      number = "B-06",
      oil_type = "Olive",
      liters = 100,
      billed = True
    )

    url = f"/api/barrels/{barrel.id}/"
    response = self.client.delete(url)

    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    self.assertIn("cannot delete a billed barrel", str(response.data).lower())

    self.assertTrue(Barrel.objects.filter(id = barrel.id).exists())