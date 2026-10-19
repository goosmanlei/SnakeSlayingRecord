#!/usr/bin/env python3
"""Create/read back this project's private OSS and separate scoped runtime users.

Run locally with --system and --credentials-directory outside Git. The existing
Aliyun account profile is used only here; it is never exported to a runtime.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def ram(action, **parameters):
    command = ['aliyun', 'ram', action]
    for key, value in parameters.items():
        command += ['--' + key, json.dumps(value) if isinstance(value, dict) else str(value)]
    response = subprocess.run(command, capture_output=True)
    if response.returncode:
        # CLI errors can contain request inputs. Do not print credentials or
        # the unfiltered command; a read-only query can diagnose the operation.
        raise RuntimeError('RAM operation failed: ' + action)
    return json.loads(response.stdout)


def provision(root, directory):
    import alibabacloud_oss_v2 as oss
    from review_desk import resources as r
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)
    config = r.settings(root)
    connection = r.client(config, administrative=True)
    try:
        connection.get_bucket_info(oss.GetBucketInfoRequest(bucket=config['bucket']))
    except Exception as error:
        if r.service_status(error) not in (404, 403):
            raise RuntimeError('cannot establish bucket ownership') from None
        if r.service_status(error) == 403:
            config['bucket'] += '-' + hashlib.sha256(config['instance_id'].encode()).hexdigest()[:8]
        connection.put_bucket(oss.PutBucketRequest(bucket=config['bucket'], acl='private',
            create_bucket_configuration=oss.CreateBucketConfiguration(storage_class='Standard', data_redundancy_type='LRS')))
    connection.put_bucket_acl(oss.PutBucketAclRequest(bucket=config['bucket'], acl='private'))
    connection.put_bucket_public_access_block(oss.PutBucketPublicAccessBlockRequest(bucket=config['bucket'],
        public_access_block_configuration=oss.PublicAccessBlockConfiguration(block_public_access=True)))
    connection.put_bucket_versioning(oss.PutBucketVersioningRequest(bucket=config['bucket'],
        versioning_configuration=oss.VersioningConfiguration(status='Enabled')))
    origins = config['allowed_origins']
    connection.put_bucket_cors(oss.PutBucketCorsRequest(bucket=config['bucket'], cors_configuration=oss.CORSConfiguration(
        response_vary=True, cors_rules=[oss.CORSRule(allowed_origins=origins, allowed_methods=['GET', 'HEAD'],
        allowed_headers=['Range', 'If-Range', 'If-None-Match', 'If-Modified-Since'],
        expose_headers=['ETag', 'Content-Length', 'Content-Range', 'Accept-Ranges', 'Content-Disposition'], max_age_seconds=300)])))
    acl = connection.get_bucket_acl(oss.GetBucketAclRequest(bucket=config['bucket']))
    versioning = connection.get_bucket_versioning(oss.GetBucketVersioningRequest(bucket=config['bucket']))
    block = connection.get_bucket_public_access_block(oss.GetBucketPublicAccessBlockRequest(bucket=config['bucket']))
    if (acl.acl != 'private' or versioning.version_status != 'Enabled'
            or not block.public_access_block_configuration.block_public_access):
        raise RuntimeError('private/versioned bucket readback failed')
    r.atomic_json(root/'config/resource-storage.json', config)
    users = {u['UserName'] for u in ram('ListUsers')['Users']['User']}
    policies = {p['PolicyName'] for p in ram('ListPolicies', PolicyType='Custom')['Policies']['Policy']}
    created = []
    for instance in ('local', 'vps'):
        user = config['project'] + '-review-' + instance
        policy = config['project'] + '-resources-' + instance
        prefix = 'acs:oss:*:*:' + config['bucket'] + '/' + config['project'] + '/'
        document = {'Version': '1', 'Statement': [
            {'Effect': 'Allow', 'Action': ['oss:GetObject', 'oss:GetObjectVersion'], 'Resource': [prefix + '*']},
            {'Effect': 'Allow', 'Action': ['oss:PutObject', 'oss:ListParts', 'oss:AbortMultipartUpload'], 'Resource': [prefix + 'originals/*', prefix + 'derivatives/*',
                prefix + 'snapshots/' + instance + '/*', prefix + 'tests/' + instance + '/*']} ]}
        if user not in users:
            ram('CreateUser', UserName=user, Comments='Private project review runtime; no account permissions')
        if policy not in policies:
            ram('CreatePolicy', PolicyName=policy, PolicyDocument=document)
        else:
            found = ram('GetPolicy', PolicyType='Custom', PolicyName=policy)
            actual = ram('GetPolicyVersion', PolicyType='Custom', PolicyName=policy, VersionId=found['DefaultPolicyVersion']['VersionId'])
            if json.loads(actual['PolicyVersion']['PolicyDocument']) != document:
                raise RuntimeError('existing runtime policy differs; inspect before changing it')
        ram('AttachPolicyToUser', PolicyType='Custom', PolicyName=policy, UserName=user)
        filename = directory / (instance + '.json')
        if not filename.exists():
            keys = ram('ListAccessKeys', UserName=user)['AccessKeys']['AccessKey']
            if keys:
                raise RuntimeError('runtime key already exists but local secret is absent; do not create another blindly')
            # Capture the one-time secret privately. Never send it to stdout.
            key = ram('CreateAccessKey', UserName=user)['AccessKey']
            fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'w') as output:
                json.dump({'project': config['project'], 'instance': instance,
                    'access_key_id': key['AccessKeyId'], 'access_key_secret': key['AccessKeySecret']}, output)
                output.flush(); os.fsync(output.fileno())
        created.append({'user': user, 'policy': policy, 'credentials': str(filename), 'mode': oct(filename.stat().st_mode & 0o777)})
    receipt = {'bucket': config['bucket'], 'region': config['region'], 'acl': 'private', 'versioning': 'Enabled',
        'block_public_access': True, 'cors_origins': origins, 'runtime_users': created}
    r.atomic_json(directory/'provision-receipt.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument('--system', type=Path, required=True)
    p.add_argument('--credentials-directory', type=Path, required=True)
    args = p.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    provision(args.root.resolve(), args.credentials_directory.resolve())
