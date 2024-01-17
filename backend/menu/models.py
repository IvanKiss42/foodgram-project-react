from django.db import models
from django.core.validators import RegexValidator


class Ingridient(models.Model):
    """Модель для ингридиентов."""

    LIST_OF_UNITS = (
        ('мл', 'миллилитр'),
        ('г', 'грамм'),
        ('по вкусу', 'по вкусу'),
        ('стакан', 'стакан 300 мл'),
        ('л', 'литр'),
        ('горсть', 'горсть'),
        ('кг', 'килограммы'),
        ('пакет', 'пакет'),
        ('пучок', 'пучок'),
        ('кусок', 'кусок'),
        ('капля', 'капля'),
        ('щепотка', 'щепотка'),
        ('долька', 'долька'),
        ('банка', 'банка'),
        ('упаковка', 'упаковка'),
        ('ч. л.', 'чайная ложка'),
        ('ст. л.', 'столовая ложка'),
        ('веточка', 'веточка'),
        ('шт.', 'штука')
    )

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

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель для тэгов."""

    name = models.CharField(
        verbose_name='Тег',
        help_text='Укажите цвет в формате #ffffff',
        max_length=200
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
        max_length=200,
        validators=([RegexValidator(regex=r'^[-a-zA-Z0-9_]+$')])
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Resipe(models.Model):
    """Модель для рецептов."""

    name = models.CharField(
        verbose_name='Название',
        help_text='Укажите название',
        unique=True,
        max_length=200
    )
    pub_date = models.DateTimeField(
        verbose_name='Название',
        auto_now_add=True
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        help_text='Укажите время приготовления (в минутах)',
        
    )
    author = models.IntegerField()
    text = models.TextField(max_length=255)
    image = models.ImageField(
        upload_to='menu/recipes/', null=True, blank=True)
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        blank=True,
        help_text='Удерживайте Ctrl для выбора нескольких вариантов'
    )
    ingridients = models.ManyToManyField(
        Ingridient,
        through='ResipeIngridient',
        verbose_name='Ингридиенты',
        blank=True,
        help_text='Удерживайте Ctrl для выбора нескольких ингридиентов'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class ResipeIngridient(models.Model):
    """Модель для ингридиентов и их количества."""

    resipe = models.ForeignKey(Resipe, on_delete=models.CASCADE)
    ingridient = models.ForeignKey(Ingridient, on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.resipe} {self.ingridient}'
