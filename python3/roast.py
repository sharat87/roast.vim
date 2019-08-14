"""
The implementation module for roast.vim plugin. This module does most of the heavy lifting for the functionality
provided by the plugin.

Example: Put the following in a `api.roast` file and hit `<Leader><CR>` on it.

    GET http://httpbin.org/get name=value

Inspiration / Ideas:
    https://github.com/Huachao/vscode-restclient
    https://github.com/baverman/vial-http
"""

from collections import defaultdict
import warnings

import requests
import vim

import roast_api


sessions = defaultdict(requests.Session)

verify_ssl = True

renderers = [
    'pretty',
    'headers',
]


def run():
    request = roast_api.build_request(vim.current.buffer, vim.current.range.end)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', requests.urllib3.exceptions.InsecureRequestWarning)
            response = request.send(sessions[vim.current.buffer.number])
    except OSError as e:
        vim.current.buffer.vars['_roast_error'] = str(e)
        vim.command(f"call roast#show_error()")
    else:
        show_response(response)
        highlight_line_text('RoastCurrentSuccess' if response.ok else 'RoastCurrentFailure')


def show_response(response: requests.Response):
    # A window holding a roast buffer, to be used as a workspace for setting up all roast buffers.
    workspace_window = workspace_renderer = None
    for window in vim.windows:
        if '_roast_renderer' in window.buffer.vars:
            workspace_window = window
            workspace_renderer = window.buffer.vars['_roast_renderer'].decode()
            break

    # Switch to workspace window.
    prev_window = vim.current.window

    for renderer in renderers:
        buf_name = f'__roast_{renderer}__'
        num = bufnr(buf_name)
        if num < 0:
            if workspace_window is not None:
                vim.current.window = workspace_window
                vim.command(f'keepalt edit {buf_name} | setl bt=nofile bh=hide noswf nornu')
                num = bufnr(buf_name)
            else:
                vim.command(f'keepalt vnew {buf_name} | setl bt=nofile bh=hide noswf nornu')
                num = bufnr(buf_name)
                vim.current.window = workspace_window = vim.windows[int(vim.eval(f'bufwinnr({num})')) - 1]
        else:
            if workspace_window is not None:
                vim.current.window = workspace_window
                vim.command(f'keepalt {num}buffer')
            else:
                vim.command(f'keepalt vertical {num}sbuffer')
                vim.current.window = workspace_window = vim.windows[int(vim.eval(f'bufwinnr({num})')) - 1]

        buf = vim.buffers[num]
        buf[:] = None

        buf.vars['_roast_renderer'] = renderer
        actions = getattr(roast_api, f'render_{renderer}')(buf, response)
        apply_actions(buf, actions)

    if vim.current.window is workspace_window:
        vim.command(f'keepalt buffer __roast_{workspace_renderer or renderers[0]}__')

    vim.current.window = prev_window


def highlight_line_text(group):
    match_id = int(vim.current.buffer.vars.get('_roast_match_id', 0))

    if match_id:
        try:
            vim.eval(f'matchdelete({match_id})')
        except vim.error:
            # TODO: Only hide E803 error, which is thrown if this match_id has already been deleted.
            pass

    vim.current.buffer.vars['_roast_match_id'] = vim.eval(f"matchadd('{group}', '\\V{vim.current.line}')")


def apply_actions(buf, actions):
    if 'lines' in actions:
        buf[:] = actions['lines']

    if 'commands' in actions:
        for cmd in actions['commands']:
            vim.command(cmd)


def next_render(delta=1):
    renderer = vim.current.buffer.vars['_roast_renderer'].decode()
    vim.command('buffer __roast_' + renderers[(renderers.index(renderer) + delta) % len(renderers)] + '__')


def prev_render():
    next_render(-1)


def bufnr(name) -> int:
    return int(vim.eval(f'bufnr("{name}")'))
