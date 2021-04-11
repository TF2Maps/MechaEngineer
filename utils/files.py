# Std Lib Imports
import re
import shutil
import bz2
import os.path

# 3rd Party Imports
import asyncssh
import httpx

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


async def upload_file(localfile, hostname, username, password, port, path, force=False):
    async with asyncssh.connect(hostname, username=username, password=password, known_hosts=None) as conn:
        async with conn.start_sftp_client() as sftp:
            file_exists = await sftp.exists(os.path.join(path, os.path.basename(localfile)))

            if not file_exists or force:
                await sftp.put(localfile, path)