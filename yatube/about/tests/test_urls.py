from http import HTTPStatus

from django.test import Client, TestCase


class AboutURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.static_urls_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

    def setUp(self):
        self.guest_client = Client()

    def test_static_pages_exists_at_desired_location(self):
        """Проверка доступности статичных страниц /about/."""
        for url in AboutURLTests.static_urls_templates.keys():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Страница по адресу: {url} не доступна'
                )

    def test_static_pages_uses_correct_template(self):
        """Проверка шаблонов статичных страниц /about/"""
        for url, template in AboutURLTests.static_urls_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Для страницы: {url} неправильный шаблон'
                )
