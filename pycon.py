import os
from datetime import date
from operator import itemgetter

from flask import Flask, g, request, render_template, abort, make_response, url_for, redirect
from flask_babel import Babel, gettext, lazy_gettext

from schedule import (FRIDAY1, FRIDAY2, FRIDAY3, SATURDAY1, SATURDAY2, SATURDAY3, SATURDAY4, SATURDAY5,
                      SUNDAY1, SUNDAY3, SUNDAY4)
from utils import get_news, get_speakers, get_talks, get_edu_speakers, get_edu_talks, encode_name, decode_name, get_jobs

EVENT = gettext('PyCon SK 2022 | Bratislava, Slovakia')
DOMAIN = 'https://2022.pycon.sk'
API_DOMAIN = 'https://api.pycon.sk'

LANGS = ('en', 'sk')
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S+00:00'

app = Flask(__name__, static_url_path='/static')  # pylint: disable=invalid-name
app.config['BABEL_DEFAULT_LOCALE'] = 'sk'
app.jinja_options = {'extensions': ['jinja2.ext.with_', 'jinja2.ext.i18n']}
babel = Babel(app)  # pylint: disable=invalid-name

CATEGORIES = {
    'tickets': lazy_gettext('Tickets'),
    'conference': lazy_gettext('Conference'),
    'media': lazy_gettext('Media'),
    'speakers': lazy_gettext('Speakers'),
}

SPEAKERS = get_speakers()
TALKS = get_talks()
EDU_SPEAKERS = get_edu_speakers()
EDU_TALKS = get_edu_talks()


@app.route('/sitemap.xml')
def sitemap():
    excluded = {'static', 'sitemap'}
    pages = []

    for lang in LANGS:
        for rule in app.url_map.iter_rules():

            if 'GET' in rule.methods and rule.endpoint not in excluded:
                # `url_for` appends unknown arguments as query parameters.
                # We want to avoid that when a page isn't localized.
                values = {'lang_code': lang} if 'lang_code' in rule.arguments else {}

                if 'name' in rule.arguments:
                    for speaker in SPEAKERS:
                        values['name'] = encode_name(speaker['name'])
                        pages.append(DOMAIN + url_for(rule.endpoint, **values))
                elif 'category' in rule.arguments:
                    for category in CATEGORIES.keys():
                        values['category'] = category
                        pages.append(DOMAIN + url_for(rule.endpoint, **values))
                else:
                    pages.append(DOMAIN + url_for(rule.endpoint, **values))

    sitemap_xml = render_template('sitemap.xml', pages=pages, today=date.today())
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    return response


@app.route('/')
def root():
    return redirect('sk/index.html')


@app.route('/<lang_code>/index.html')
def index():
    template_vars = _get_template_variables(li_index='active', news=get_news(get_locale(), items=3),
                                            categories=CATEGORIES, background_filename='img/about/header1.jpg',
                                            speakers=SPEAKERS+EDU_SPEAKERS)
    return render_template('index.html', **template_vars)


@app.route('/chat.html')
def chat():
    template_vars = _get_template_variables(li_index='active', news=get_news(get_locale(), items=3),
                                            categories=CATEGORIES, background_filename='img/about/header1.jpg',
                                            speakers=SPEAKERS+EDU_SPEAKERS, redirect="https://discord.gg/zA3kc72N")
    return render_template('index.html', **template_vars)

@app.route('/<lang_code>/news.html')
def news():
    template_vars = _get_template_variables(li_news='active', news=get_news(get_locale()), categories=CATEGORIES,
                                            background='bkg-news')
    return render_template('news.html', **template_vars)


@app.route('/<lang_code>/news/<category>.html')
def news_category(category):
    if category not in CATEGORIES.keys():
        abort(404)

    template_vars = _get_template_variables(li_news='active', categories=CATEGORIES, background='bkg-news')
    news = []

    for item in get_news(get_locale()):
        if category in item['categories']:
            news.append(item)

    template_vars['news'] = news
    template_vars['category'] = category
    return render_template('news.html', **template_vars)


@app.route('/<lang_code>/coc.html')
def coc():
    return render_template('coc.html', **_get_template_variables(li_coc='active', background='bkg-chillout'))


