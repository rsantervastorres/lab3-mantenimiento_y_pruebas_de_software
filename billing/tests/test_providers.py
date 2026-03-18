from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from billing.models import Provider, Barrel

User = get_user_model()

class ProviderTests(APITestCase):
  def setUp(self):
    self.providerA = Provider.objects.create(name = "Provider A")
    self.providerB = Provider.objects.create(name = "Provider B")

    self.userA = User.objects.create_user(username = "userA", password = "password")
    self.userA.provider = self.providerA
    self.userA.save()

    self.admin_user = User.objects.create_superuser(username = "admin", password = "password")

  def test_normal_user_list_providers_sees_only_own(self):
    self.client.force_authenticate(user = self.userA)
    response = self.client.get("/api/providers/")

    self.assertEqual(response.status_code, status.HTTP_200_OK)

    self.assertEqual(len(response.data), 1)
    self.assertEqual(response.data[0]["name"], "Provider A")

  def test_superuser_list_providers_sees_all(self):
    self.client.force_authenticate(user = self.admin_user)
    response = self.client.get("/api/providers/")

    self.assertEqual(response.status_code, status.HTTP_200_OK)

    self.assertTrue(len(response.data) >= 2)

  def test_normal_user_cannot_access_other_provider_detail(self):
    self.client.force_authenticate(user = self.userA)

    url = f"/api/providers/{self.providerB.id}/"
    response = self.client.get(url)

    self.assertNotEqual(response.status_code, status.HTTP_200_OK)

  def test_provider_liters_calculations(self):
    Barrel.objects.create(
      provider = self.providerA,
      number = "B-05",
      oil_type = "Olive",
      liters = 100,
      billed = True
    )

    Barrel.objects.create(
      provider = self.providerA,
      number = "B-005",
      oil_type = "Olive",
      liters = 50,
      billed = False
    )

    self.client.force_authenticate(user = self.userA)
    url = f"/api/providers/{self.providerA.id}/"
    response = self.client.get(url)

    self.assertEqual(response.status_code, status.HTTP_200_OK)

    self.assertEqual(response.data["billed_liters"], 100)
    self.assertEqual(response.data["liters_to_bill"], 50)