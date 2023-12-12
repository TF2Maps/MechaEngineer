# Std Lib Imports
import re
import shutil
import bz2
import os.path
import hashlib
from urllib.parse import urlparse
import os
import requests

# 3rd Party Imports
import asyncssh
import httpx
import aioboto3

# Local Imports
pass


def compress_file(filepath):
    output_filepath = f"{filepath}.bz2"

    with open(filepath, 'rb') as input:
        with bz2.BZ2File(output_filepath, 'wb') as output:
            shutil.copyfileobj(input, output)

    return output_filepath

async def download_file(link, destination):
    async with httpx.AsyncClient() as client:
        response = await client.get(link, timeout=60)
        with open(destination, "wb") as file:
            file.write(response.content)

async def dropbox_download(link, destination):
    headers = {'user-agent': 'Wget/1.16 (linux-gnu)'}
    r = requests.get(link, stream=True, headers=headers)
    with open(destination, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)

async def get_download_filename(link):
    async with httpx.AsyncClient() as client:
        response = await client.head(link)
        #DROPBOX BULLSHIT
        if str(link).startswith('https://www.dropbox.com'):
            shortened_url = str(link)[:-5]
            url_path = urlparse(shortened_url)
            filename = os.path.basename(url_path.path)

            return filename
        #tf2maps :)
        else:
            content_header = response.headers.get("content-disposition")
        matches = re.search("filename=\"([\w.]+)\"", content_header)
        filename = matches.group(1)

        return filename


async def check_redirect_hash(file, s3_config):
    session = aioboto3.session.Session()
    async with session.client('s3', **s3_config) as s3:
        remote_hash = await s3.head_object(Bucket="tf2maps-maps", Key=f"maps/{os.path.basename(file)}")
        remote_hash = remote_hash.get('ETag', None).replace('"', '')
        local_hash = hashlib.md5(open(file, "rb").read()).hexdigest()

        return local_hash == remote_hash


async def upload_to_redirect(localfile, s3_config):
    session = aioboto3.session.Session()
    async with session.client('s3', **s3_config) as s3:
        with open(localfile, "rb") as file:
            obj = await s3.put_object(ACL="public-read", Body=file, Bucket="tf2maps-maps", Key=f"maps/{os.path.basename(localfile)}")


async def upload_to_gameserver(localfile, hostname, username, password, port, path, force=False):
    async with asyncssh.connect(hostname, username=username, password=password, known_hosts=None) as conn:
        async with conn.start_sftp_client() as sftp:
            file_exists = await sftp.exists(os.path.join(path, os.path.basename(localfile)))

            if not file_exists or force:
                await sftp.put(localfile, path)


async def redirect_file_exists(filename, s3_config):
    session = aioboto3.session.Session()    
    async with session.client('s3', **s3_config) as s3:
        obj = await s3.list_objects(Bucket="tf2maps-maps", Prefix=f"maps/{os.path.basename(filename)}", MaxKeys=2)
        return bool(obj.get('Contents', []))



async def remote_file_exists(filename, hostname, username, password, port, path):
    async with asyncssh.connect(hostname, username=username, password=password, known_hosts=None) as conn:
        async with conn.start_sftp_client() as sftp:
            exists = await sftp.exists(os.path.join(path, os.path.basename(filename)))
            return exists

async def remote_file_size(filename, hostname, username, password, port, path):
    async with asyncssh.connect(hostname, username=username, password=password, known_hosts=None) as conn:
        async with conn.start_sftp_client() as sftp:
            try:
                stat = await sftp.stat(os.path.join(path, os.path.basename(filename)))
                byte = int(stat.size)
                mb = byte/1048576
                return mb
            except:
                return 0
            