@app.route('/<lang_code>/faq.html')
def faq():
    return render_template('faq.html', **_get_template_variables(li_faq='active', background='bkg-chillout'))


@app.route('/<lang_code>/venue.html')
def venue():
    return render_template('venue.html', **_get_template_variables(li_venue='active', background='bkg-chillout'))


@app.route('/<lang_code>/aboutus.html')
def aboutus():
    return render_template('aboutus.html', **_get_template_variables(li_aboutus='active', background='bkg-index'))


@app.route('/<lang_code>/tickets.html')
def tickets():
    return render_template('tickets.html', **_get_template_variables(li_tickets='active', background='bkg-index'))


@app.route('/<lang_code>/cfp.html')
def cfp():
    return render_template('cfp.html', **_get_template_variables(li_cfp='active', background='bkg-speaker'))


@app.route('/<lang_code>/cfp_form.html')
def cfp_form():
    return render_template('cfp_form.html', **_get_template_variables(li_cfp='active', background='bkg-workshop'))


@app.route('/<lang_code>/recording.html')
def recording():
    return render_template('recording.html', **_get_template_variables(li_recording='active', background='bkg-snake'))


@app.route('/<lang_code>/cfv.html')
def cfv():
    return render_template('cfv.html', **_get_template_variables(li_cfv='active', background='bkg-cfv'))


@app.route('/<lang_code>/sponsors.html')
def sponsors():
    return render_template('sponsors.html', **_get_sponsors_variables(li_sponsors='active', background='bkg-index'))


@app.route('/<lang_code>/edusummit.html')
def edusummit():
    #
    # FRIDAY = [
    #     {
    #         'time': '9:25 - 9:30',
    #         'speakers': ['Eva Klimeková'],
    #         'talk': 'Otvorenie 4. ročníka EduSummit na PyCon SK',
    #     },
    #     {
    #         'time': '9:30 - 9:45',
    #         'talk': 'Učíme s hardvérom'
    #     },
    #     {
    #         'time': '9:45 - 10:15',
    #         'talk': 'Finále súťaže SPy Cup'
    #     },
    #     {
    #         'time': '10:20 - 10:50',
    #         'talk': 'Vzbuďme v študentoch chuť programovať!'
    #     },
    #     {
    #         'time': '11:05 - 12:05',
    #         'talk': 'Ako sa dá s Python zvládnuť štvorročné štúdium na strednej škole',
    #         'keynote': 'True'
    #     },
    #     {
    #         'time': '13:10 - 13:35',
    #         'talk': 'EDUTalks'
    #     },
    #     {
    #         'time': '13:35- 13:55',
    #         'speakers': ['Peter Palát'],
    #         'talk': 'Internetová bezpečnosť: základy sebaobrany'
    #     },
    #     {
    #         'time': '14:00- 14:30',
    #         'talk': "Programujeme v Pythone hardvér",
    #     },
    #     {
    #         'time': '14:45- 15:30',
    #         'talk': "Python ako nástroj pre STE(A)M problémy a úlohy",
    #     },
    #     {
    #         'time': '15:35- 16:05',
    #         'talk': "Programovací jazyk Robot Karel po novom a online.",
    #     },
    #     {
    #         'time': '16:20- 16:50',
    #         'talk': 'Vyhlásenie výsledkov SPy Cup a Python Cup'
    #     },
    #     {
    #         'time': '16:55- 17:25',
    #         'talk': "Z maturity v pascale na pythonovskú novú maturitu, študenstká mobilná apka o pythone v pythone a jednoduché grafické rozhranie pomocou libreoffice calc",
    #     }
    # ]
    #
    # FRIDAY2 = [
    #     {
    #         'time': '11:05- 12:10',
    #         'talk': "Programovanie vlastných micro:bit herných ovládačov a autíčok",
    #     },
    #     {
    #         'time': '13:10 - 13:55',
    #         'talk': "Životopis predáva",
    #     },
    #     {
    #         'time': '14:00 - 16:00',
    #         'talk': "Buď SMART s micro:bitom",
    #     }
    # ]
    #
    # SATURDAY = [
    #     {
    #         'time': '9:00 - 10:50',
    #         'talk': "Robíme IoT na mikrokontroléri ESP32 v jazyku MicroPython"
    #     },
    #     {
    #         'time': '11:05 - 12:10',
    #         'talk': "Jednoduchý blog vo Flasku",
    #     },
    #     {
    #         'time': '13:10 - 15:00',
    #         'talk': "Buď SMART s micro:bitom",
    #     },
    #     {
    #         'time': '15:20 - 16:50',
    #         'speakers': ['Jaroslav Výbošťok', 'Marek Mansell'],
    #         'talk': "Využitie otvorených dát a GPS s použitím tkinter a Jupyter"
    #     }
    # ]
    #
    # SATURDAY2 = [
    #     {
    #         'time': '9:00 - 10:50',
    #         'talk': "Zábava a informatika idú ruka v ruke ! :)",
    #     },
    #     {
    #         'time': '11:05 - 12:10',
    #         'talk': "Naučte sa programovať s CoderDojo",
    #     },
    #     {
    #         'time': '13:10 - 14:10',
    #         'talk': "Naprogramuj si robota Ozobot EVO",
    #     },
    # ]

    for spot in FRIDAY2:
        for talk in EDU_TALKS:
            if spot['title'] == talk['title']:
                spot['talk'] = talk
                spot['speakers'] = talk['speakers']
                continue

    for spot in SATURDAY2:
        for talk in EDU_TALKS:
            if spot['title'] == talk['title']:
                spot['talk'] = talk
                spot['speakers'] = talk['speakers']
                continue

    return render_template('edusummit.html', **_get_template_variables(li_edusummit='active', background='bkg-index',
                                                                       friday2=FRIDAY2, saturday2=SATURDAY2,
                                                                       speakers=EDU_SPEAKERS, talks=EDU_TALKS))


