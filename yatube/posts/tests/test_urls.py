from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    """TestCase для urls"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_without_post = User.objects.create_user(
            username='auth_without_post'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        # пост без группы
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост это более 15 символов',
        )

    def setUp(self):
        self.guest_client = Client()
        # авторизованный клиент с постом
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # авторизованный клиент без поста
        self.authorized_client_without_post = Client()
        self.authorized_client_without_post.force_login(self.user_without_post)
        cache.clear()

    def test_url_is_for_guests(self):
        """Страницы доступны любому пользователю."""
        slug = PostURLTests.group.slug
        username = PostURLTests.user.username
        post_id = PostURLTests.post.id
        urls = [
            '/',
            f'/group/{slug}/',
            f'/profile/{username}/',
            f'/posts/{post_id}/',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Страница {url} недоступна любому пользователю.'
                )

    def test_url_is_for_user(self):
        """Страница 'create/' доступна зарегистрированным пользователям."""
        response = self.authorized_client_without_post.get('/create/')

        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            'Страница create/ не доступна зарегистрированным пользователям.'
        )

    def test_url_is_for_author(self):
        """Страница 'posts/<int:post_id>/edit/' доступна автору поста."""
        post_id = PostURLTests.post.id
        response = self.authorized_client.get(f'/posts/{post_id}/edit/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            'Страница posts/<int:post_id>/edit/ не доступна автору поста.'
        )

    def test_url_is_for_author(self):
        """
        У не автора поста и неавторизованного пользователя на URL:
        'posts/<int:post_id>/edit/' происходит редирект на пост.
        """
        post_id = PostURLTests.post.id
        url_edit = f'/posts/{post_id}/edit/'
        url_redirect_authorized = f'/posts/{post_id}/'
        url_redirect_guest = f'/auth/login/?next=/posts/{post_id}/edit/'
        responses_redirects = {
            self.authorized_client_without_post.get(url_edit): (
                url_redirect_authorized
            ),
            self.guest_client.get(url_edit): url_redirect_guest,
        }
        for response, url_redirect in responses_redirects.items():
            with self.subTest(response=response):
                self.assertRedirects(
                    response,
                    url_redirect,
                    msg_prefix=(
                        (
                            'При попытке редактирования поста '
                            'неавторизрованным пользователем или '
                            'не автором поста не перенаправляется '
                            'на вход или страницу поста'
                        )
                    )
                )

    def test_non_existent_url(self):
        """Запрос к несуществующей странице вернёт ошибку 404."""
        response = self.guest_client.get('/none/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            'Запрос к несуществующей странице не возвращает ошибку 404.'
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        slug = PostURLTests.group.slug
        username = PostURLTests.user.username
        post_id = PostURLTests.post.id
        url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{slug}/': 'posts/group_list.html',
            f'/profile/{username}/': 'posts/profile.html',
            f'/posts/{post_id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{post_id}/edit/': 'posts/create_post.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'URL-адрес: {address} использует неправильный шаблон'
                )

    def test_add_comment_authorized_client(self):
        """
        Проверка, что комментировать посты
        может только авторизованный пользователь
        и комментарий создаётся
        """
        comment_id: int = 1
        post_id = PostURLTests.post.id
        form_data = {'text': 'Мой комментарий'}
        client_test = self.authorized_client
        client_test.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data
        )
        self.assertEqual(
            Comment.objects.get(id=comment_id).text,
            'Мой комментарий',
            'Комментарий не создается')
        client_test.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id})
        )
        self.assertEqual(
            PostURLTests.post.comments.get(id=comment_id).text,
            'Мой комментарий',
            'Авторизованный пользователь не может создать комментарий'
        )

    def test_add_comment_guest_client(self):
        """
        Проверка, что неавторизованный пользователь
        не может комментировать посты
        и комментарий не создаётся
        """
        comment_id: int = 1
        post_id = PostURLTests.post.id
        form_data = {'text': 'Мой комментарий'}
        client_test = self.guest_client
        client_test.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data
        )
        with self.assertRaisesMessage(
            ObjectDoesNotExist,
            'Comment matching query does not exist'
        ):
            Comment.objects.get(id=comment_id)

    def test_url_is_for_author(self):
        """
        Проверка, что неавторизованные пользователи
        не могут подписываться (происходит перенаправление).
        """
        username = PostURLTests.user.username
        url_profile_follow = f'/profile/{username}/follow/'
        url_redirect_guest = f'/auth/login/?next=/profile/{username}/follow/'
        self.assertRedirects(
            self.guest_client.get(url_profile_follow),
            url_redirect_guest,
            msg_prefix=(
                (
                    'При попытке неавторизованного пользователя '
                    'подписаться не происходит перенаправление '
                    'на авторизацию'
                )
            )
        )
