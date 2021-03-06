#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import os

# Need to set the environment variable before importing girder
os.environ['GIRDER_PORT'] = os.environ.get('GIRDER_TEST_PORT', '20200')  # noqa

from tests import base


def setUpModule():
    """
    Enable the minerva plugin and start the server.
    """
    base.enabledPlugins.append('jobs')
    base.enabledPlugins.append('romanesco')
    base.enabledPlugins.append('gravatar')
    base.enabledPlugins.append('minerva')
    base.startServer(False)


def tearDownModule():
    """
    Stop the server.
    """
    base.stopServer()


class WmsTestCase(base.TestCase):

    """
    Tests of the minerva source API endpoints.
    """

    def setUp(self):
        """
        Set up the test case with  a user
        """
        super(WmsTestCase, self).setUp()

        self._user = self.model('user').createUser(
            'minervauser', 'password', 'minerva', 'user',
            'minervauser@example.com')

    def testCreateWmsSource(self):
        """
        Test the minerva WMS source API endpoints.
        """

        path = '/minerva_source_wms'
        name = 'testWMS'
        username = ''
        password = ''
        baseURL = 'http://demo.boundlessgeo.com/geoserver/ows'
        params = {
            'name': name,
            'username': username,
            'password': password,
            'baseURL': baseURL
        }
        response = self.request(path=path, method='POST', params=params, user=self._user)
        self.assertStatusOk(response)
        wmsSource = response.json
        minerva_metadata = wmsSource['meta']['minerva']
        self.assertEquals(wmsSource['name'], name, 'incorrect wms source name')
        self.assertEquals(minerva_metadata['source_type'], 'wms', 'incorrect wms source type')
        self.assertEquals(minerva_metadata['wms_params']['base_url'], baseURL, 'incorrect wms source baseURL')

    def testCreateWmsDataset(self):
        """
        Test the minerva WMS dataset API endpoints.
        """

        # create the source

        path = '/minerva_source_wms'
        name = 'testWMS'
        typeName = 'geonode:global_temp'
        username = ''
        password = ''
        baseURL = 'http://demo.boundlessgeo.com/geoserver/ows'
        params = {
            'name': name,
            'username': username,
            'password': password,
            'baseURL': baseURL
        }
        response = self.request(path=path, method='POST', params=params, user=self._user)
        self.assertStatusOk(response)
        wmsSource = response.json

        # create the dataset

        path = '/minerva_dataset_wms'
        name = 'testWMSdataset'
        wmsParams = {}
        params = {
            'name': name,
            'wmsSourceId': wmsSource['_id'],
            'typeName': typeName,
            'wmsParams': wmsParams
        }
        response = self.request(path=path, method='POST', params=params, user=self._user)
        self.assertStatusOk(response)
        wmsDataset = response.json
        minerva_metadata = wmsDataset['meta']['minerva']
        self.assertEquals(wmsDataset['name'], name, 'incorrect wms dataset name')
        self.assertEquals(minerva_metadata['source_id'], wmsSource['_id'], 'incorrect wms source_id')
        self.assertEquals(minerva_metadata['dataset_type'], 'wms', 'incorrect wms dataset type')
        self.assertEquals(minerva_metadata['base_url'], wmsSource['meta']['minerva']['wms_params']['base_url'],'incorrect wms dataset baseURL')
        self.assertEquals(minerva_metadata['type_name'], typeName, 'incorrect wms dataset typeName')
        legend = 'PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48U2VydmljZUV4Y2VwdGlvblJlcG9ydCB2ZXJzaW9uPSIxLjMuMCIgeG1sbnM9Imh0dHA6Ly93d3cub3Blbmdpcy5uZXQvb2djIiB4bWxuczp4c2k9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1hLWluc3RhbmNlIiB4c2k6c2NoZW1hTG9jYXRpb249Imh0dHA6Ly93d3cub3Blbmdpcy5uZXQvb2djIGh0dHA6Ly9kZW1vLmJvdW5kbGVzc2dlby5jb206ODAvZ2Vvc2VydmVyL3NjaGVtYXMvd21zLzEuMy4wL2V4Y2VwdGlvbnNfMV8zXzAueHNkIj4gICA8U2VydmljZUV4Y2VwdGlvbj4KICAgICAgQ2FuJmFwb3M7dCBvYnRhaW4gdGhlIHNjaGVtYSBmb3IgdGhlIHJlcXVpcmVkIGxheWVyLgpnZW9ub2RlOmdsb2JhbF90ZW1wIGxheWVyIGRvZXMgbm90IGV4aXN0Lgo8L1NlcnZpY2VFeGNlcHRpb24+PC9TZXJ2aWNlRXhjZXB0aW9uUmVwb3J0Pg==\n'
        # TODO determine if legend is stable, if not, needs to be mocked
        self.assertEquals(minerva_metadata['legend'], legend, 'incorrect wms dataset legend')
