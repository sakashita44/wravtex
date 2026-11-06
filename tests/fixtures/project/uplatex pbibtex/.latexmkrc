use Cwd 'abs_path';
$pdf_mode = 3;
$latex = 'uplatex -interaction=nonstopmode -halt-on-error -file-line-error %O %S';
$bibtex = 'pbibtex -kanji=utf8 %O %B';
$dvipdf = 'dvipdfmx %O -o %D %S';
$bibtex_use = 2;
ensure_path('TEXINPUTS', '../common//');
ensure_path('BIBINPUTS', abs_path('../common'));
