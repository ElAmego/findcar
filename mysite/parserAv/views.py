from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import *
from .models import *
import requests
from pytils.translit import slugify
from bs4 import BeautifulSoup
import datetime
import pickle
from django.conf import settings
from django.shortcuts import redirect


def connection(url):
    headers = {
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
    }

    req = requests.get(url, headers=headers)
    src = req.text
    return BeautifulSoup(src, 'html.parser')


def parser(cars, featured_cars, min_price, max_price, car_index, model_index, amount, request):
    start_model_index = model_index
    all_cars_links = []
    featured_cars_links = []
    models_list = None
    for car in cars:
        all_cars_links.append(car.link)

    for featured_car in featured_cars:
        featured_cars_links.append(featured_car.link)

    if start_model_index == 0:
        models_list = (CarModelsList.objects.filter(car__car_index=car_index).select_related('car')
                       .values('model_name', 'model_index'))

    page = 0
    now = 0
    is_work = True

    while is_work:
        page += 1
        url = ((f'https://cars.av.by/filter?brands[0][brand]={car_index}&brands[0][model]={model_index}&price_usd[min]='
                f'{min_price}&price_usd[max]={max_price}&page=') + str(page))

        main_soup = connection(url)

        all_cars = main_soup.find_all('div', class_=['listing-item', 'listing-top'])

        if len(all_cars) < 25:
            is_work = False

        for num in range(0, len(all_cars)):
            if now == amount:
                is_work = False
                break

            if num == 25:
                page += 1

            if start_model_index == 0:
                car_name = all_cars[num].find('a', class_=['listing-item__link', 'listing-top__title-link']).text
                for model in models_list:
                    if car_name.find(model["model_name"]) >= 0:
                        model_index = model['model_index']
                        break

            # Car link
            car_link = ('https://cars.av.by' + all_cars[num]
                        .find('a', class_=['listing-item__link', 'listing-top__title-link']).get('href'))

            if car_link in all_cars_links:
                break

            car_parameters = None

            # Parameters (year, transmission, engine volume, engine type, body, mileage)
            if all_cars[num].find('div', class_='listing-item__params'):
                car_parameters = []
                for i in range(len(all_cars[num].find('div', class_=['listing-item__params']).find_all('div'))):
                    if i != 1:
                        car_parameters.append(all_cars[num].find('div', class_=['listing-item__params'])
                                              .find_all('div')[i].text)
                    else:
                        car_parameters += (all_cars[num].find('div', class_=['listing-item__params']).find_all('div')[i]
                                           .text.split(', '))

            if all_cars[num].find('div', class_='listing-top__params'):
                car_parameters = all_cars[num].find('div', class_=['listing-top__params']).text.split(', ')

            # Initialization
            car = Cars()

            if 'электро' in car_parameters:
                year, car.transmission, car.engine, car.body, car.volume, mileage = car_parameters
            else:
                year, car.transmission, car.volume, car.engine, car.body, mileage = car_parameters

            car.year = year[:4]
            car.mileage = int(mileage[:-2].replace('\u2009', ''))
            car.location = (all_cars[num].find('div', class_=['listing-top__info-location', 'listing-item__location'])
                            .text)
            car.price = (all_cars[num]
                         .find('div', class_=['listing-top__price-usd', 'listing-item__priceusd']).text[2:-2]
                         .replace('\u2009', ''))
            car.link = car_link

            if all_cars[num].find('div', class_=['listing-top__message', 'listing-item__message']).text is not None:
                car.message = all_cars[num].find('div', class_=['listing-item__message']).text
            else:
                car.message = ''

            if car_link in featured_cars_links:
                car.isFeatured = True

            car.car_model_id = CarModelsList.objects.get(model_index=model_index).id
            car.user = request.user
            car.save()
            car_id = Cars.objects.get(user_id=request.user.id, link=car.link).id
            slug = slugify(car.car_model_id) + '-' + str(request.user.id) + str(car_id)
            Cars.objects.filter(id=car_id).update(slug=slug)
            detail_parser(car)
            now += 1

    amount = CustomUser.objects.get(username=request.user).amount + now
    CustomUser.objects.filter(username=request.user).update(amount=amount)


