from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    """TestCase для моделей"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
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
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Мой 15 комментарий болеее 15 символов'
        )
        cls.author = User.objects.create(username='author')
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        follow = PostModelTest.follow
        str_models = {
            post: post.text[:15],
            group: group.title,
            comment: comment.text[:15],
            follow: follow.user.username
        }
        for model, expected_value in str_models.items():
            with self.subTest(model=model):
                self.assertEqual(
                    str(model),
                    expected_value,
                    f'У "{model.__doc__}" некорректно работает __str__'
                )
