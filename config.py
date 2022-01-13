import json
from itertools import chain

PROPERTIES = 'properties.json'

def throw_config_error(err, reason):
    raise Exception("\nConfiguration Error in: {0}\nCaused by: {1}".format(err, reason))

def get_unified_ages_from_obj(obj):
    return sorted(chain(*[range(x['lower-limit'], x['upper-limit'] + 1) for x in obj]))

def check_cpf_contribution_config(config):
    age = get_unified_ages_from_obj(config['cpf']['contribution-rate'])
    if len(age) == 0 or min(age) > config['current-age'] or max(age) < config['retirement-age'] \
            or (set(range(min(age), max(age) + 1)) - set(age)) or list(set(age)) != age:
        throw_config_error(config['cpf']['contribution-rate'],
                           'Age ranges are invalid/insufficient, '
                           'Current Age: {0}, Retirement Age: {1}'
                           .format(config['current-age'], config['retirement-age']))

def check_retirement_age_config(config):
    if(config['retirement-age'] < config['current-age']):
        throw_config_error("Current age/Retirement age", 'Current age > Retirement age')

def check_salary_config(config):
    age = get_unified_ages_from_obj(config['salary'])
    if len(age) == 0 or min(age) > config['current-age'] or max(age) < config['retirement-age'] \
            or (set(range(min(age), max(age) + 1)) - set(age)) or list(set(age)) != age:
        throw_config_error(config['salary'],
                           'Age ranges are invalid/insufficient, '
                           'Current Age: {0}, Retirement Age: {1}'
                           .format(config['current-age'], config['retirement-age']))

def check_extra_interest_config(config):
    if(config['cpf']['total-extra-interest-cap'] < config['cpf']['oa']['extra-interest-cap']):
        throw_config_error('OA extra interest cap/Combined extra interest cap',
                           'OA extra interest cap > Combined extra interest cap')

def check_config(config):
    check_retirement_age_config(config)
    check_cpf_contribution_config(config)
    check_salary_config(config)
    check_extra_interest_config(config)

def load():
    with open(PROPERTIES) as config_data:
        config = json.load(config_data)
    check_config(config)
    return config