import argparse
import os
import requests
import json
import time

from boto.s3.connection import S3Connection
from boto.s3.key import Key


class CoreOSPublisher(object):
	base_discovery_etcd = "https://discovery.etcd.io/new?size="
	discovery_url_file = "discovery_etcd.json"

	def __init__(self, size, aws_id, aws_secret, bucket_name):
		self.size = size
		self.new_discovery_url = ""
		self.aws_id = aws_id
		self.aws_secret = aws_secret
		self.bucket_name = bucket_name

	def get_new_discovery_url(self):
		self.new_discovery_url = requests.get("%s%d" % (self.base_discovery_etcd, self.size))
		content = {
			"url": self.new_discovery_url,
			"size": self.size,
			"url_ts": time.time()
		}
		with open(self.discovery_url_file, 'w') as f:
			json.dump(content, f)

	def upload(self):
		conn = S3Connection(self.aws_id, self.aws_secret)
		bucket = conn.get_bucket(self.bucket_name)
		new_key = Key(bucket)
		new_key.key = "%s" % self.discovery_url_file
		new_key.set_contents_from_filename(self.discovery_url_file)
		bucket.set_acl("public-read", self.discovery_url_file)

	def check(self):
		if self.aws_id is None:
			raise AttributeError("missing AWS_ID")
		if self.aws_secret is None:
			raise AttributeError("missing AWS_SECRET")


def fast_arg_parsing():
	args = argparse.ArgumentParser()
	args.add_argument("size", type=str, help="Etcd cluster size")
	args.add_argument("bucket_name", type=str, help="Amazon Web Services S3 bucket")
	return args.parse_args().size, args.parse_args().bucket_name


if __name__ == "__main__":
	# Fetch args
	size, bucket_name = fast_arg_parsing()
	aws_id = os.getenv("AWS_ID")
	aws_secret = os.getenv("AWS_SECRET")

	publisher = CoreOSPublisher(size, aws_id, aws_secret, bucket_name)
	publisher.check()
	publisher.get_new_discovery_url()
	publisher.upload()
