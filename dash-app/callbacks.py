import dash

from dash.dependencies import Input, Output, State
from app import app
import re

from lib.here import get_geocode, get_here_map, get_places_nearby, add_markers, get_route_summaries
from lib.do import find_possible_sites

def get_deployment_uid(query_param):
  deployment_uid = None

  if query_param and 'deployment' in query_param:
    m = re.match(r'deployment=[^&]*', query_param[1:], re.I)
    deployment_uid = m.group()[len('deployment='):]

  return deployment_uid


def reset_map(address):
  geocode = get_geocode(address)
  here_map = None

  if geocode:
    here_map = get_here_map(geocode)

  return here_map, geocode


def find_places(geocode, categories, max_distance, max_results):
  places = []

  if len(categories) > 0:
    places = get_places_nearby(
      geocode,
      categories=categories, 
      max_distance_km=max_distance,
      results_limit=max_results
    )

  return places


def show_places(here_map, places):
  markers = [p.marker() for p in places]
  add_markers(here_map, markers, fit_bounds=True)


def handle_optimize(places, deployment_uid):
  route_summaries = get_route_summaries(places)
  possible_sites, status = find_possible_sites(places, route_summaries, number_sites=3, deployment_uid=deployment_uid)
  return possible_sites, status


@app.callback(
  [
    Output('hereMap', 'srcDoc'),
    Output('currentGeocode', 'value'),
    Output('solutionStatus', 'children')
  ],
  [
    Input('optimizeButton', 'n_clicks'),
    Input('searchButton', 'n_clicks')
  ],
  [
    State('addressInput', 'value'),
    State('maxDistance', 'value'),
    State('maxResults', 'value'),
    State('selectCategories', 'value'),
    State('currentGeocode', 'value'),
    State('url', 'search')
  ]
)
def map_update(optimize_btn, search_btn, address, max_distance, max_results, categories, geocode, query_param):
  ctx = dash.callback_context

  if not ctx.triggered:
    button_id = None
  else:
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

  deployment_uid = get_deployment_uid(query_param)
  here_map, current_geocode = reset_map(address)
  places = find_places(current_geocode, categories, float(max_distance), int(max_results))

  if button_id == 'optimizeButton':
    possible_sites, status = handle_optimize(places, deployment_uid)
    show_places(here_map, possible_sites)
  else:
    status = ''
    show_places(here_map, places)
  
  map_html = here_map.get_root().render()

  return map_html, current_geocode, status


@app.callback(
    [
      Output('optimizeButton', 'disabled'),
      Output('searchButton', 'disabled')
    ],
    [
      Input('optimizeButton', 'n_clicks'),
      Input('searchButton', 'n_clicks'),
      Input('currentGeocode', 'value')
    ])
def disable_enable_buttons(optimize_btn, search_btn, geocode):
  ctx = dash.callback_context

  if not ctx.triggered:
    button_id = None
  else:
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

  if button_id in ['optimizeButton', 'searchButton']:
    if (optimize_btn is not None and optimize_btn > 0) or (search_btn is not None and search_btn > 0):
      return True, True
    else:
      return False, False
  else:
    return False, False
