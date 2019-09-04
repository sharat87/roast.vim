setl commentstring=#\ %s

py3 import vim, roast

if !exists('#roast_response_maps')
	aug roast_response_maps
		au!
		au BufNewFile __roast_* nnoremap <buffer> <silent> <C-j> :py3 roast.next_render()<CR>
		au BufNewFile __roast_* nnoremap <buffer> <silent> <C-k> :py3 roast.prev_render()<CR>
	aug END
endif

if &bg ==? 'light'
	highlight default RoastCurrentSuccess guibg=#E7F4D2 gui=bold
	highlight default RoastCurrentFailure guibg=#F4DFD2 gui=bold
else
	highlight default RoastCurrentSuccess guibg=#005A66 gui=bold
	highlight default RoastCurrentFailure guibg=#700e01 gui=bold
endif

exe 'nnoremap <buffer> <silent> ' . get(g:, 'roast_key_run', '<CR>') . ' :py3 roast.run()<CR>'

command! -buffer RoastSSLVerify py3 roast.verify_ssl = True
command! -buffer RoastSSLIgnore py3 roast.verify_ssl = False
