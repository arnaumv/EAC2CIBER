from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.auth.models import User, Permission
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class PollsSeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Configuración del navegador en modo headless
        options = Options()
        options.add_argument("--headless")  # Modo headless
        options.add_argument("--disable-gpu")  # Desactiva la GPU, útil para entorno CI
        options.add_argument("--no-sandbox")  # Evita problemas con el contenedor de CI
        
        # Iniciar el WebDriver con las opciones
        cls.selenium = WebDriver(options=options)
        cls.selenium.implicitly_wait(10)

        # Crear superusuario para pruebas
        superuser = User.objects.create_user("isard", "isard@isardvdi.com", "pirineus")
        superuser.is_superuser = True
        superuser.is_staff = True
        superuser.save()

        # Crear usuario staff con permisos para ver usuarios
        staff_user = User.objects.create_user("staffuser", "staff@isardvdi.com", "staffpassword")
        staff_user.is_staff = True
        view_user_permission = Permission.objects.get(codename="view_user")
        staff_user.user_permissions.add(view_user_permission)
        staff_user.save()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_staff_user_permissions(self):
        # Acceder al panel de administración como usuario de staff
        self.selenium.get(f'{self.live_server_url}/admin')

        # Iniciar sesión como usuario de staff
        self.selenium.find_element(By.NAME, 'username').send_keys('staffuser')
        self.selenium.find_element(By.NAME, 'password').send_keys('staffpassword')
        self.selenium.find_element(By.XPATH, '//input[@type="submit"]').click()

        # Comprobar que puede ver el enlace "Users" (usuarios)
        try:
            WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.LINK_TEXT, "Users"))
            )
        except TimeoutException:
            with open("debug_staff_permissions.html", "w") as f:
                f.write(self.selenium.page_source)
            self.fail("El usuario de staff no puede ver la lista de usuarios en el panel de administración")

        # Acceder a la página de usuarios
        self.selenium.find_element(By.LINK_TEXT, "Users").click()

        # Comprobar que el usuario no puede crear usuarios (botón "Add user" no debería estar presente)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.LINK_TEXT, "Add user")

        # Comprobar que el usuario no puede eliminar usuarios (botón "Delete" no debería estar presente)
        try:
            delete_button = self.selenium.find_element(By.XPATH, "//button[contains(text(), 'Delete')]")
            self.fail("El usuario de staff puede eliminar usuarios, lo cual no debería estar permitido")
        except NoSuchElementException:
            pass  # Esto es lo esperado: el botón no debe existir
