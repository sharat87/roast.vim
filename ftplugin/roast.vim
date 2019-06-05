setl commentstring=#\ %s

nnoremap <buffer> <silent> <CR> :call roast#run()<CR>

command! -buffer RoastSSLVerify py3 roast.verify_ssl = True
command! -buffer RoastSSLIgnore py3 roast.verify_ssl = False
