# WebForm
Example of full stack web form developed for Utepils Brewing. Utilizes Flask, HTML/CSS/JS, &amp; Firebase/Firestore

## Purpose of Repo

The purpose of this repo is to demonstrate a basic, in-production use of a web form written in HTML/CSS &amp; vanilla JavaScript. The backend is written in Flask with user authentication and storage run through Firebase/Firestore. All data in the repo is test data.

Being that the repo is an example, some features have been disabled for privacy & security reasons.

## High Level Business requirements

The business required a simple, dynamic web form that would allow for easy tracking of product removals without the need for paper forms or verbal communcation. The webform presents a few basic input fields &amp; radio button fields for selecting items that are important to the business and then a fillable table to input various size varieties and quantities taken.  Submitted data is stored in a Firestore document.

The webform is controlled by an administrator portal (user authentication setup and managed by Firebase) where an admin can modify what products are presented in the main form. The admin portal also allows for querying of the Firestore document database based on business criteria including submitted date.

# Configuring & running the form

## Requirements for running
- Python
- Firebase
- Docker (if running as Docker container)

## Configuring service to run

- Create a new Firebase project and initialize a new Firestore document database.
- Make note of the Firestore document database name
- Enter the database name as the `DATABASE_COLLECTION_NAME` environment variable valuep
- Copy/download the .json file with the credentials and save it.
- Copy the contents of the .json file into the `.env` file and reformat the key/values.
- Create a new Firestore document for the webform's config. Make note of the document name
- Add the document ID or name into the `.env` file
- Update fields within [app_config.json](./configs/app_config.json) to populate data


## Running Service

The entire form is run from Flask using Jinja2 templates to populate the data. Serving the form can done in two ways
1. Running `flask run` in the server/src directory
    - this will run a debug version or non-production version of the app
2. Running `gunicorn -c gunicorn_settings.py wsgi:app`
    - this will run a WSGI enabled version of the application
    - NOTE: `gunicorn` is only enabled on Linux/MacOS and not on Windows
        - you can use `waitress` to serve the application on Windows if needed

## Interacting with the Form

The service has three routes: `/`, `/login`, and `/admin`. The root path is the main user form while `/login` and `/admin` are used to modify and manage the form. To modify the main form, create a user within Firebase then log into the `/admin` route to modify the form.

# License
All rights reserved. No commercial or AI training use without prior, written consent.