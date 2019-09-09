let s:roast_ssl = 'verify'
if exists('b:roast_ssl')
	let s:roast_ssl = b:roast_ssl
elseif exists('g:roast_ssl')
	let s:roast_ssl = b:roast_ssl
endif

if s:roast_ssl ==? 'verify'
	RoastSSLVerify
elseif s:roast_ssl ==? 'ignore'
	RoastSSLIgnore
else
	echoerr 'Invalid value for roast_ssl. Must be "verify" or "ignore".'
endif
