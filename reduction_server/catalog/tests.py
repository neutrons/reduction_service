from django.test import TestCase
from django.test import RequestFactory
from django.test.runner import DiscoverRunner
from django.contrib.messages.storage.fallback import FallbackStorage

from .icat import ICat


"""
To run the test:

python manage.py test reduction_server/catalog/ --testrunner=reduction_server.catalog.tests.NoDbTestRunner
python manage.py test reduction_server/catalog/ --testrunner=reduction_server.catalog.tests.NoDbTestRunner --settings=config.settings.local


"""


class NoDbTestRunner(DiscoverRunner):
    """
    A test runner to test without database creation/deletion
    """
    def setup_databases(self, **kwargs):
        pass
    def teardown_databases(self, old_config, **kwargs):
        pass

class IcatTestCase(TestCase):
    def setUp(self):
        request_factory = RequestFactory()
        request = request_factory.get('/users/login')
        # Workaround for messages to work!
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        self.icat = ICat(request)

    def test_get_instruments(self):
        instruments = self.icat.get_instruments()        
        self.assertEqual(instruments, {u'instrument': [u'ARCS', u'BSS', u'CNCS', u'CORELLI', u'EQSANS', u'FNPB', u'HYS', u'HYSA', u'MANDI', u'NOM', u'NSE', u'PG3', u'REF_L', u'REF_M', u'SEQ', u'SNAP', u'TOPAZ', u'USANS', u'VIS', u'VULCAN']})

    def test_get_experiments(self):
        instruments = self.icat.get_experiments("MANDI")        
        self.assertEqual(instruments, {u'proposal': [u'2012_2_11b_SCI', u'2013_2_11B_SCI', u'2014_1_11B_SCI', u'IPTS-10136', u'IPTS-10138', u'IPTS-10663', u'IPTS-10943', u'IPTS-11063', u'IPTS-11091', u'IPTS-11215', u'IPTS-11464', u'IPTS-11482', u'IPTS-11543', u'IPTS-11817', u'IPTS-11862', u'IPTS-11932', u'IPTS-11940', u'IPTS-12152', u'IPTS-12402', u'IPTS-12438', u'IPTS-12697', u'IPTS-12864', u'IPTS-12874', u'IPTS-12924', u'IPTS-13243', u'IPTS-13288', u'IPTS-13552', u'IPTS-13643', u'IPTS-13653', u'IPTS-13722', u'IPTS-13904', u'IPTS-14069', u'IPTS-14562', u'IPTS-14586', u'IPTS-15880', u'IPTS-8776']})
        
        instruments = self.icat.get_experiments("M")
        self.assertEqual(instruments,None)