def detail_parser(car):
    detail_parser_soup = connection(car.link)
    car_detail_data = CarDetail()
    car_color = detail_parser_soup.find('div', class_='card__description').text.split(',')[2].strip()
    car_detail_data.color_id = Colors.objects.get(color=car_color).id
    car_detail_data.img_link = detail_parser_soup.find('div', class_='gallery__frame').find('img').get('data-src')

    if detail_parser_soup.find('div', class_='card__modification'):
        detail_link_div = detail_parser_soup.find('div', class_='card__modification')
        detail_link = detail_link_div.find('a').get('href')

        new_detail_parser_soup = connection(detail_link)
        all_data_sections = new_detail_parser_soup.find_all('section', class_='modification-section')
        for i in range(len(all_data_sections)):
            section_name = all_data_sections[i].find('h2', class_='modification-section-title').text

            match section_name:
                case 'Кузов':
                    body_section = all_data_sections[i].find('dl', class_='modification-list')
                    body_section_arr = []
                    for body_param in body_section:
                        body_param_name = body_param.find('dt').text
                        body_param_value = body_param.find('dd').text
                        body_section_arr.append({body_param_name: body_param_value})
                    db_body_section_arr = pickle.dumps(body_section_arr)
                    car_detail_data.body_section = db_body_section_arr

                case 'Двигатель':
                    engine_section = all_data_sections[i].find('dl', class_='modification-list')
                    engine_section_arr = []
                    for engine_param in engine_section:
                        engine_param_name = engine_param.find('dt').text
                        engine_param_value = engine_param.find('dd').text
                        engine_section_arr.append({engine_param_name: engine_param_value})
                    db_engine_section_arr = pickle.dumps(engine_section_arr)
                    car_detail_data.engine_section = db_engine_section_arr

                case 'Трансмиссия и управление':
                    transmission_section = all_data_sections[i].find('dl', class_='modification-list')
                    transmission_section_arr = []
                    for transmission_param in transmission_section:
                        transmission_param_name = transmission_param.find('dt').text
                        transmission_param_value = transmission_param.find('dd').text
                        transmission_section_arr.append({transmission_param_name: transmission_param_value})
                    db_transmission_section_arr = pickle.dumps(transmission_section_arr)
                    car_detail_data.transmission_section = db_transmission_section_arr

                case 'Эксплуатационные показатели':
                    performance_indicators_section = all_data_sections[i].find('dl', class_='modification-list')
                    performance_indicators_section_arr = []
                    for performance_indicators_param in performance_indicators_section:
                        performance_indicators_param_name = performance_indicators_param.find('dt').text
                        performance_indicators_param_value = performance_indicators_param.find('dd').text
                        performance_indicators_section_arr.append(
                            {performance_indicators_param_name: performance_indicators_param_value})
                    db_performance_indicators_section_arr = pickle.dumps(performance_indicators_section_arr)
                    car_detail_data.performance_indicators_section = db_performance_indicators_section_arr

                case 'Подвеска и тормоза':
                    suspension_and_brakes_section = all_data_sections[i].find('dl', class_='modification-list')
                    suspension_and_brakes_section_arr = []
                    for suspension_and_brakes_param in suspension_and_brakes_section:
                        suspension_and_brakes_param_name = suspension_and_brakes_param.find('dt').text
                        suspension_and_brakes_param_value = suspension_and_brakes_param.find('dd').text
                        suspension_and_brakes_section_arr.append({
                            suspension_and_brakes_param_name: suspension_and_brakes_param_value})
                    db_suspension_and_brakes_section_arr = pickle.dumps(suspension_and_brakes_section_arr)
                    car_detail_data.suspension_and_brakes_section = db_suspension_and_brakes_section_arr
    car_detail_data.car = car
    car_detail_data.save()


def index(request):
    date_now = datetime.datetime.now().date()
    if request.user.is_authenticated:
        all_adds = Cars.objects.all().filter(user_id=request.user).count()
        featured_adds = Featured.objects.all().filter(user_id=request.user).count()
        amount = CustomUser.objects.get(username=request.user).amount
    else:
        all_adds = '???'
        featured_adds = '???'
        amount = '???'

    context = {
        'title': 'Findcar',
        'all_adds': all_adds,
        'featured_adds': featured_adds,
        'amount': amount,
        'date_now': date_now,
    }

    return render(request, 'parserAv/index.html', context)


