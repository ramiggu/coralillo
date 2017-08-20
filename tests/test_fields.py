from norm import create_engine, Model
from norm.fields import *
from norm.hashing import check_password
from datetime import datetime
import unittest
import time
import os

nrm = create_engine()

os.environ['TZ'] = 'UTC'
time.tzset()


class User(Model):
    password = Hash()


class FieldTestCase(unittest.TestCase):

    def setUp(self):
        nrm.lua.drop(args=['*'])
        self.pwd = 'bcrypt$$2b$12$gWQweaiLPJr2OHSPOshyQe3zmnSAPGv2pA.PwOIuxZ3ylvLMN7h6C'

    def test_field_text(self):
        field = Text(name='field', default='pollo')

        self.assertEqual(field.recover({'field': 'foo'}, 'field'), 'foo')
        self.assertEqual(field.prepare('foo'), 'foo')
        self.assertEqual(field.validate(None, 'field'), 'pollo')
        self.assertEqual(field.recover({'field': ''}, 'field'), '')
        self.assertEqual(field.recover({'field': None}, 'field'), None)

    def test_field_text_validate(self):
        field = Text()

        with self.assertRaises(MissingFieldError):
            field.validate('', 'field')

    def test_field_hash(self):
        field = Hash(name='field')

        self.assertEqual(field.recover({'field': 'foo'}, 'field'), 'foo')
        self.assertNotEqual(field.validate('foo', 'field'), 'foo')
        self.assertEqual(field.recover({'field': None}, 'field'), None)

    def test_field_bool(self):
        field = Bool(name='field')

        self.assertEqual(field.recover({'field': 'True'}, 'field'), True)
        self.assertEqual(field.recover({'field': 'False'}, 'field'), False)
        self.assertEqual(field.prepare(True), 'True')
        self.assertEqual(field.prepare(False), 'False')
        self.assertEqual(field.recover({'field': None}, 'field'), None)

        self.assertEqual(field.validate('true', 'field'), True)
        self.assertEqual(field.validate('false', 'field'), False)
        self.assertEqual(field.validate('1', 'field'), True)
        self.assertEqual(field.validate('0', 'field'), False)
        self.assertEqual(field.validate('', 'field'), False)

    def test_field_int(self):
        field = Integer(name='field')

        self.assertEqual(field.recover({'field': '35'}, 'field'), 35)
        self.assertEqual(field.recover({'field': '0'}, 'field'), 0)
        self.assertEqual(field.recover({'field': ''}, 'field'), None)
        self.assertEqual(field.recover({'field': None}, 'field'), None)

        self.assertEqual(field.prepare(35), '35')
        self.assertEqual(field.prepare(0), '0')

        self.assertEqual(field.validate(0, 'field'), 0)
        self.assertEqual(field.validate('0', 'field'), 0)

        with self.assertRaises(MissingFieldError):
            field.validate('', 'field')

        with self.assertRaises(InvalidFieldError):
            field.validate('pollo', 'field')

    def test_field_float(self):
        field = Float(name='field')

        self.assertEqual(field.recover({'field': '3.14'}, 'field'), 3.14)
        self.assertEqual(field.recover({'field': '0'}, 'field'), 0.0)
        self.assertEqual(field.recover({'field': ''}, 'field'), None)
        self.assertEqual(field.recover({'field': None}, 'field'), None)

        self.assertEqual(field.prepare(3.14), '3.14')
        self.assertEqual(field.prepare(0.0), '0.0')

        self.assertEqual(field.validate(0, 'field'), 0)
        self.assertEqual(field.validate('0', 'field'), 0)

    def test_field_date(self):
        field = Datetime(name='field')

        self.assertEqual(field.recover({'field': '1499794899'}, 'field'), datetime(2017, 7, 11, 17, 41, 39))
        self.assertEqual(field.recover({'field': ''}, 'field'), None)
        self.assertEqual(field.recover({'field': None}, 'field'), None)
        self.assertEqual(field.prepare(datetime(2017, 7, 11, 17, 41, 39)), '1499794899')

    def test_field_location(self):
        class MyModel(Model):
            field = Location()

        obj = MyModel(field = datamodel.Location(-103.3590, 20.7240)).save(nrm.redis)

        self.assertEqual(nrm.redis.type('mymodel:geo_field'), b'zset')
        self.assertEqual(MyModel.get(obj.id, nrm.redis).field, datamodel.Location(-103.3590, 20.7240))

    def test_password_check(self):
        user = User(
            password  = self.pwd,
        ).save(nrm.redis)

        self.assertTrue(check_password('123456', user.password))
        self.assertFalse(user.password == '123456')

    def test_empty_field_dict(self):
        class Dummy(Model):
            dynamic = Dict()

        a = Dummy().save(nrm.redis)
        loaded_a = Dummy.get(a.id, nrm.redis)

        self.assertDictEqual(loaded_a.dynamic, {})

    def test_field_dict(self):
        class Dummy(Model):
            name           = Text()
            dynamic        = Dict()

        # Create and save models with a dict field
        a = Dummy(
            name = 'dummy',
            dynamic = {
                '1': 'one',
            },
        ).save(nrm.redis)

        b = Dummy(
            name = 'dummy',
            dynamic = {
                '2': 'two',
            },
        ).save(nrm.redis)

        c = Dummy(
            name = 'dummy',
            dynamic = {
                '1': 'one',
                '2': 'two',
            },
        ).save(nrm.redis)

        # override dict
        a.dynamic = {
            '3': 'thre',
        }

        a.save(nrm.redis)

        loaded_a = Dummy.get(a.id, nrm.redis)
        loaded_b = Dummy.get(b.id, nrm.redis)
        loaded_c = Dummy.get(c.id, nrm.redis)

        self.assertDictEqual(a.dynamic, loaded_a.dynamic)
        self.assertDictEqual(b.dynamic, loaded_b.dynamic)
        self.assertDictEqual(c.dynamic, loaded_c.dynamic)


if __name__ == '__main__':
    unittest.main()
