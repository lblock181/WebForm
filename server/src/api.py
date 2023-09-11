import logging
import functools
from traceback import print_exc
from typing import Callable
from io import BytesIO

from controller import Controller
from jinja2 import TemplateNotFound
from datetime import datetime
from flask import render_template, Blueprint, abort, request, make_response, redirect, send_file, url_for

api = Blueprint("api", __name__, template_folder="templates")
ctrl = Controller()

def login_required(func) -> Callable:
    @functools.wraps(func)
    def secure_func(*args, **kwargs) -> Callable:
        if 'session' not in request.cookies or not ctrl.validate_user(request.cookies['session']):
            return redirect(url_for('api.login'))
        return func(*args, **kwargs)
    return secure_func

@api.get('/')
def index() -> dict:
    try:
        form_config = ctrl.read_config()
        return render_template('mainform.html', 
                               beer_list=form_config['beerList'], 
                               distrib_list=form_config['distributorList'],
                               max_date=datetime.today().strftime("%Y-%m-%d"),
                               beer_list_str=form_config['beerList'])
    except TemplateNotFound:
        logging.error('MainForm template not found')
        abort(404)

@api.post('/')
def submit_new_form() -> dict:
    try:
        rjson = request.json
        form_submit_success = ctrl.new_form_submit(rjson)
        resp = create_api_response(form_submit_success, "Submission successful" if form_submit_success else "Submission failed")
    except Exception as e:
        logging.error(str(e))
        print(print_exc())
        resp = create_api_response(False, "An error occurred while submitting. Please try again.")
    finally:
        return resp

@api.get('/admin')
@login_required
def get_admin_page() -> str:
    try:
        form_config = ctrl.read_config(sort_config=True)
        return render_template('admin.html', config_content=form_config)
    except TemplateNotFound:
        logging.error("Admin template not found")
        abort(404)

@api.post('/admin/saveConfig')
@login_required
def save_config() -> str:
    try:
        config_success = ctrl.update_config(request.json)
        resp = create_api_response(config_success, "Config updated" if config_success else "Config update failed")
    except Exception as e:
        logging.error(f'Config update failed - {e}')
        resp = create_api_response(False, "Unexpected error occurred while updating config")
    finally:
        return resp

@api.route('/login', methods=['POST', 'GET'])
def login(ret_status=''):
    if request.method == 'GET':
        try:
            return render_template('login.html', status=ret_status)
        except TemplateNotFound:
            logging.error("Login template not found")
            abort(404)
    
    ret_status = ""
    session_cookie = ""

    email=request.form['username']
    password=request.form['password']
    if email is None or password is None:
        ret_status = "Username and/or password cannot be empty. Please try again."
    
    try:
        login_success, login_msg = ctrl.sign_in_email_password(email, password)
        if login_success:
            session_cookie = ctrl.generate_session_cookie()
        else:
            ret_status = login_msg
    except Exception as e:
        logging.error(e)
        ret_status = "Authentication failed. Try again or contact developer."
        session_cookie = ""
    finally:
        if ret_status == '':
            resp = redirect(location='admin', Response=make_response(render_template('admin.html')))
        else:
            resp = make_response(render_template('login.html',status=ret_status))
        resp.set_cookie("session", session_cookie)
        return resp

@api.route('/resetPassword',methods=['POST','GET'])
def reset_password(ret_status:str = "") -> str:
    if request.method == 'GET':
        try:
            return render_template('reset_password.html', status=ret_status)
        except TemplateNotFound:
            logging.error("Login template not found")
            abort(404)
    user_email = request.form['username']
    if ctrl.is_valid_email(user_email):
        if ctrl.reset_user_password(user_email):
            logging.info(f"Password reset email sent for {user_email}")
        else:
            logging.info(f"Password reset requested for email {user_email} but no user exists")
        ret_status = "If the email you provided is valid, we have sent a password reset email to that address"
    else:
        ret_status = "Invalid or missing username/email. Please try again"
    return make_response(render_template('reset_password.html', status=ret_status))

@api.post('/devUpdateConfig')
def update_full_config():
    if ctrl.update_full_config(request.headers['apikey'], request.json):
        return create_api_response(True, "Full config updated")
    else:
        return create_api_response(False, "Config not updated"), 400

@api.post('/downloadReport')
def download_report() -> bool:
    try:
        rjson = request.json
        file_bytes = ctrl.get_report(rjson)
        if isinstance(file_bytes, bytes):
            return send_file(
                path_or_file=BytesIO(file_bytes),
                mimetype='application/vnd.ms-excel',
                download_name="Utepils_Removals_Report.xlsx",
                as_attachment=True
            )
        elif isinstance(file_bytes, str):
            return create_api_response(False, file_bytes), 400
        else:
            raise Exception("Report unable to be generated. file_bytes is None")
    except Exception as e:
        logging.error(str(e))
        return create_api_response(False, "Failed to get report. Try again or contact developer"), 400

@api.get('/healthCheck')
def health_check() -> dict:
    return create_api_response(True, "Health Check Ok", status="running")

def create_api_response(success:bool, response_message:str, **kwargs) -> dict:
    resp = {
        "success": success,
        "status_message": response_message,
        **kwargs
        }
    return resp
