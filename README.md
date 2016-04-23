# CoreOS Publisher

Publish fresh etcd content get from https://discovery.etcd.io

## How

Run the python file `./s3_publisher.py` with the following requirements:

Environment:
* AWS_ID=ID
* AWS_SECRET=SECRET


Arguments values:
* int size
* str bucket_name

Or use the docker container:


    docker run --rm julienbalestra/coreos_publisher -h
    
    docker run --rm \
        -e AWS_ID=ID \
        -e AWS_SECRET=SECRET \
         julienbalestra/coreos_publisher 3 bucket_name
    
    docker run --rm \
        -e AWS_ID=ID \
        -e AWS_SECRET=SECRET \
         julienbalestra/coreos_publisher 3 bucket_name
         
Will produce:

    {
        "url": "https://discovery.etcd.io/75859661e9178cea34d27d47fcc91587", 
        "url_registered": [], 
        "url_ts": "1461431876", 
        "size": "3"
    }

This content is uploaded to your S3 bucket.

    Uploading discovery_etcd.json
    Upload done: http://coreos-deploy.s3-website-eu-west-1.amazonaws.com/discovery_etcd.json


Depending on the --poll delay (default at 600s), this will notify you until delay expired:

    Polling https://discovery.etcd.io/75859661e9178cea34d27d47fcc91587 during 600s...
    56s:	ec027cb438df449d806868a68f8fa29f=http://192.168.1.4		:2380
    59s:	bc2e9b4258b1486ebe8c7199d6376f6a=http://192.168.1.37	:2380
    125s:	eb355be3db93403e8c4a3f4cb8fa38cd=http://192.168.1.32	:2380
    
    Etcd 3/3 after 127s
    Discovery object: 
    {
        "url": "https://discovery.etcd.io/75859661e9178cea34d27d47fcc91587", 
        "url_registered": [
            "ec027cb438df449d806868a68f8fa29f=http://192.168.1.4:2380", 
            "bc2e9b4258b1486ebe8c7199d6376f6a=http://192.168.1.37:2380", 
            "eb355be3db93403e8c4a3f4cb8fa38cd=http://192.168.1.32:2380"
        ], 
        "url_ts": "1461431876", 
        "size": "3"
    }

Again, content is uploaded to your S3 bucket, replacing the **url_registered** value.

    Uploading discovery_etcd.json
    Upload done: http://coreos-deploy.s3-website-eu-west-1.amazonaws.com/discovery_etcd.json