from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Group, Post
from django.urls import reverse
from http import HTTPStatus


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exists_at_desired_location(self):
        """Страницы доступны гостям и авторизованным пользователям."""
        url = [
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug':
                            PostURLTests.group.slug}),
            reverse('posts:profile',
                    kwargs={'username':
                            PostURLTests.user.username}),
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            PostURLTests.post.id}),
        ]
        for url in url:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        url = [
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            PostURLTests.post.id}),
            reverse('posts:post_create'),
        ]
        for url in url:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous(self):
        """Страница /post_id/edit перенаправляет анонимного пользователя."""
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, f'/auth/login/?next=/posts/'
                                       f'{self.post.id}/edit/')

    def test_post_create_url_redirect_anonymous(self):
        """Страница /posts/create/ перенаправляет анонимного пользователя. """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_unexisting_page(self):
        """Запрос к странице unixisting_page вернет ошибку 404"""
        response = self.guest_client.get('/unixisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
