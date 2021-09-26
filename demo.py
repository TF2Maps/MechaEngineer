import vdf
import pymysql
import paramiko

import socket
import os
import stat
from datetime import datetime


# For some reason someone set chmod +x on all official maps in the server
TF_ROOT = "/home/tf/tf/"
OFFICIAL_MAPS = tuple([ map_name for map_name in os.listdir(os.path.join(TF_ROOT, 'maps')) if os.stat(os.path.join(TF_ROOT, f'maps/{map_name}')).st_mode == 33277 ])


def main():
    # For each file in "finished_demos"
    print("Searching for demos...")
    os.chdir(os.path.join(TF_ROOT, "demos_finished"))
    for demo_file in os.listdir():
        if not demo_file.endswith(".dem"):
            print(f"Skipping {demo_file}. Not a .dem file")
            return

        # Gather info about demo played
        print(f"Parsing {demo_file}...")
        server_id = socket.getfqdn()
        demo_info = demo_file.replace(".dem", "").split("-")
        map_name = demo_info[3]
        file_size = os.path.getsize(demo_file) #/ 1024 / 1024
        date_string = f"{demo_info[1]}-{demo_info[2]}"
        date = datetime.strptime(date_string, "%Y%m%d-%H%M" )

        # Check if official map
        print(f"Checking if map is official...")
        if map_name in OFFICIAL_MAPS:
            print(f"{demo_file} is an offical map. Deleting...")
            os.remove(demo_file)
            return

        # Upload to CDN
        print(f"Uploading {demo_file} to CDN")
        upload_demo(demo_file)

        print(f"Putting demo into CDN database...")
        insert_demo(map_name, os.path.basename(demo_file), file_size, date, server_id)

        # Delete local file
        print(f"Deleting {demo_file}")
        os.remove(demo_file)


def upload_demo(demo_file):
    remote_path = "/home/tf2maps/web/demos.tf2maps.net/public_html/files/"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
    ssh.connect('srvr.tf2maps.net', port=22, username='tf2maps', password='C7fox8LFvN0DqCuW')
    sftp = ssh.open_sftp()
    sftp.chdir(remote_path)

    sftp.put(demo_file, f"/home/tf2maps/web/demos.tf2maps.net/public_html/files/{demo_file}")
    ssh.close()


def insert_demo(map_name, file_name, file_size, date, server_name):
    db_config = os.path.join(TF_ROOT, "addons/sourcemod/configs/databases.cfg")

    server_ids = {
        "us.tf2maps.net": 1,
        "eu.tf2maps.net": 2
    }

    with open(db_config) as file:
        databases = vdf.load(file)

    database = databases['Databases']['xenforo']

    connection = pymysql.connect(
        host=database['host'],
        user=database['user'],
        port=int(database['port']),
        password=database['pass'],
        database="tf2maps_demos",
        cursorclass=pymysql.cursors.DictCursor
    )

    with connection.cursor() as cursor:
        query = (
            "INSERT INTO demos "
            "(map, file, filesize, recorded_on, server_id, downloads, datetime, bandwidth) "
            "VALUES "
            "(%s, %s, %s, %s, %s, 0, %s, 0)"
        )

        cursor.execute(query, (map_name, file_name, file_size, date,  server_ids[server_name], date))


main()