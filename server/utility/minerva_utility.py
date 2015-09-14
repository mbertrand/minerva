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

from girder.utility.model_importer import ModelImporter

from girder.plugins.minerva.constants import PluginSettings


def findNamedFolder(currentUser, user, parent, parentType, name, create=False):
    folders = [
        ModelImporter.model('folder').filter(folder, currentUser) for folder in
        ModelImporter.model('folder').childFolders(
            parent=parent, parentType=parentType, user=currentUser,
            filters={'name': name})]
    # folders should have len of 0 or 1, since we are looking in a
    # user folder for a folder with a certain name
    if len(folders) == 0:
        if create:
            return ModelImporter.model('folder').createFolder(
                parent, name, parentType=parentType, public=False)
        else:
            return None
    else:
        return folders[0]


def findMinervaFolder(currentUser, user, create=False):
    return findNamedFolder(currentUser, user, user, 'user',
                           PluginSettings.MINERVA_FOLDER, create)


def findDatasetFolder(currentUser, user, create=False):
    minervaFolder = findMinervaFolder(currentUser, user, create)
    if minervaFolder is None:
        return minervaFolder
    else:
        return findNamedFolder(currentUser, user, minervaFolder, 'folder',
                               PluginSettings.DATASET_FOLDER, create)


def findSourceFolder(currentUser, user, create=False):
    minervaFolder = findMinervaFolder(currentUser, user, create)
    if minervaFolder is None:
        return minervaFolder
    else:
        return findNamedFolder(currentUser, user, minervaFolder, 'folder',
                               PluginSettings.SOURCE_FOLDER, create)


def findSessionFolder(currentUser, user, create=False):
    minervaFolder = findMinervaFolder(currentUser, user, create)
    if minervaFolder is None:
        return minervaFolder
    else:
        return findNamedFolder(currentUser, user, minervaFolder, 'folder',
                               PluginSettings.SESSION_FOLDER, create)


def findNamedCollection(currentUser, name, create=False):
    collections = \
        [ModelImporter.model('collection').filter(c, currentUser) for c in
         ModelImporter.model('collection').textSearch(name, user=currentUser)]
    # collections should have len of 0 or 1, since we are looking
    # for a collection with a certain name
    if len(collections) == 0:
        if create:
            return ModelImporter.model('collection').createCollection(
                name, description='', public=True, creator=currentUser)
        else:
            return None
    else:
        return collections[0]


def findMinervaCollection(currentUser, create=False):
    return findNamedCollection(currentUser, PluginSettings.MINERVA_COLLECTION,
                               create)


def findAnalysisFolder(currentUser, create=False):
    minervaCollection = findMinervaCollection(currentUser,  create)
    if minervaCollection is None:
        return None
    else:
        analysisFolder = findNamedFolder(currentUser, currentUser,
                                         minervaCollection, 'collection',
                                         'analysis', create)
        return analysisFolder


def findAnalysisByName(currentUser, name):
    analysisFolder = findAnalysisFolder(currentUser)
    filters = {}
    filters['$text'] = {
        '$search': name
    }
    analyses = [ModelImporter.model('item').filter(item, currentUser)
                for item in
                ModelImporter.model('folder').childItems(folder=analysisFolder,
                                                         filters=filters)]
    if len(analyses) > 0:
        return analyses[0]
    else:
        return None


def updateMinervaMetadata(item, minerva_metadata):
    if 'meta' not in item:
        item['meta'] = {}
    item['meta']['minerva'] = minerva_metadata
    ModelImporter.model('item').setMetadata(item, item['meta'])
    return item['meta']['minerva']