def table(request):
    is_ready = False
    if request.user.is_authenticated:
        cars = Cars.objects.filter(user_id=request.user).select_related('car_model__car')
        car_names_list = list(CarNamesList.objects.values_list('car_name', 'car_index').order_by('car_name'))
        featured_cars = Featured.objects.all().filter(user_id=request.user)

        if request.method == "POST":
            data = request.POST.dict()
            car_index = int(data['car_name'])
            model_index = int(data['model_name'])

            min_price = data['min_price']
            if min_price != '':
                min_price = int(data['min_price'])
            else:
                min_price = 0

            max_price = data['max_price']
            if max_price != '':
                max_price = data['max_price']
            else:
                max_price = 999999

            amount = data['amount']
            if amount != '':
                amount = int(data['amount'])
            else:
                amount = 1

            parser(cars, featured_cars, min_price, max_price, car_index, model_index, amount, request)
            is_ready = True

        # Get-запросы
        if request.method == 'GET':
            # Проверка есть ли type-name в запросе
            if 'type_name' in request.GET:
                # Если type-name - add, то идет процедура добавления объявления в избранное БД
                if request.GET['type_name'] == 'add':
                    link = request.GET['link']
                    if len(Featured.objects.filter(user=request.user, link=link)) != 0:
                        Cars.objects.filter(user=request.user, link=link).update(isFeatured=False)
                        Featured.objects.filter(user=request.user, link=link).delete()
                    else:
                        Cars.objects.filter(user=request.user, link=link).update(isFeatured=True)
                        car = Cars.objects.filter(user_id=request.user, link=link).select_related('car_model__car')
                        add_car = Featured(name=f'{car[0].car_model.car.car_name} {car[0].car_model.model_name}',
                                           year=car[0].year, transmission=car[0].transmission, volume=car[0].volume,
                                           engine=car[0].engine, body=car[0].body, mileage=car[0].mileage,
                                           price=car[0].price, link=car[0].link, location=car[0].location,
                                           user=request.user)
                        add_car.save()

                # Если type-name - delete, то происходит удаления объявления из БД
                if request.GET['type_name'] == 'delete':
                    link = request.GET['link']
                    Cars.objects.filter(user=request.user, link=link).delete()

                # Если type-name - check_status, то происходит обновление статуса автомобилей пользователя
                if request.GET['type_name'] == 'check_status':
                    for car in cars:
                        soup = connection(car.link)
                        try:
                            status = soup.find('div', class_='gallery__status').get_text()
                        except AttributeError:
                            status = 'Продается'

                        Cars.objects.filter(user=request.user, link=car.link).update(status=status)

                    return JsonResponse('', safe=False)

                if request.GET['type_name'] == 'get_models':
                    car_id = CarNamesList.objects.get(car_index=request.GET['car_index'])
                    model_list = (CarModelsList.objects.filter(car_id=car_id).values_list('model_index', 'model_name')
                                  .order_by('model_name'))
                    return JsonResponse(list(model_list), safe=False)

        context = {
            'title': 'Findcar Объявления',
            'all_cars': cars,
            'is_ready': is_ready,
            'car_names_list': car_names_list,
        }

        return render(request, 'parserAv/table.html', context)

    return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))


def featured(request):
    if request.user.is_authenticated:
        featured_adds = Featured.objects.filter(user_id=request.user)
        context = {
            'title': 'Findcar Избранное',
            'featured_adds': featured_adds
        }

        if request.method == 'GET':
            if 'text' in request.GET:
                text = request.GET['text'].strip()
                link = request.GET['link']
                Featured.objects.filter(user=request.user, link=link).update(note=text)

            if 'type_name' in request.GET:
                if request.GET['type_name'] == 'delete':
                    link = request.GET['link']
                    Featured.objects.filter(user=request.user, link=link).delete()

                    if len(list(Cars.objects.filter(user=request.user, link=link))) != 0:
                        Cars.objects.filter(user=request.user, link=link).update(isFeatured=False)

        return render(request, 'parserAv/featured.html', context)
    return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))


def car_detail(request, car_slug):
    car = get_object_or_404(Cars, user_id=request.user.id, slug=car_slug)
    car_info = Cars.objects.filter(slug=car_slug).select_related('car_model__car')
    if Cars.objects.get(user_id=request.user.id, slug=car_slug):
        details = CarDetail.objects.get(car_id=car.id)
        color = Colors.objects.get(id=details.color_id)

        if details.body_section is not None:
            body_section = pickle.loads(details.body_section)
        else:
            body_section = details.body_section

        if details.engine_section is not None:
            engine_section = pickle.loads(details.engine_section)
        else:
            engine_section = details.engine_section

        if details.transmission_section is not None:
            transmission_section = pickle.loads(details.transmission_section)
        else:
            transmission_section = details.transmission_section

        if details.performance_indicators_section is not None:
            performance_indicators_section = pickle.loads(details.performance_indicators_section)
        else:
            performance_indicators_section = details.performance_indicators_section

        if details.suspension_and_brakes_section is not None:
            suspension_and_brakes_section = pickle.loads(details.suspension_and_brakes_section)
        else:
            suspension_and_brakes_section = details.suspension_and_brakes_section

        context = {
            'title': f'{car.car_model.car.car_name} {car.car_model.model_name}',
            'data': car,
            'details': details,
            'body_section': body_section,
            'engine_section': engine_section,
            'transmission_section': transmission_section,
            'performance_indicators_section': performance_indicators_section,
            'suspension_and_brakes_section': suspension_and_brakes_section,
            'color': color,
            'car_info': car_info,
        }

        return render(request, 'parserAv/car-detail-page.html', context=context)


class RegisterForm(CreateView):
    template_name = 'parserAv/register.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('login')


class LoginForm(LoginView):
    template_name = 'parserAv/login.html'
    form_class = LoginUserForm

    def get_success_url(self):
        return reverse_lazy('home')


def logout_user(request):
    logout(request)
    return redirect('home')
