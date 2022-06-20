import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    """TestCase для views"""
    # количество записей для занесения в БД
    COUNT_OF_REC: int = 15

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_without_post = User.objects.create_user(
            username='auth_without_post'
        )
        cls.group_1 = Group.objects.create(
            title='Тестовая группа № 1',
            slug='test_slug_1',
            description='Тестовое описание № 1',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа № 2',
            slug='test_slug_2',
            description='Тестовое описание № 2',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image_gif_1 = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.image_gif_2 = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        # список объектов Post для БД
        cls.user_1 = User.objects.create_user(username='auth_1')
        objs = []
        for i in range(1, PostViewTests.COUNT_OF_REC + 1):
            objs.append(
                Post(
                    author=cls.user,
                    text=f'Тестовый пост и содержит номер: {i}',
                    group=cls.group_1,
                    image=cls.image_gif_1
                )
            )
        Post.objects.bulk_create(objs)
        cls.post = Post.objects.filter(author=cls.user).latest('pub_date')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewTests.user)
        self.authorized_client_without_post = Client()
        self.authorized_client_without_post.force_login(PostViewTests.user_1)
        cache.clear()

    def test_index_page_show_correct_context(self):
        """
        Шаблон index сформирован с правильным контекстом.
        Проверка что передается список постов.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        last_object = response.context['page_obj'][0]
        expected_post = PostViewTests.post
        last_object_expected_post_fields = {
            last_object.text: expected_post.text,
            last_object.pub_date: expected_post.pub_date,
            last_object.group: expected_post.group,
            last_object.image: expected_post.image,
        }
        for last_object_field, expected_post_field in (
            last_object_expected_post_fields.items()
        ):
            with self.subTest(last_object=last_object):
                self.assertEqual(
                    last_object_field,
                    expected_post_field,
                    'Ошибка передачи контекста в index'
                )

    def test_group_list_page_show_correct_context(self):
        """
        Шаблон group_list сформирован с правильным контекстом.
        Проверка что передается список постов группы.
        """
        group_1 = PostViewTests.group_1
        slug = group_1.slug
        expected_post = group_1.posts.latest('pub_date')
        response = (
            self.
            authorized_client.
            get(reverse('posts:group_list', kwargs={'slug': slug}))
        )
        last_object = response.context['page_obj'][0]
        last_object_expected_post_fields = {
            last_object.text: expected_post.text,
            last_object.pub_date: expected_post.pub_date,
            last_object.author: expected_post.author,
            last_object.image: expected_post.image,
        }
        for last_object_field, expected_post_field in (
            last_object_expected_post_fields.items()
        ):
            with self.subTest(last_object=last_object):
                self.assertEqual(
                    last_object_field,
                    expected_post_field,
                    'Ошибка передачи контекста в group_list'
                )

    def test_profile_page_show_correct_context(self):
        """
        Шаблон profile сформирован с правильным контекстом.
        Проверка что передается список постов группы.
        """
        user = PostViewTests.user
        response = (
            self.
            authorized_client.
            get(reverse('posts:profile', kwargs={'username': user.username}))
        )
        last_object = response.context['page_obj'][0]
        expected_post = user.posts.latest('pub_date')
        last_object_expected_post_fields = {
            last_object.text: expected_post.text,
            last_object.pub_date: expected_post.pub_date,
            last_object.author.get_full_name: (
                expected_post.author.get_full_name
            ),
            last_object.image: expected_post.image,
        }
        for last_object_field, expected_post_field in (
            last_object_expected_post_fields.items()
        ):
            with self.subTest(last_object=last_object):
                self.assertEqual(
                    last_object_field,
                    expected_post_field,
                    'Ошибка передачи контекста в profile'
                )

    def test_not_group_page_show_correct(self):
        """
        Проверка, что пост не попал в группу,
        для которой не был предназначен.
        """
        user = PostViewTests.user
        group_2 = PostViewTests.group_2
        slug = group_2.slug
        response = (
            self.
            authorized_client.
            get(reverse('posts:group_list', kwargs={'slug': slug}))
        )
        objects_group_2 = response.context['page_obj']
        self.assertNotIn(
            user.posts.latest('pub_date'),
            objects_group_2,
            'Новый пост появляется не в той группе'
        )

    def test_post_detail_page_show_correct_context(self):
        """
        Шаблон post_detail сформирован с правильным контекстом.
        Проверка что передается пост c заданным id.
        """
        user = PostViewTests.user
        post_id = PostViewTests.post.id
        response = (
            self.
            authorized_client.
            get(reverse('posts:post_detail', kwargs={'post_id': post_id}))
        )
        last_object = response.context['post']
        expected_post = user.posts.get(id=post_id)
        last_object_expected_post_fields = {
            last_object.text: expected_post.text,
            last_object.image: expected_post.image,
        }
        for last_object_field, expected_post_field in (
            last_object_expected_post_fields.items()
        ):
            with self.subTest(last_object=last_object):
                self.assertEqual(
                    last_object_field,
                    expected_post_field,
                    'Ошибка передачи контекста в post_detail'
                )

    def test_create_post_page_show_correct_context(self):
        """
        Шаблон create_post сформирован с правильным контекстом.
        Проверка что передается форма с text и списком group.
        """
        response = (
            self.
            authorized_client.
            get(reverse('posts:post_create'))
        )
        post_id = PostViewTests.post.id
        response_edit = (
            self.
            authorized_client.
            get(reverse('posts:post_edit', kwargs={'post_id': post_id}))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(
                    form_field,
                    expected,
                    'Ошибка передачи контекста в create_post'
                )
                form_field = (
                    response_edit.
                    context.get('form').
                    fields.get(value)
                )
                self.assertIsInstance(
                    form_field,
                    expected,
                    (
                        'Ошибка передачи контекста в create_post'
                        'при редактировании'
                    )
                )

    def test_pages_contains_required_counts_records(self):
        """
        Проверка, что на странице 1 и 2
        выводится необходимое количество постов"""
        numb_of_post_10: int = settings.NUMB_OF_POST
        numb_of_post_5: int = 5
        slug = PostViewTests.group_1.slug
        username = PostViewTests.user.username
        numbers = {
            numb_of_post_10: [
                reverse('posts:index'),
                reverse('posts:profile', kwargs={'username': username}),
                reverse('posts:group_list', kwargs={'slug': slug}),
            ],
            numb_of_post_5: [
                reverse('posts:index') + '?page=2',
                reverse(
                    'posts:profile', kwargs={'username': username}
                ) + '?page=2',
                reverse('posts:group_list', kwargs={'slug': slug}) + '?page=2',
            ]
        }
        for number, urls in numbers.items():
            for url in urls:
                with self.subTest(url=url):
                    response = self.authorized_client.get(url)
                    self.assertEqual(
                        len(response.context['page_obj']),
                        number,
                        (
                            f'На странице {url}'
                            ' выводится неправильное количество постов'
                        )
                    )

    def test_edit_post(self):
        """Редактирование поста пользователем"""
        url_post_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostViewTests.post.id}
        )
        response = self.authorized_client.get(url_post_edit)
        form_data = response.context['form'].initial
        changed_text = 'Изменение'
        form_data['text'] = changed_text
        form_data['image'] = PostViewTests.image_gif_2
        response = self.authorized_client.post(
            url_post_edit,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostViewTests.post.id}
        ))
        changed_post = Post.objects.get(id=self.post.id)
        # self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertEqual(changed_post.text, changed_text)

    def test_cache_index_page(self):
        """"Проверка работы кеша на главной странице"""
        response_0 = self.authorized_client.get('/')
        Post.objects.latest('pub_date').delete()
        response_1 = self.authorized_client.get('/')
        cache.clear()
        response_2 = self.authorized_client.get('/')
        self.assertEqual(
            response_0.content,
            response_1.content,
            'Кеширование на главной странице не осуществляется'
        )
        self.assertNotEqual(
            response_1.content,
            response_2.content,
            'После обновления кеша главная страница не обновляется'
        )

    def test_follow_index(self):
        """
        Проверка вывода постов авторов,
        на которых подписался пользователь
        """
        self.authorized_client_without_post.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostViewTests.user.username}
            )
        )
        response = self.authorized_client_without_post.get(
            reverse('posts:follow_index')
        )
        last_object = response.context['page_obj'][0]
        expected_post = PostViewTests.post
        last_object_expected_post_fields = {
            last_object.text: expected_post.text,
            last_object.pub_date: expected_post.pub_date,
            last_object.group: expected_post.group,
            last_object.image: expected_post.image,
        }
        for last_object_field, expected_post_field in (
            last_object_expected_post_fields.items()
        ):
            with self.subTest(last_object=last_object):
                self.assertEqual(
                    last_object_field,
                    expected_post_field,
                    'Ошибка передачи контекста в follow'
                )

    def test_profile_follow_and_unfollow(self):
        """Проверка подписки на автора и отписки"""
        self.authorized_client_without_post.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostViewTests.user.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=PostViewTests.user_1, author=PostViewTests.user
            ).exists(),
            'Подписка не осуществляется'
        )
        self.authorized_client_without_post.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostViewTests.user.username}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=PostViewTests.user_1, author=PostViewTests.user
            ).exists(),
            'Отписка от автора не осуществляется'
        )
