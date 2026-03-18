from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from billing.models import Invoice, Provider, Barrel, InvoiceLine
from datetime import date

User = get_user_model()

class InvoiceAddLineTests(APITestCase):
  def test_cannot_add_barrel_from_different_provider(self):
    providerA = Provider.objects.create(name = "Provider A")
    providerB = Provider.objects.create(name = "Provider B")

    invoiceA = Invoice.objects.create(
      provider = providerA,
      invoice_no = "A-01",
      issued_on = date.today()
    )

    barrelB = Barrel.objects.create(
      provider = providerB,
      number = "B-01",
      oil_type = "Olive",
      liters = 50,
      billed = False
    )

    user = User.objects.create_user(username = "testuser", password = "password")
    user.provider = providerA
    user.save()

    self.client.force_authenticate(user = user)

    url = f"/api/invoices/{invoiceA.id}/add-line/"

    payload = {
      "barrel": barrelB.id,
      "liters": 50,
      "unit_price": "10.5",
      "description": "prueba de mezcla de proveedores"
    }

    response = self.client.post(url, payload, format = "json")

    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    self.assertIn("barrel must belong to the same provider", str(response.data).lower())

    self.assertEqual(InvoiceLine.objects.count(), 0)

    barrelB.refresh_from_db()
    self.assertFalse(barrelB.billed)


class InvoiceScopingTests(APITestCase):
  def test_user_cannot_access_other_providers_invoices(self):
    providerA = Provider.objects.create(name = "Provider A")
    providerB = Provider.objects.create(name = "Provider B")

    invoiceA = Invoice.objects.create(
      provider = providerA,
      invoice_no = "A-02",
      issued_on = date.today()
    )

    invoiceB = Invoice.objects.create(
      provider = providerB,
      invoice_no = "B-02",
      issued_on = date.today()
    )

    userA = User.objects.create_user(username = "userA", password = "password")
    userA.provider = providerA
    userA.save()

    self.client.force_authenticate(user = userA)

    list_url = "/api/invoices/"
    response_list = self.client.get(list_url)

    self.assertEqual(response_list.status_code, status.HTTP_200_OK)

    response_txt = str(response_list.data)

    self.assertIn("A-02", response_txt)
    self.assertNotIn("B-02", response_txt)

    detail_url = f"/api/invoices/{invoiceB.id}/"
    response_detail = self.client.get(detail_url)

    self.assertEqual(response_detail.status_code, status.HTTP_404_NOT_FOUND)