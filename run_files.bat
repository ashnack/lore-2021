pip install --progress-bar pretty --no-cache-dir --upgrade -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py create_files
