from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from ..models import Group, Post, User, Follow
from posts.views import NUM_POST
from django.core.cache import cache

User = get_user_model()


class PostPagesTests(TestCase):
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
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug':
                            PostPagesTests.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            PostPagesTests.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            PostPagesTests.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            PostPagesTests.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        for post in Post.objects.all():
            response = self.authorized_client.get(reverse('posts:index'))
            page_obj = response.context['page_obj']
            self.assertIn(post, page_obj)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        for post in Post.objects.all():
            response = self.authorized_client.get(reverse(
                                                  'posts:group_posts',
                                                  kwargs={'slug':
                                                          PostPagesTests.
                                                          group.slug}))
            page_obj = response.context['page_obj']
            self.assertIn(post, page_obj)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        for post in Post.objects.all():
            response = self.authorized_client.get(reverse(
                                                  'posts:profile',
                                                  kwargs={'username':
                                                          PostPagesTests.
                                                          user.username}))
            page_obj = response.context['page_obj']
            self.assertIn(post, page_obj)

    def test_posts_detail_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      kwargs={'post_id':
                                                              PostPagesTests.
                                                              post.id}))
        post_context = response.context['post']
        self.assertEqual(post_context, PostPagesTests.post)

    def test_create_post__page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        username_context = response.context['username']
        self.assertEqual(username_context, PostPagesTests.user)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id':
                                                              PostPagesTests.
                                                              post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        username_context = response.context['username']
        self.assertEqual(username_context, PostPagesTests.user)
        is_edit_context = response.context.get('is_edit')
        self.assertTrue(is_edit_context)

    def test_page_list_is_1(self):
        """Пост с группой попал на необходимые страницы."""
        field_urls_templates = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={
                'slug': PostPagesTests.group.slug}),
            reverse('posts:profile', kwargs={
                'username': PostPagesTests.user.username})
        ]
        for url in field_urls_templates:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']), 1)

    def test_cache_index_page_correct_context(self):
        """Кэш index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        content = response.content
        post_id = PostPagesTests.post.id
        instance = Post.objects.get(pk=post_id)
        instance.delete()
        new_response = self.authorized_client.get(reverse('posts:index'))
        new_content = new_response.content
        self.assertEqual(content, new_content)
        cache.clear()
        new_new_response = self.authorized_client.get(reverse('posts:index'))
        new_new_content = new_new_response.content
        self.assertNotEqual(content, new_new_content)


class PaginatorViewsTest(TestCase):

    NUM_POST_OF_PAGE_2 = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.all().delete()
        list_objs = [
            Post(
                author=cls.user,
                text=f'Тестовое содержание поста #{i}',
                group=cls.group,
            ) for i in range(
                NUM_POST + PaginatorViewsTest.NUM_POST_OF_PAGE_2
            )
        ]
        Post.objects.bulk_create(list_objs)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_paginator_pages(self):
        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': PaginatorViewsTest.
                            group.slug}),
            reverse('posts:profile', kwargs={'username':
                                             PaginatorViewsTest.
                                             user.username})
        ]
        page_offset = {'': NUM_POST,
                       '?page=2': PaginatorViewsTest.NUM_POST_OF_PAGE_2,
                       }
        get_page_contains(self,
                          self.authorized_client,
                          pages_names,
                          page_offset)


def get_page_contains(self, client, page_names, page_offset):
    for page_URL, num_of_posts_in_page in page_offset.items():
        for url in page_names:
            with self.subTest(url=url):
                response = client.get(url + page_URL)
                self.assertEqual(len(response.context['page_obj']),
                                 num_of_posts_in_page)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='following')
        cls.visitor = User.objects.create_user(username='follower')
        cls.simple_user = User.objects.create_user(username='simpleUser')

    def setUp(self) -> None:
        self.visitor_client = Client()
        self.simple_user_client = Client()
        self.visitor_client.force_login(self.visitor)
        self.simple_user_client.force_login(self.simple_user)
        self.post = Post.objects.create(
            author=self.author,
            text='текст'
        )

    def test_user_can_following_and_unfollowing(self):
        """Пользователь может подписаться или отписаться"""
        follow_count = Follow.objects.count()
        self.visitor_client.get(reverse('posts:profile_follow',
                                kwargs={'username': self.author.username}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        follow_count = Follow.objects.count()
        self.visitor_client.get(reverse('posts:profile_unfollow',
                                kwargs={'username': self.author.username}))
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_follow_page_for_follower(self):
        """Пост появляется на странице того, кто подписан"""
        self.visitor_client.get(reverse('posts:profile_follow', kwargs={
            'username': self.author.username,
        }))
        response = self.visitor_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)
        '''self.assertContains(response, self.post.text)'''

    def test_follow_page_for_user(self):
        """Пост не появляется на странице того, кто не подписан"""
        self.visitor_client.get(reverse('posts:profile_follow', kwargs={
            'username': self.author.username,
        }))
        response = self.simple_user_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post.text, response)
