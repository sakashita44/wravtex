use Cwd 'abs_path';
$pdf_mode = 1;
$pdflatex = 'pdflatex -interaction=nonstopmode -halt-on-error -file-line-error %O %S';
$bibtex_use = 2;
ensure_path('TEXINPUTS', '../common//');
ensure_path('BIBINPUTS', abs_path('../common'));
