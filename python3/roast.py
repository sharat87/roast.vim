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
from threading import Thread

import requests
import vim

import roast_api


sessions = defaultdict(requests.Session)

verify_ssl = True

renderers = [
    'pretty',
    'headers',
]

IS_NEOVIM = vim.eval("has('nvim')") == '1'

CURRENT_RESPONSE = None


def run(*, use=None):
    request = roast_api.build_request(vim.current.buffer, vim.current.range.end, use_overrides=use)
    if IS_NEOVIM:
        run_th(request, vim.current.buffer.number, vim.current.range.end)
    else:
        Thread(target=run_th, args=(request, vim.current.buffer.number, vim.current.range.end), daemon=True).start()


def run_th(request, buf_number, line_number):
    global CURRENT_RESPONSE
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', requests.urllib3.exceptions.InsecureRequestWarning)
            response = request.send(sessions[buf_number])
    except OSError as e:
        show_error(str(e))
    else:
        CURRENT_RESPONSE = response
        vim.eval("timer_start(10, {_ -> py3eval('roast.show_response_current()')})")
        vim.eval("timer_start(10, {_ -> py3eval('roast.highlight_line(\"" +
                 ('RoastCurrentSuccess' if response.ok else 'RoastCurrentFailure') +
                 '", ' + str(buf_number) + ', ' + str(line_number) + ")')})")


def show_response_current():
    show_response(CURRENT_RESPONSE)


def show_response(response: requests.Response):
    # A window holding a roast buffer, to be used as a workspace for setting up all roast buffers.
    workspace_window = workspace_renderer = None
    for window in vim.windows:
        if '_roast_renderer' in window.buffer.vars:
            workspace_window = window
            workspace_renderer = window.buffer.vars['_roast_renderer']
            if not isinstance(workspace_renderer, str):
                workspace_renderer = workspace_renderer.decode()
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
        workspace_window.options['statusline'] = "Roast <%{get(b:, '_roast_renderer', 'N/A')}>  " + \
                ('' if response.ok else '%#Error#') + " HTTP:" + str(response.status_code) + " %*  %{&ft}"

    vim.command(f'{workspace_window.number}windo keepalt buffer __roast_{workspace_renderer or renderers[0]}__')
    vim.current.window = prev_window


def show_error(message: str):
    vim.vars['__roast_error_message'] = message
    vim.eval("timer_start(10, {_ -> execute(['echohl Error', 'redraw', 'echomsg g:__roast_error_message',"
             " 'echohl None', 'unlet g:__roast_error_message'], '')})")


def highlight_line(group, buf_number, line_number):
    match_id = int(vim.buffers[buf_number].vars.get('_roast_match_id', 0))

    if match_id:
        win = None
        for win in vim.windows:
            if win.buffer.number == buf_number:
                break

        try:
            vim.eval(f'matchdelete({match_id})' if win is None else f'matchdelete({match_id}, {win.number})')
        except vim.error:
            # TODO: Only hide E803 error, which is thrown if this match_id has already been deleted.
            pass

    vim.buffers[buf_number].vars['_roast_match_id'] = vim.eval(
        fr"matchadd('{group}', '\V' . escape(getbufline({buf_number}, {line_number + 1})[0], '\') . '\$')"
    )


def apply_actions(buf, actions):
    if 'lines' in actions:
        buf[:] = actions['lines']

    if 'commands' in actions:
        for cmd in actions['commands']:
            vim.command(cmd)


def next_render(delta=1):
    renderer = vim.current.buffer.vars['_roast_renderer']
    if not isinstance(renderer, str):
        renderer = renderer.decode()
    vim.command('buffer __roast_' + renderers[(renderers.index(renderer) + delta) % len(renderers)] + '__')


def prev_render():
    next_render(-1)


def bufnr(name) -> int:
    return int(vim.eval(f'bufnr("{name}")'))