@app.route('/<lang_code>/thanks.html')
def thanks():
    return render_template('thanks.html', **_get_template_variables(li_cfp='active', background='bkg-index'))


@app.route('/<lang_code>/privacy-policy.html')
def privacy_policy():
    return render_template('privacy-policy.html', **_get_template_variables(li_privacy='active',
                                                                            background='bkg-privacy'))


@app.route('/<lang_code>/program/index.html')
def program():
    # variables = _get_template_variables(li_program='active', background='bkg-speaker', speakers=SPEAKERS)
    # variables['talks_list'] = []
    # variables['workshops_link'] = []
    #
    # for talk in TALKS:
    #     if talk['type'] == 'Talk':
    #         variables['talks_list'].append({
    #             'talk': talk,
    #             'speakers': talk['speakers']
    #         })
    #         continue
    #     elif talk['type'] == 'Workshop':
    #         variables['workshops_link'].append({
    #             'talk': talk,
    #             'speakers': talk['speakers']
    #         })
    #         continue
    #
    # return render_template('program.html', **variables)
    return redirect('/')


@app.route('/<lang_code>/speakers/index.html')
def speakers():
    variables = _get_template_variables(li_speakers='active', background='bkg-speaker', speakers=SPEAKERS+EDU_SPEAKERS)

    return render_template('speaker_list.html', **variables)

@app.route('/<lang_code>/speakers/<name>.html')
def profile(name):
    variables = _get_template_variables(li_speakers='active', background='bkg-speaker')

    for speaker in SPEAKERS+EDU_SPEAKERS:
        speaker['talks'] = []
        if speaker['name'].lower() == decode_name(name):
            for talk in TALKS + EDU_TALKS:
                if speaker['name'] in talk.get('speakers', []):
                    speaker.get('talks', []).append(talk)
            variables['speaker'] = speaker
            break

    if not variables.get('speaker'):
        return abort(404)

    return render_template('speaker.html', **variables)


@app.route('/<lang_code>/friday.html')
def friday():
    return render_template('schedule.html', **_get_template_variables(li_friday='active', magna=FRIDAY1,
                                                                      minor=FRIDAY2, babbageovaA=FRIDAY3,
                                                                      day=gettext('Friday'),
                                                                      background='bkg-speaker'
                                                                      ))

