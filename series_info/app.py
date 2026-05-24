import json
import logging
from typing import Type

import flask
import requests
from flask import stream_template, request, redirect

from series_info import providers, data

app = flask.Flask(__name__)


def find_provider(provider_name) -> Type[data.Provider]:
    if provider_name not in providers.providers:
        raise RuntimeError('No provider named ' + provider_name)
    return providers.providers[provider_name]


@app.route("/<string:provider>/search", methods=['POST'])
def search(provider: str):
    provider_cls = find_provider(provider)
    obj = provider_cls()
    query = request.form.get('search')
    results = obj.search(query)
    return stream_template("search_results.html", series_list=results, provider=obj)


@app.route("/<string:provider>", methods=['GET', 'POST'])
def select_series(provider: str):
    if provider == 'favicon.ico':
        return ""
    provider_cls = find_provider(provider)
    obj = provider_cls()

    if request.method == 'POST':
        series_slug = request.form.get('series')
        return redirect('/%s/%s' % (provider_cls.slug, series_slug))

    return stream_template("select_series.html", provider=obj, recent=[])


@app.route("/<string:provider>/<string:series_slug>.json")
def series_json(provider, series_slug: str):
    provider_cls = find_provider(provider)
    obj = provider_cls()
    args = flask.request.args.to_dict()
    series = obj.series(series_slug, **args)
    return [series]


@app.route("/<string:provider>/<string:series_slug>/episodes.json")
def episodes_json(provider, series_slug: str = None):
    # lib = importlib.import_module("providers.provider_" + provider)
    provider_cls = find_provider(provider)
    obj = provider_cls()
    args = flask.request.args.to_dict()
    if 'search' in args and hasattr(obj, 'search'):
        return obj.search(**args)
    try:
        episodes = obj.episodes(series_slug, **args)
    except RuntimeError as e:
        return {'error': str(e)}

    return episodes


@app.route("/<string:provider>/<string:series_slug>/episode.json")
def episode_json(provider, series_slug: str):
    provider_cls = find_provider(provider)
    obj = provider_cls()
    args = flask.request.args.to_dict()
    episode_name = args['name']
    del args['name']
    try:
        episodes = obj.episodes(series_slug, **args)
        for episode in episodes:
            if episode.title is None:
                continue
            if episode.title == episode_name:
                return [episode]
            pass

    except RuntimeError as e:
        return {'error': str(e)}

    return []


@app.route("/<string:provider>/<string:series_slug>/bbcode")
@app.route("/<string:provider>/<string:series_slug>/bbcode/<int:season>")
def season_bbcode(provider, series_slug: str, season: int = None):
    # lib = importlib.import_module("providers.provider_" + provider)
    provider_cls = find_provider(provider)
    obj = provider_cls()
    args = flask.request.args.to_dict()
    series = obj.series(series_slug, **args)
    episodes = obj.episodes(series_slug, **args)
    if season is not None:
        episodes = [episode for episode in episodes if episode.season == season]

    response = stream_template("season_bbcode.j2", series=series, episodes=episodes, provider=obj)
    return Response(response=response, status=200, mimetype="text/plain")


@app.route("/<string:provider>/<string:series_slug>")
def episodeguide(provider, series_slug: str = None):
    cache = request.headers.get('HTTP_CACHE_CONTROL') != 'no-cache'

    provider_cls = find_provider(provider)

    obj = provider_cls()
    logger = logging.getLogger("pydisney")
    logger.setLevel(logging.DEBUG)
    args = flask.request.args.to_dict()
    # if series_slug:
    #     args['slug'] = series_slug
    if 'order' in args and args.get('order') == 'default':
        del args['order']

    if 'language' in args and args.get('language') == 'default':
        del args['language']

    if 'search' in args:
        try:
            return stream_template("search_results.html", series_list=obj.search(**args), provider=obj)
        except NotImplementedError:
            del args['search']

    try:
        series_info = obj.series(series_slug)
    except requests.exceptions.HTTPError:
        return flask.abort(404)
    episodes = obj.episodes(series_slug, **args)

    return stream_template("episodeguide.html", episodes=episodes, series=series_info, provider=obj)


@app.route("/")
def select_provider():
    return stream_template("select_provider.html", providers=providers.providers, title='Select provider')


if __name__ == "__main__":
    app.run()
