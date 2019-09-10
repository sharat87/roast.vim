"""
Core functionality for roast.vim plugin. This module is inteded to be testable outside vim, so MUST NOT import the `vim`
module.
"""

import shlex
from itertools import takewhile
from typing import List, Dict, Optional
import json
from pathlib import Path
from xml.dom import minidom
from xml.parsers.expat import ExpatError
from jinja2 import Template
import re

import requests


class Request:
    def __init__(self, method, url, headers, params=None, data=None, auth=None, verify_ssl=True):
        self.method = method
        self.url = url
        self.headers = headers
        self.params = params
        self.data = data
        self.auth = auth
        self.verify_ssl = verify_ssl

    def send(self, session: requests.Session = None) -> requests.Response:
        session.auth = self.auth
        return session.send(requests.Request(
            self.method,
            self.url,
            self.headers,
            params=self.params,
            data=self.data,
        ).prepare(), verify=self.verify_ssl)


def build_request(lines, line_num, *, use_overrides=None) -> Request:
    config = {}
    headers = {}
    variables = {}
    aliases = {}
    templates = {}
    current_template = None
    heredoc = None

    # TODO: Need an actual parser.
    for line in lines[:line_num]:
        if heredoc:
            if line == heredoc:
                heredoc = None
            continue

        heredoc = pop_heredoc(tokenize(line))
        if heredoc:
            continue

        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            continue

        is_indented = line.startswith(' ' * 4)
        if not is_indented:
            current_template = None
        elif current_template:
            current_template.append(line)
            continue

        parts = tokenize(line)
        if len(parts) < 1:
            continue

        head, *rest = parts

        if head == 'set':
            # Interpolations in variables are applied when the variable is defined.
            variables[rest[0]] = Template(' '.join(rest[1:])).render(**variables)

        elif head == 'alias':
            # Interpolations in aliases are applied when the alias is used.
            aliases[rest[0]] = ' '.join(rest[1:])

        elif head == 'use':
            if len(rest) > 1:
                config[rest[0]] = ' '.join(rest[1:])
            else:
                del config[rest[0]]

        elif head.endswith(':'):
            key = head[:-1].lower()
            if rest:
                headers[key] = Template(' '.join(rest)).render(**variables)
            else:
                del headers[key]

        elif head == 'template':
            templates[rest[0]] = current_template = []

    line = lines[line_num]
    for alias, replacement in aliases.items():
        if line.startswith(alias + ' '):
            line = line.replace(alias + ' ', replacement, 1)
            break

    method, loc, *tokens = tokenize(line)

    heredoc = pop_heredoc(tokens)
    if heredoc:
        body = '\n'.join(takewhile(lambda l: l != heredoc, lines[line_num + 1:]))
    else:
        file_path = pop_file_body(tokens)
        body = file_path.read_text() if file_path else None

    if body:
        body = Template(body).render(**variables)

    if use_overrides:
        config.update(use_overrides)

    url_prefix = None
    if 'url_prefix' in config:
        url_prefix = config['url_prefix']
    elif 'host' in headers:
        url_prefix = headers['host']
        # TODO: Using host header this way is against the HTTP spec and should be removed. See issue #14.
        if '/' in url_prefix or url_prefix.startswith('http:') or url_prefix.startswith('https:'):
            del headers['host']

    url = Template(loc).render(**variables)
    if url_prefix and not re.match(r'https?://', url):
        url = url_prefix.rstrip('/') + '/' + url.lstrip('/')

    params = build_params_dict(tokens, variables)

    # TODO: Use syntax like `use http_auth basic user password` instead.
    auth = None
    if 'http_auth_username' in config and 'http_auth_password' in config:
        auth = config['http_auth_username'], config['http_auth_password']

    return Request(method, url, headers, params=params, data=body, auth=auth)


def pop_heredoc(tokens: List[str]) -> Optional[str]:
    heredoc = None
    if tokens and tokens[-1].startswith('<<'):
        heredoc = tokens.pop()[2:]
    elif len(tokens) >= 2 and tokens[-2] == '<<':
        heredoc = tokens.pop()
        tokens.pop()
    return heredoc


def pop_file_body(tokens: List[str]) -> Optional[Path]:
    loc = None
    if tokens and tokens[-1].startswith('<'):
        loc = tokens.pop()[1:]
    elif len(tokens) >= 2 and tokens[-2] == '<':
        loc = tokens.pop()
        tokens.pop()
    return loc and Path(loc)


def build_params_dict(tokens: List[str], variables: Dict[str, str] = None) -> Dict[str, str]:
    if variables is None:
        variables = {}

    params = {}
    for var in tokens:
        if '=' in var:
            name, value = var.split('=', 1)
            value = Template(value).render(**variables)
        else:
            name, value = var, variables[var]
        params[name] = variables[name] = value

    return params


def tokenize(text: str) -> List[str]:
    return shlex.split(text, comments=True)


def render_pretty(buf, response):
    blueprint = {'commands': ['call clearmatches()']}
    content_type = response.headers['content-type'].split(';')[0] if 'content-type' in response.headers else 'text/html'
    if content_type.endswith('/json'):
        try:
            blueprint['lines'] = json.dumps(response.json(), ensure_ascii=False, indent=2).splitlines()
        except json.JSONDecodeError:
            blueprint['commands'].append('set filetype=txt')
            blueprint['commands'].append('call matchaddpos("Error", range(1, line("$")))')
        else:
            blueprint['commands'].append('set filetype=json')

    elif content_type.endswith('/xml'):
        try:
            blueprint['lines'] = minidom.parseString(response.text).toprettyxml().splitlines()
        except ExpatError:
            blueprint['commands'].append('set filetype=txt')
            blueprint['commands'].append('call matchaddpos("Error", range(1, line("$")))')
        else:
            blueprint['commands'].append('set filetype=xml')

    elif content_type.endswith('/html'):
        blueprint['commands'].append('set filetype=html')

    if not blueprint.get('lines'):
        blueprint['lines'] = response.text.splitlines()

    return blueprint


def render_headers(buf, response):
    lines = ['=== Response Headers ===']
    for key, value in response.headers.items():
        lines.append(f'{key}: {value}')

    lines.append('')
    lines.append('')
    lines.append('=== Request Headers ===')
    for key, value in response.request.headers.items():
        lines.append(f'{key.title()}: {value}')

    return {'lines': lines}
