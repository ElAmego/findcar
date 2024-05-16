# name, year, transmission, engine,  body, mileage, price, link
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class CustomUser(AbstractUser):
    amount = models.IntegerField(default=0, verbose_name='Общее количество объявлений')


class Cars(models.Model):
    year = models.IntegerField(verbose_name='Год')
    transmission = models.TextField(max_length=255, verbose_name='КПП')
    volume = models.CharField(max_length=32, verbose_name='Объем двигателя & Запас хода')
    engine = models.CharField(max_length=255, verbose_name='Двигатель')
    body = models.CharField(max_length=255, verbose_name='Тип кузова')
    mileage = models.IntegerField(verbose_name='Пробег')
    price = models.CharField(max_length=255, verbose_name='Цена')
    link = models.CharField(max_length=255, verbose_name='Ссылка')
    message = models.CharField(verbose_name='Сообщение продавца')
    location = models.TextField(max_length=255, verbose_name='Город')
    status = models.TextField(max_length=16, verbose_name='Статус авто', default='Продается')
    isFeatured = models.BooleanField(default=False, verbose_name='Избранное')
    slug = models.SlugField(unique=True, db_index=True)
    car_model = models.ForeignKey('CarModelsList', on_delete=models.CASCADE, verbose_name='CarModelsList_id')
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, verbose_name='CustomUser_id')

    def get_absolute_url(self):
        return reverse('car_detail', kwargs={'car_slug': self.slug})


class Featured(models.Model):
    name = models.CharField(max_length=255, verbose_name='Марка & Модель машины')
    year = models.IntegerField(verbose_name='Год')
    transmission = models.TextField(max_length=255, verbose_name='КПП')
    volume = models.CharField(max_length=32, verbose_name='Объем двигателя & Запас хода')
    engine = models.CharField(max_length=255, verbose_name='Двигатель')
    body = models.CharField(max_length=255, verbose_name='Тип кузова')
    mileage = models.IntegerField(verbose_name='Пробег')
    price = models.CharField(max_length=255, verbose_name='Цена')
    link = models.CharField(max_length=255, verbose_name='Ссылка')
    location = models.TextField(max_length=255, verbose_name='Город')
    note = models.CharField(max_length=255, verbose_name='Примечания', default='')
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, verbose_name='CustomUser_id')


class CarDetail(models.Model):
    color = models.ForeignKey('Colors', on_delete=models.CASCADE, verbose_name='color_id')
    img_link = models.CharField(max_length=255, verbose_name='Ссылка картинки')
    body_section = models.BinaryField(verbose_name='Секция Кузов', default=None, null=True)
    engine_section = models.BinaryField(verbose_name='Секция Двигатель', default=None, null=True)
    transmission_section = models.BinaryField(verbose_name='Секция Трансмиссия и управление', default=None, null=True)
    performance_indicators_section = models.BinaryField(verbose_name='Секция Эксплуатационные показатели',
                                                        default=None, null=True)
    suspension_and_brakes_section = models.BinaryField(verbose_name='Секция Подвеска и тормоза', default=None,
                                                       null=True)
    car = models.ForeignKey('Cars', on_delete=models.CASCADE, verbose_name='cars_id')


class CarNamesList(models.Model):
    car_name = models.CharField(max_length=32, verbose_name='Марка')
    car_index = models.IntegerField(verbose_name='Индекс в ссылке')


class CarModelsList(models.Model):
    model_name = models.CharField(max_length=64, verbose_name='Модель')
    model_index = models.IntegerField(verbose_name='Индекс в ссылке')
    car = models.ForeignKey('CarNamesList', on_delete=models.CASCADE, verbose_name='CarNamesList_id')


class Colors(models.Model):
    color = models.TextField(max_length=32, verbose_name='Цвет')
    color_hex = models.CharField(max_length=7, verbose_name='HEX')
