from datetime import datetime
import json
import logging
from google.cloud import logging as gcloudlogging
from os import getenv
from traceback import print_exc
from requests.exceptions import HTTPError

from authguard import AuthGuard
from typing import Union, Optional
from packages.db import FirestoreDb
from packages import file_utils, utility

APIKEY = getenv('FLASK_API_KEY')

g_logging = gcloudlogging.Client()
g_logging.setup_logging()

class Controller():
    def __init__(self) -> None:
        self.auth_guard = AuthGuard()
        self.apikey = APIKEY
        self.user_obj = None
        self.fs_db = FirestoreDb(getenv("DATABASE_COLLECTION_NAME"))
        self.config = None
        self.read_config()
        self.fs_db.size_map_dict = self.config['sizeMap']
        self.multi_entry_keyword_list = ['12', '16']

    def __get_firebase_user__(self, user_local_id: str) -> dict:
        return self.auth_guard.get_firebase_user_by_id(user_local_id)

    def __send_email_verification__(self, user_id_token:str) -> None:
        self.auth_guard.send_verification_email(user_id_token)

    def __validate_api_request__(self, req_apikey:str) -> bool:
        return True if req_apikey != None and req_apikey != "" and req_apikey == self.apikey else False

    def __set_filter_list__(self, d:dict) -> list:
        filter_list = []
        if "distributors" in d.keys():
            filter_list.append(("vendor", "in", [ x for x in d['distributors'].split(',') if x != ""]))
        elif "fromDate" in d.keys() or "toDate" in d.keys():
            from_date = d['fromDate']
            to_date = d['toDate']
            if from_date and to_date:
                filter_list.append(("dateTaken", ">=", datetime.strptime(from_date, "%Y-%m-%d")))
                filter_list.append(("dateTaken", "<=", datetime.strptime(to_date, "%Y-%m-%d")))
            elif from_date:
                filter_list.append(("dateTaken", "==", datetime.strptime(from_date, "%Y-%m-%d")))
            elif to_date:
                filter_list.append(("dateTaken", "==", datetime.strptime(to_date, "%Y-%m-%d")))
        return filter_list
    
    def is_valid_email(self, raw_email:str) -> bool:
        return utility.valid_email(raw_email)

    def sign_in_email_password(self, email: str, password: str) -> Union[bool, str | None]:
        try:
            logging.info(f"Login attempt using {email}")
            self.user_obj = self.auth_guard.firebase_sign_in_email_password(email, password)
            user_record = self.__get_firebase_user__(self.user_obj['localId'])
            if not user_record.email_verified:
                self.__send_email_verification__(self.user_obj['idToken'])
                return False, "Please verify your account via email and try again."
            return True, None
        except HTTPError as he:
            return False, str(he)
        except Exception as e:
            logging.error(f"Auth error - {str(e)}")
            raise Exception()

    def generate_session_cookie(self) -> bytes:
        if self.user_obj is None:
            raise Exception("No user object")
        return self.auth_guard.generate_session_cookie(self.user_obj['idToken'])

    def validate_user(self, session_cookie:str) -> bool:
        return self.auth_guard.validate_session_cookie(session_cookie)

    def reset_user_password(self, user_email) -> bool:
        user_obj = self.auth_guard.get_firebase_user_by_email(user_email)
        if user_obj:
            self.auth_guard.send_password_reset(user_email)
            return True
        return False

    def update_full_config(self, req_api_key:str, new_dict:dict) -> bool:
        logging.warning(f"Full config updated using api on {datetime.now()}")
        if self.__validate_api_request__(req_api_key):
            self.fs_db.update_config_doc(new_dict)
            return True

    def new_form_submit(self, req_json: dict) -> bool:
        if req_json is not None and len(req_json) > 0:
            try:
                valid_submission = self.fs_db.validate_submission_dict(req_json)
                if valid_submission != None and len(valid_submission) > 0:
                    self.fs_db.create_new_doc(valid_submission)
                else:
                    raise Exception("Validated submission is none or 0 length")
                doc_created = True
            except KeyError as ke:
                logging.error(f"Mandatory key missing - {ke}")
                doc_created = False
            except ValueError as ve:
                logging.error(f"Null value found - {ve}")
                doc_created = False
            except Exception as e:
                logging.error(f"Unknown error - {e}")
                print(print_exc())
                doc_created = False
        else:
            doc_created = False
        return doc_created

    def read_config(self, sort_config:Optional[bool] = False, debug:Optional[bool] = False) -> dict:
        if debug:
            with open('./configs/app_config.json', 'r') as f:
                self.config = json.load(f)
        else:
            self.config = self.fs_db.read_doc(getenv('CONFIG_DOC_ID'))
        if sort_config:
            self.config['sizeMap'] = utility.sort_subdict(self.config['sizeMap'], lambda x: x[-2:])
        return self.config

    def update_config(self, upd_dict:dict) -> bool:
        try:
            logging.info(f"Config updated with {upd_dict}")
            self.fs_db.update_config_doc(upd_dict)
            config_updated = True
            self.read_config(sort_config=True)
        except KeyError as ke:
            logging.error(f"New config error - {ke}")
            config_updated = False
        except Exception as e:
            logging.error(f"Uncaught config error - {e}")
            config_updated = False
        finally:
            return config_updated

    def get_report(self, req_json:dict) -> Union[bytes, str, None]:
        logging.info(f"Report requested using params {str(req_json)}")
        filter_list = self.__set_filter_list__(req_json)
        try:
            if len(filter_list) == 0:
                queried_docs_list = self.fs_db.read_doc_collection()
            else:
                queried_docs_list = self.fs_db.read_doc_collection(filter_list)

            if len(queried_docs_list) > 0:
                unique_beers_set = set()
                for doc in queried_docs_list:
                    doc['dateTaken'] = doc['dateTaken'].strftime("%m/%d/%Y") if not isinstance(doc['dateTaken'], str) else doc['dateTaken']
                    if isinstance(doc['beersTaken'], list):
                        doc['beersTaken'] = utility.list_to_dict(doc['beersTaken'])
                    doc['beersTaken'] = utility.convert_to_case_equivalent(self.config['sizeMap'], doc['beersTaken'])
                    for k in doc['beersTaken'].keys():
                        unique_beers_set.add(k)
                file_bytes:bytes = file_utils.dict_to_xlsx_bytes(queried_docs_list, unique_beers_set)
                return file_bytes
            else:
                return "No documents within date range"
        except Exception as e:
            raise e