@app.route('/<lang_code>/saturday.html')
def saturday():
    return render_template('schedule.html', **_get_template_variables(li_saturday='active', magna=SATURDAY1,
                                                                      minor=SATURDAY2, babbageovaA=SATURDAY3,
                                                                      babbageovaB=SATURDAY4, digilab=SATURDAY5,
                                                                      day=gettext('Saturday'),
                                                                      background='bkg-speaker'))

@app.route('/<lang_code>/sunday.html')
def sunday():
    return render_template('schedule.html', **_get_template_variables(li_sunday='active', magna=SUNDAY1,
                                                                      babbageovaA=SUNDAY3, babbageovaB=SUNDAY4,
                                                                      day=gettext('Sunday'),
                                                                      background='bkg-speaker'))

@app.route('/<lang_code>/countdown.html')
def countdown():
    template_vars = _get_template_variables(li_index='active', background='bkg-index')
    return render_template('countdown.html', **template_vars)


@app.route('/<lang_code>/jobs.html')
def jobs():
    job_offers = get_jobs()
    companies = sorted(set(map(itemgetter("company"), job_offers)))
    template_vars = _get_template_variables(
        li_jobs='active',
        background='bkg-chillout',
        jobs=job_offers,
        companies=companies
    )
    return render_template('jobs.html', **template_vars)


@app.route('/<lang_code>/livestream-titans-room.html')
def livestream_titans_room():
    template_vars = _get_template_variables(
        li_livestream1='active',
        background='bkg-speaker',
        room_name='Titans room',
        youtube_stream='cudKMpOGmS4',
        slido_link='https://app.sli.do/event/cEPd2DTRrEKybtAK6nget8/live/questions?section=a550b24c-5361-4dfd-af63-01f811f53da5',
    )
    return render_template('livestream.html', **template_vars)


@app.route('/<lang_code>/livestream-spy-room.html')
def livestream_spy_room():
    template_vars = _get_template_variables(
        li_livestream2='active',
        background='bkg-speaker',
        room_name='SPy room',
        youtube_stream='wkqzkAros4Y',
        slido_link='https://app.sli.do/event/cEPd2DTRrEKybtAK6nget8/live/questions?section=86fb8dd8-d3c9-42ba-8ac9-3fb165f421e1',
    )
    return render_template('livestream.html', **template_vars)


def get_speaker_url():
    pass

def _get_template_variables(**kwargs):
    """Collect variables for template that repeats, e.g. are in body.html template"""
    variables = {
        'title': EVENT,
        'domain': DOMAIN,
        'lang_code': get_locale(),
    }
    variables.update(kwargs)

    return variables


def _get_schedule_variables(**kwargs):
    variables = _get_template_variables(**kwargs)
    lang_code = get_locale()
    _schedule_vars = ['magna', 'minor', 'babbageovaA', 'babbageovaB', 'digilab']
    for key, spots in kwargs.items():
        if key not in _schedule_vars:
            continue
        for spot in spots:
            name = spot.get('name')
            if name is None:
                continue
            _speakers = [spkr.strip() for spkr in name.split(',')]
            spkr = _speakers and _speakers[0]   # todo fix multiple speakers
            spot['speaker'] = url_for('profile', lang_code=lang_code,
                                      name=spkr.lower().replace('-', '--').replace(' ', '-'))
            # spot['speakers'] = [url_for('profile', lang_code=lang_code,
            #                             name=spkr.lower().replace('-', '--').replace(' ', '-'))
            #                     for spkr in _speakers]
    return variables


def _get_sponsors_variables(**kwargs):
    variables = _get_template_variables(**kwargs)
    # todo add sponsors json and make sponsors.html jinja template
    return variables


@app.before_request
def before():  # pylint: disable=inconsistent-return-statements
    if request.view_args and 'lang_code' in request.view_args:
        g.current_lang = request.view_args['lang_code']
        if request.view_args['lang_code'] not in LANGS:
            return abort(404)
        request.view_args.pop('lang_code')


@babel.localeselector
def get_locale():
    # try to guess the language from the user accept
    # header the browser transmits. The best match wins.
    # return request.accept_languages.best_match(['de', 'sk', 'en'])
    return g.get('current_lang', app.config['BABEL_DEFAULT_LOCALE'])
