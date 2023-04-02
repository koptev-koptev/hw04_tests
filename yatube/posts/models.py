from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, unique=True, null=True,
                             verbose_name='Имя группы')
    slug = models.SlugField(max_length=100, unique=True,
                            verbose_name='Slug группы')
    description = models.TextField(max_length=2000, blank=True, null=True,
                                   verbose_name='Описание группы')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа публикаций'
        verbose_name_plural = 'Группы публикаций'


class Post(models.Model):
    text = models.TextField(verbose_name='Текст публикации')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор публикации',
    )

    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа публикации',
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)
