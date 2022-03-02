# Std Lib Imports
import re
import shutil
import bz2
import os.path
import hashlib

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
        response = await client.get(link)

        with open(destination, "wb") as file:
            file.write(response.content)

async def get_download_filename(link):
    async with httpx.AsyncClient() as client:
        response = await client.head(link)
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