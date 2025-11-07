from django.test import TestCase
from django.urls import reverse
from horarios.models import Horarios

class HorariosViewsTest(TestCase):
    def setUp(self):
        # Create a dummy Horarios object for testing
        self.horario = Horarios.objects.create(
            nombre='Test Horario',
            hora_entrada='09:00:00',
            hora_salida='17:00:00',
            lunes=True,
            cantidad_personal_requerida=1
        )

    def test_editar_horario_view_uses_correct_template(self):
        """
        Tests that the editar_horario view uses the correct template.
        """
        # Get the URL for the editar_horario view
        url = reverse('editar_horario', args=[self.horario.id])
        
        # Make a GET request to the view
        response = self.client.get(url)
        
        # Check that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template was used
        self.assertTemplateUsed(response, 'editar_horario.html')