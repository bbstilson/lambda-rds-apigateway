#!/usr/bin/env python

import os
import json
import logging
import traceback
import psycopg2

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_USERNAME = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

logger=logging.getLogger()
logger.setLevel(logging.INFO)

query='SELECT * FROM pdf_hashes WHERE hash = %s'

def make_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    conn.autocommit=True
    return conn 

def log_err(errmsg):
    logger.error(errmsg)
    return {
        'message': errmsg,
        'headers': {},
        'statusCode': 400,
        'isBase64Encoded':'false'
    }

logger.info('Cold start complete.')

def lambda_handler(event, context):
    logger.info(event)

    try:
        cnx = make_connection()
        cursor = cnx.cursor()

        try:
            cursor.execute(query, (event['pathParameters']['pdf_hash'],))
        except:
            err = f'ERROR: Cannot execute cursor.\n{traceback.format_exc()}'
            return log_err(err)
        try:
            row = cursor.fetchone()
            result = True if row else False
            cursor.close()
        except:
            err = f'ERROR: Cannot retrieve query data.\n{traceback.format_exc()}'
            return log_err(err)

        return {
            'body': json.dumps({ 'valid': result }),
            'headers': {},
            'statusCode': 200,
            'isBase64Encoded':'false'
        }
    except:
        err = f'ERROR: Cannot connect to database from handler.\n{traceback.format_exc()}'
        return log_err(err)
    finally:
        try:
            cnx.close()
        except:
            pass
