au BufRead,BufNewFile *.roast setf roast

if get(g:, 'roast_http_ext', 0) == 1
  au BufRead,BufNewFile *.http setf roast
endif
