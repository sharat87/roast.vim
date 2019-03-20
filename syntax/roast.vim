if exists("b:current_syntax")
    finish
endif

let b:current_syntax = 'roast'

syn match roastComment "\v^#.*$"
syn match roastInterpolated "\v\{\@?\k+\}" contained

syn match roastPath "\v[^ ]+" contained nextgroup=roastParams skipwhite contains=roastInterpolated
syn match roastHeaderVal ".*" nextgroup=roastHeaderVal contained contains=roastInterpolated
syn match roastHeaderKey "\v^[a-zA-Z-]+:" nextgroup=roastHeaderVal contains=roastInterpolated
syn match roastParams "\v.*" contained contains=roastInterpolated

syn match roastVerbGet "\v\c^GET\ze " nextgroup=roastPath skipwhite contains=roastInterpolated
syn match roastVerbPost "\v\c^POST\ze " nextgroup=roastPath skipwhite contains=roastInterpolated
syn match roastVerbPatch "\v\c^PATCH\ze " nextgroup=roastPath skipwhite contains=roastInterpolated
syn match roastVerbPut "\v\c^PUT\ze " nextgroup=roastPath skipwhite contains=roastInterpolated
syn match roastVerbHead "\v\c^HEAD\ze " nextgroup=roastPath skipwhite contains=roastInterpolated
syn match roastVerbDelete "\v\c^DELETE\ze " nextgroup=roastPath skipwhite contains=roastInterpolated

syn match roastSet "\v\c^set\ze " nextgroup=roastVarName skipwhite
syn match roastVarName "\v\k+" contained nextgroup=roastVarVal skipwhite
syn match roastVarVal "\v.+" contained contains=roastInterpolated

syn match roastTplKeyword "\v\c^template\ze " nextgroup=roastTplName skipwhite
syn match roastTplName "\v\k+" contained

syn include @json syntax/json.vim
syn region roastJsonBody start="\v^\{" end="\v\}$" contains=@json

hi link roastVerbGet roastVerb
hi link roastVerbPost roastVerb
hi link roastVerbPatch roastVerb
hi link roastVerbPut roastVerb
hi link roastVerbHead roastVerb
hi link roastVerbDelete roastVerb
hi link roastVerb DiffAdd

hi link roastComment Comment
hi link roastPath Constant
hi link roastHeaderKey Identifier
hi link roastHeaderVal String
hi link roastJsonBody SpecialComment
hi link roastSet Type
hi link roastVarName Identifier
hi link roastTplKeyword Type
hi link roastTplName Identifier
hi link roastInterpolated Type
