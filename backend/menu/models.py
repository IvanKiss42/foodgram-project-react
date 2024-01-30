from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import UniqueConstraint
from django.core.validators import MinValueValidator

User = get_user_model()


class Ingredient(models.Model):
    """Модель для ингридиентов."""

    name = models.CharField(
        max_length=200,
        verbose_name='Название ингридиента',
        help_text='Укажите ингридиент',
        unique=True,
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения',
        help_text='Укажите единицы измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='ingredient_name_unit_unique'
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель для тэгов."""

    name = models.CharField(
        verbose_name='Тег',
        help_text='Укажите имя',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        verbose_name='Цвет',
        help_text='Укажите цвет в формате #ffffff',
        max_length=7
    )
    slug = models.SlugField(
        verbose_name='Slug',
        help_text='Укажите slug',
        unique=True,
        max_length=200
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель для рецептов."""

    name = models.CharField(
        verbose_name='Название',
        help_text='Укажите название',
        unique=True,
        max_length=200
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        help_text='Укажите время приготовления (в минутах)',
        validators=[MinValueValidator(
            1, message='Время приготовления должно быть не менее 1 минуты!'
        )]
    )
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    text = models.TextField(
        verbose_name='Введите описание рецепта',
        max_length=255
    )
    image = models.ImageField(
        upload_to='recipes_images/',
        verbose_name='Изображение',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги',
        help_text='Удерживайте Ctrl для выбора нескольких вариантов'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='ingredients',
        verbose_name='Ингридиенты',
        help_text='Удерживайте Ctrl для выбора нескольких ингридиентов'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель для ингридиентов и их количества."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            1,
            message=('Количество ингридиента измеряется целыми числами'
                     + 'и не может быть меньше 1!')
        )]
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipe_ingredient_unique'
            )
        ]

    def __str__(self):
        return f'{self.recipe} {self.ingredient} {self.amount}'


class RecipeTag(models.Model):
    """Модель тега и рецепта."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'tag'],
                name='recipe_tag_unique'
            )
        ]


class ShoppingCart(models.Model):
    """Модель корзины."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_cart',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_shopping_cart_unique'
            )
        ]


class Favorite(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_favorite_unique'
            )
        ]
