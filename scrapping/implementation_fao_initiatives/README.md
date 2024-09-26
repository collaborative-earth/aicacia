## Scrapping URL
https://ferm.fao.org/search/initiatives

## Details
Create a temp directory
```
mkdir temp
```

Get list of all the practices
```
cd scrapping/implementation_fao_good_practices/
pipenv run python3 list_all_initiatives.py
```

For each of the practice, download HTML and PDF.
```
pipenv run python3 get_all_html_pdfs.py
```

Note: The script for the first time will fail with folder doesnot exist, please create those folders if they dont exist.