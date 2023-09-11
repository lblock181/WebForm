from os import getenv
from base64 import b64decode
from re import match
from typing import Callable, Union


def valid_email(raw_email:str) -> bool:
    return bool(match(
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        string=raw_email
    ))

def duplicate_dict_keys_in_list(target_dict:dict, sub_dict_keyword:str) -> Union[bool, set]:
    key_set = set()
    ret_val = None
    for sub_dict in target_dict[sub_dict_keyword]:
        for key in sub_dict.keys():
            if key not in key_set:
                key_set.add(key)
            else:
                ret_val = True
    if ret_val == None:
        ret_val = False
    return ret_val, key_set

def beers_taken_list_to_dict(source_list:list, key_set:set, case_equiv_map:dict) -> dict:
    upd_dict = { k:None for k in key_set }
    for x in source_list:
        for k,v in x.items():
            v['quantity'] = round(int(v['quantity']) / case_equiv_map[v['size']]['caseEquiv'], 2)
            v['size'] = f"case{k.split('-')[1]}"
            if upd_dict[k] == None:
                upd_dict[k] = v
            else:
                upd_dict[k]['quantity'] = upd_dict[k]['quantity'] + v['quantity']
    for v in upd_dict.values():
        v['quantity'] = str(v['quantity'])
    return upd_dict

def convert_to_case_equivalent(case_equiv_map:dict, data:dict) -> dict:
    for beer_name, vals in data.items():
        if "." not in vals['quantity']:
            vals['quantity'] = int(vals['quantity'])
        else:
            vals['quantity'] = float(vals['quantity'])
        data[beer_name]['caseEquivalent'] = round(vals['quantity'] / case_equiv_map[vals['size']]['caseEquiv'], 2)
    return data

def list_to_dict(source_list:list) -> dict:
    temp_dict = dict()
    for x in source_list:
        temp_dict.update(x)
    return temp_dict

def get_firebase_config() -> dict:
    return {
        "apiKey": getenv("apiKey"),
        "authDomain": getenv("authDomain"),
        "databaseURL": getenv("databaseURL"),
        "projectId": getenv("projectId"),
        "storageBucket": getenv("storageBucket"),
        "messagingSenderId": getenv("messagingSenderId"),
        "appId": getenv("appId")
    }

def get_db_cert() -> dict:
    return {
        "type": getenv("type"),
        "project_id": getenv("project_id"),
        "private_key_id": getenv("private_key_id"),
        "private_key": decode_b64(getenv("private_key")),
        "client_email": getenv("client_email"),
        "client_id": getenv("client_id"),
        "auth_uri": getenv("auth_uri"),
        "token_uri": getenv("token_uri"),
        "auth_provider_x509_cert_url": getenv("auth_provider_x509_cert_url"),
        "client_x509_cert_url": getenv("client_x509_cert_url"),
        "universe_domain": getenv("universe_domain")
    }

def decode_b64(encoded_val:str) -> str:
    return b64decode(encoded_val)

def sort_subdict(dict_to_sort:dict, sort_fn:Callable) -> dict:
    return { x: dict_to_sort[x] for x in sorted(dict_to_sort, key=sort_fn) }