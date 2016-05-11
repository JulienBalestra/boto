#!/usr/bin/env python
import argparse
import os
import requests
import json
import time

from boto.s3.connection import S3Connection
from boto.s3.key import Key


class BucketUpload(object):
	def __init__(self, aws_id, aws_secret, bucket_name):
		self.aws_id = aws_id
		self.aws_secret = aws_secret
		self.bucket_name = bucket_name

	def check(self):
		if self.aws_id is None:
			raise AttributeError("missing AWS_ID")
		if self.aws_secret is None:
			raise AttributeError("missing AWS_SECRET")

	def upload(self, local_filename, remote_filename):
		print "\nUploading %s ..." % local_filename
		conn = S3Connection(self.aws_id, self.aws_secret)
		bucket = conn.get_bucket(self.bucket_name)
		new_key = Key(bucket)
		new_key.key = "%s" % remote_filename
		new_key.set_contents_from_filename(local_filename)
		bucket.set_acl("public-read", remote_filename)
		print "Upload done: http://{bucket_name}.s3-website-{bucket_location}.amazonaws.com/{discovery_file}\n".format(
			bucket_name=self.bucket_name,
			bucket_location=bucket.get_location(),
			discovery_file=remote_filename)


class NewDiscoveryKey(object):
	peers_port = 2380
	poller_steps = 2
	base_discovery_etcd = "https://discovery.etcd.io/new?size="
	discovery_file = "discovery_etcd.json"

	def __init__(self, pub_instance, size, poll_delay=0):
		self.size = size
		self.new_discovery_url = ""
		self.bucket_data = {}
		self.poll_delay = poll_delay
		self.registered = []
		self.publisher = pub_instance

	@staticmethod
	def write_discovery_object(bucket_data, local_filename):
		print "Discovery object: "
		print json.dumps(bucket_data, indent=4)

		with open(local_filename, 'w') as f:
			json.dump(bucket_data, f)

	def create_new_discovery_url(self):
		print "Request new etcd endpoint"
		req = requests.get("%s%d" % (self.base_discovery_etcd, self.size))
		self.new_discovery_url = req.content
		url_ts = "%d" % time.time()
		self.bucket_data = {
			"url": "%s" % self.new_discovery_url,
			"size": "%d" % self.size,
			"url_ts": url_ts,
			"url_registered": self.registered
		}
		self.write_discovery_object(self.bucket_data, self.discovery_file)
		self.publisher.upload(
			local_filename=self.discovery_file,
			remote_filename=self.discovery_file)

	def _poll_etcd(self):
		print "Polling %s during %ds..." % (self.new_discovery_url, self.poll_delay)
		start = time.time()
		until = start + self.poll_delay
		member_list = []
		while len(member_list) != self.size and time.time() < until:
			registered = requests.get("%s" % self.new_discovery_url)
			try:
				nodes = json.loads(registered.content)["node"]["nodes"]
				for n in nodes:
					value = n["value"]
					if value not in member_list:
						print "%ds:\t" % (time.time() - start), value.replace(
							":%d" % self.peers_port, "\t:%d" % self.peers_port)
						member_list.append(value)
			except KeyError:
				pass
			time.sleep(self.poller_steps)

		if len(member_list) == self.size:
			print "\nEtcd %d/%d after %ds" % (
				len(member_list), self.size, time.time() - start)
			self.bucket_data["url_registered"] = member_list
			self.write_discovery_object(self.bucket_data, self.discovery_file)
			return True
		else:
			print "Polling timeout"
			return False

	def update_registered(self):
		success = self._poll_etcd()
		if success:
			self.publisher.upload(
				local_filename=self.discovery_file,
				remote_filename=self.discovery_file)


class CloudConfig(object):
	cloud_config_file = "cloud-config.yaml"

	def __init__(self, pub_instance, config_path):
		self.publisher = pub_instance
		self.config_path = config_path

	def check(self):
		if os.path.isfile(self.config_path) is False:
			raise OSError("Path: %s is invalid\nCWD: %s\nFiles: %s" % (
				self.config_path, os.getcwd(), os.listdir(".")))

	def create_remote_config(self):
		self.publisher.upload(
			local_filename=self.config_path,
			remote_filename=self.cloud_config_file)


def fast_arg_parsing():
	args = argparse.ArgumentParser()
	args.add_argument("size", type=int, help="Etcd cluster size")
	args.add_argument("bucket_name", type=str, help="Amazon Web Services S3 bucket")
	args.add_argument("cloud_config", type=str, help="Cloud init path")
	args.add_argument("--poll", default=600, type=int, help="Polling delay to follow registers")

	argument_values = \
		args.parse_args().size, \
		args.parse_args().bucket_name, \
		args.parse_args().cloud_config, \
		args.parse_args().poll
	return argument_values


if __name__ == "__main__":
	# Fetch args
	av_size, av_bucket_name, av_cloud_config, av_poll_delay = fast_arg_parsing()
	env_aws_id = os.getenv("AWS_ID")
	env_aws_secret = os.getenv("AWS_SECRET")

	# AWS tool
	publisher = BucketUpload(env_aws_id, env_aws_secret, av_bucket_name)
	publisher.check()

	# CloudConfig
	config = CloudConfig(publisher, av_cloud_config)
	config.check()
	config.create_remote_config()

	# Etcd
	discovery = NewDiscoveryKey(publisher, av_size, av_poll_delay)
	discovery.create_new_discovery_url()
	discovery.update_registered()
