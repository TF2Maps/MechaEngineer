import boto3


def create_server(server_type, requester_name, request_id, password, ttl, discord_channel_id, discord_message_id, region):
    session = boto3.session.Session(region_name=region)
    ec2 = session.client('ec2')

    location = region_to_location(region)

    tags = {
        "Name": f"{server_type}-{request_id}",
        "server_password": password,
        "spectate_password": password,
        "ttl": str(ttl),
        "requested_by": requester_name,
        "discord_channel_id": discord_channel_id,
        "discord_message_id": discord_message_id,
        "request_id": request_id,
        "location": location
    }

    response = ec2.run_instances(
        LaunchTemplate={
            'LaunchTemplateName': server_type,
            'Version': get_lastest_launchtemplate_version(server_type, region=region)
        },
        MaxCount=1,
        MinCount=1,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {"Key": key, "Value": str(value)}
                    for key, value in tags.items()
                ]
            }
        ]
    )
    raise_for_status(response)

    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[response['Instances'][0]['InstanceId']])

    return response['Instances'][0]


def get_lastest_launchtemplate_version(name, region="us-east-2"):
    session = boto3.session.Session(region_name=region)
    ec2 = session.client('ec2')
    response = ec2.describe_launch_templates(LaunchTemplateNames=[name])
    raise_for_status(response)
    launch_template_version = str(response["LaunchTemplates"][0]["LatestVersionNumber"])

    return launch_template_version


def get_instance_ip(instance_id, region="us-east-2"):
    session = boto3.session.Session(region_name=region)
    ec2 = session.client('ec2')
    response = ec2.describe_instances(InstanceIds=[instance_id])
    raise_for_status(response)

    return response['Reservations'][0]['Instances'][0]['PublicIpAddress']


def region_to_location(region):
    locations = {
        "us-east-1": "US East - Virginia",
        "us-east-2": "US Central - Ohio",
        "us-west-1": "US West - California",
        "us-west-2": "US West - Oregon",
        "eu-central-1": "EU Central - Frankfurt"
    }
    return locations[region]


def list_servers():
    servers = []
    regions = {
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2",
        "eu-central-1",
    }
    for region in regions:
        session = boto3.session.Session(region_name=region)
        ec2 = session.resource('ec2')

        instances = ec2.instances.all()
        servers.extend(instances)

    return servers


def raise_for_status(boto_response):
    status_code = boto_response['ResponseMetadata']['HTTPStatusCode']
    request_id = boto_response['ResponseMetadata']['RequestId']

    if status_code != 200:
        raise Exception(f"AWS response failed with HTTP {status_code}! RequestId: {request_id}")


def ec2_tags_to_dict(tags):
    return {t["Key"]: t["Value"] for t in tags}


def dict_to_ec2_tags(tag_dict):
    return [{"Key": k, "Value": v} for k, v in tag_dict.items()]