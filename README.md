# Lore 2021

## Installation

### Local installation
 1. Install python (3.6 and above would do fine, 3.9 is best), making sure python is in the path and that pip is enabled 
 2. Open a command prompt in the 2021 directory and type in **pip install --progress-bar pretty --no-cache-dir --upgrade -r requirements.txt**
 3. Run **python manage.py generate_secret_key --replace** and then **python manage.py migrate**
 4. Run python manage.py createsuperuser to create an admin account
 
### Docker installation
 1. Install docker desktop (might take a little more system ressources than local mode) and run it.
 2. Run create_user.bat to... wait for it... create an admin account
 
## Running the application
Select the run_{XXX}.bat that corresponds to your installation type and leave it open if in local mode.
Then, in a browser, go to http://localhost:2021 and login.

To add your ods file, there is a trombone icon in the donations page.