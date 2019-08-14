aug roast_response_maps
	au!
	au BufNewFile __roast_* nnoremap <buffer> <silent> <C-j> :py3 roast.next_render()<CR>
	au BufNewFile __roast_* nnoremap <buffer> <silent> <C-k> :py3 roast.prev_render()<CR>
aug END

if (&bg ==? 'light')
	highlight default RoastCurrentSuccess guibg=#E7F4D2 gui=bold
	highlight default RoastCurrentFailure guibg=#F4DFD2 gui=bold
else
	highlight default RoastCurrentSuccess guibg=#005A66 gui=bold
	highlight default RoastCurrentFailure guibg=#700e01 gui=bold
endif

py3 import roast

fun! roast#run()
	py3 roast.run()
endfun

fun! roast#show_error()
	if exists('b:_roast_error') && !empty(b:_roast_error)
		echohl Error
		redraw
		echomsg b:_roast_error
		echohl None
	endif
endfun
