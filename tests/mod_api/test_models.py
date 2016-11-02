import boto3
from urlparse import urlparse
from moto import mock_s3
import unittest
import json
from app import create_app
from app.database import db
from app.mod_api.models import MetaDataS3, MetaDataDB, User


class MetadataS3TestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()

    @staticmethod
    def test_metadata_s3_key():
        metadata = MetaDataS3(publisher="pub_test", package="test_package")
        expected = "{t}/pub_test/test_package/_v/latest/datapackage.json".format(t=metadata.prefix)
        assert expected == metadata.build_s3_key('datapackage.json')

    @staticmethod
    def test_metadata_s3_prefix():
        metadata = MetaDataS3(publisher="pub_test", package="test_package")
        expected = "{t}/pub_test".format(t=metadata.prefix)
        assert expected == metadata.build_s3_prefix()

    @mock_s3
    def test_save(self):
        with self.app.app_context():
            s3 = boto3.client('s3')
            bucket_name = self.app.config['S3_BUCKET_NAME']
            s3.create_bucket(Bucket=bucket_name)
            metadata = MetaDataS3(publisher="pub_test", package="test_package", body='hi')
            key = metadata.build_s3_key('datapackage.json')
            metadata.save()
            obs_list = list(s3.list_objects(Bucket=bucket_name, Prefix=key).get('Contents'))
            assert 1 == len(obs_list)
            assert key == obs_list[0]['Key']

    @mock_s3
    def test_get_metadata_body(self):
        with self.app.app_context():
            s3 = boto3.client('s3')
            bucket_name = self.app.config['S3_BUCKET_NAME']
            s3.create_bucket(Bucket=bucket_name)
            metadata = MetaDataS3(publisher="pub_test", package="test_package", body='hi')
            s3.put_object(
                Bucket=bucket_name,
                Key=metadata.build_s3_key('datapackage.json'),
                Body=metadata.body)
            assert metadata.body == metadata.get_metadata_body()

    @mock_s3
    def test_get_all_metadata_name_for_publisher(self):
        with self.app.app_context():
            s3 = boto3.client('s3')
            bucket_name = self.app.config['S3_BUCKET_NAME']
            s3.create_bucket(Bucket=bucket_name)
            metadata = MetaDataS3(publisher="pub_test", package="test_package", body='hi')
            s3.put_object(
                Bucket=bucket_name,
                Key=metadata.build_s3_key('datapackage.json'),
                Body=metadata.body)
            assert 1 == len(metadata.get_all_metadata_name_for_publisher())

    @mock_s3
    def test_get_empty_metadata_name_for_publisher(self):
        with self.app.app_context():
            s3 = boto3.client('s3')
            bucket_name = self.app.config['S3_BUCKET_NAME']
            s3.create_bucket(Bucket=bucket_name)
            metadata = MetaDataS3(publisher="pub_test", package="test_package", body='hi')
            s3.put_object(Bucket=bucket_name, Key='test/key.json', Body=metadata.body)
            assert 0 == len(metadata.get_all_metadata_name_for_publisher())

    @mock_s3
    def test_generate_pre_signed_put_obj_url(self):
        with self.app.app_context():
            s3 = boto3.client('s3')
            bucket_name = self.app.config['S3_BUCKET_NAME']
            s3.create_bucket(Bucket=bucket_name)
            metadata = MetaDataS3(publisher="pub_test", package="test_package", body='hi')
            url = metadata.generate_pre_signed_put_obj_url('datapackage.json')
            parsed = urlparse(url)
            print parsed
            print parsed.netloc
            print 's3-{region}.amazonaws.com'.format(region=self.app.config['AWS_REGION'])
            assert parsed.netloc == 's3-{region}.amazonaws.com'.format(region=self.app.config['AWS_REGION'])


class MetaDataDBTestCase(unittest.TestCase):

    def setUp(self):
        self.publisher_one = 'test_publisher1'
        self.publisher_two = 'test_publisher2'
        self.package_one = 'test_package1'
        self.package_two = 'test_package2'
        self.app = create_app()
        self.app.app_context().push()

        with self.app.test_request_context():
            db.drop_all()
            db.create_all()
            metadata1 = MetaDataDB(self.package_one, self.publisher_one)
            metadata1.descriptor = json.dumps(dict(name='test_one'))
            db.session.add(metadata1)

            metadata2 = MetaDataDB(self.package_two, self.publisher_one)
            metadata2.descriptor = json.dumps(dict(name='test_two'))
            db.session.add(metadata2)

            metadata3 = MetaDataDB(self.package_one, self.publisher_two)
            metadata3.descriptor = json.dumps(dict(name='test_three'))
            db.session.add(metadata3)

            metadata4 = MetaDataDB(self.package_two, self.publisher_two)
            metadata4.descriptor = json.dumps(dict(name='test_four'))
            db.session.add(metadata4)

            db.session.commit()

    def test_composite_key(self):
        # from app.mod_api.models import MetaDataDB
        res = MetaDataDB.query.filter_by(publisher=self.publisher_one).all()
        self.assertEqual(2, len(res))

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


class UserTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.app_context().push()
        with self.app.test_request_context():
            db.drop_all()
            db.create_all()
            user = User()
            user.user_id = 'test_user_id'
            db.session.add(user)
            db.session.commit()

    def test_serialize(self):
        user = User.query.filter_by(user_id='test_user_id').one().serialize
        self.assertEqual('test_user_id', user['user_id'])

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
