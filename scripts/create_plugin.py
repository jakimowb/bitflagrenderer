# -*- coding: utf-8 -*-

"""
***************************************************************************
    create_plugin.py
    Script to build the Bit Flag Renderer Plugin from Repository code
    ---------------------
    Date                 : August 2020
    Copyright            : (C) 2020 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.
                 *
*                                                                         *
***************************************************************************
"""
# noinspection PyPep8Naming

import argparse
import datetime
import os
import pathlib
import re
import requests
import shutil
import sys
import docutils.core
import typing
import xml.etree.ElementTree as ET
from xml.dom import minidom
from http.client import responses

import bitflagrenderer
from bitflagrenderer import DIR_REPO, __version__, PATH_ABOUT
from qps.make.deploy import QGISMetadataFileWriter
from qps.utils import file_search, zipdir

CHECK_COMMITS = False

########## Config Section

with open(PATH_ABOUT, 'r', encoding='utf-8') as f:
    aboutText = f.readlines()
    for i in range(1, len(aboutText)):
        aboutText[i] = '    ' + aboutText[i]
    aboutText = ''.join(aboutText)

MD = QGISMetadataFileWriter()
MD.mName = 'Virtual Raster Builder'
MD.mDescription = bitflagrenderer.DESCRIPTION
MD.mTags = ['Raster']
MD.mCategory = 'Analysis'
MD.mAuthor = 'Benjamin Jakimow, Geomatics Lab, Humboldt-Universität zu Berlin'
MD.mIcon = 'bitflagrenderer/icons/bitflagimage.png'
MD.mHomepage = bitflagrenderer.URL_HOMEPAGE
MD.mAbout = aboutText
MD.mTracker = bitflagrenderer.URL_ISSUE_TRACKER
MD.mRepository = bitflagrenderer.URL_REPOSITORY
MD.mQgisMinimumVersion = '3.14'
MD.mEmail = 'benjamin.jakimow@geo.hu-berlin.de'

PLUGIN_DIR_NAME = 'BitFlagRenderer'


########## End of config section

def scantree(path, pattern=re.compile('.$')) -> typing.Iterator[pathlib.Path]:
    """
    Recursively returns file paths in directory
    :param path: root directory to search in
    :param pattern: str with required file ending, e.g. ".py" to search for *.py files
    :return: pathlib.Path
    """
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from scantree(entry.path, pattern=pattern)
        elif entry.is_file and pattern.search(entry.path):
            yield pathlib.Path(entry.path)


def create_plugin():
    DIR_REPO = pathlib.Path(__file__).resolve().parents[1]
    assert (DIR_REPO / '.git').is_dir()

    DIR_DEPLOY = DIR_REPO / 'deploy'

    try:
        import git
        REPO = git.Repo(DIR_REPO)
        currentBranch = REPO.active_branch.name
    except Exception as ex:
        currentBranch = 'TEST'
        print('Unable to find git repo. Set currentBranch to "{}"'.format(currentBranch))

    timestamp = datetime.datetime.now().isoformat().split('.')[0]

    BUILD_NAME = '{}.{}.{}'.format(__version__, timestamp, currentBranch)
    BUILD_NAME = re.sub(r'[:-]', '', BUILD_NAME)
    BUILD_NAME = re.sub(r'[\\/]', '_', BUILD_NAME)
    PLUGIN_DIR = DIR_DEPLOY / PLUGIN_DIR_NAME
    PLUGIN_ZIP = DIR_DEPLOY / f'{PLUGIN_DIR_NAME}.{BUILD_NAME}.zip'

    if PLUGIN_DIR.is_dir():
        shutil.rmtree(PLUGIN_DIR)
    os.makedirs(PLUGIN_DIR, exist_ok=True)

    PATH_METADATAFILE = PLUGIN_DIR / 'metadata.txt'
    MD.mVersion = BUILD_NAME
    MD.writeMetadataTxt(PATH_METADATAFILE)

    # 1. (re)-compile all enmapbox resource files

    from scripts.compile_resourcefiles import compileResources
    compileResources()

    # copy python and other resource files
    pattern = re.compile(r'\.(py|svg|png|txt|ui|tif|qml|md|js|css)$')
    files = list(scantree(DIR_REPO / 'bitflagrenderer', pattern=pattern))
    files.extend(list(scantree(DIR_REPO / 'exampledata', pattern=pattern)))
    files.append(DIR_REPO / '__init__.py')
    files.append(DIR_REPO / 'ABOUT.html')
    files.append(DIR_REPO / 'CHANGELOG.rst')
    files.append(DIR_REPO / 'LICENSE.md')
    files.append(DIR_REPO / 'LICENSE.html')
    files.append(DIR_REPO / 'requirements.txt')

    for fileSrc in files:
        assert fileSrc.is_file()
        fileDst = PLUGIN_DIR / fileSrc.relative_to(DIR_REPO)
        os.makedirs(fileDst.parent, exist_ok=True)
        shutil.copy(fileSrc, fileDst.parent)

    # update metadata version

    f = open(DIR_REPO / 'bitflagrenderer' / '__init__.py')
    lines = f.read()
    f.close()
    lines = re.sub(r'(__version__\W*=\W*)([^\n]+)', r'__version__ = "{}"\n'.format(BUILD_NAME), lines)
    f = open(PLUGIN_DIR / 'bitflagrenderer' / '__init__.py', 'w')
    f.write(lines)
    f.flush()
    f.close()

    createCHANGELOG(PLUGIN_DIR)

    # 5. create a zip
    print('Create zipfile...')
    zipdir(PLUGIN_DIR, PLUGIN_ZIP)

    # 7. install the zip file into the local QGIS instance. You will need to restart QGIS!
    if True:
        info = []
        info.append(f'\n### To update/install the BitFlagRenderer, run this command on your QGIS Python shell:\n')
        info.append('from pyplugin_installer.installer import pluginInstaller')
        info.append('pluginInstaller.installFromZipFile(r"{}")'.format(PLUGIN_ZIP))
        info.append('#### Close (and restart manually)\n')
        # print('iface.mainWindow().close()\n')
        info.append('QProcess.startDetached(QgsApplication.arguments()[0], [])')
        info.append('QgsApplication.quit()\n')
        info.append('## press ENTER\n')

        print('\n'.join(info))

    print('Finished')


def createCHANGELOG(dirPlugin):
    """
    Reads the CHANGELOG.rst and creates the deploy/CHANGELOG (without extension!) for the QGIS Plugin Manager
    :return:
    """

    pathMD = os.path.join(DIR_REPO, 'CHANGELOG.rst')
    pathCL = os.path.join(dirPlugin, 'CHANGELOG')

    os.makedirs(os.path.dirname(pathCL), exist_ok=True)
    assert os.path.isfile(pathMD)

    overrides = {'stylesheet': None,
                 'embed_stylesheet': False,
                 'output_encoding': 'utf-8',
                 }

    html = docutils.core.publish_file(source_path=pathMD, writer_name='html5', settings_overrides=overrides)

    xml = minidom.parseString(html)
    #  remove headline
    for i, node in enumerate(xml.getElementsByTagName('h1')):
        if i == 0:
            node.parentNode.removeChild(node)
        else:
            node.tagName = 'h4'

    for node in xml.getElementsByTagName('link'):
        node.parentNode.removeChild(node)

    for node in xml.getElementsByTagName('meta'):
        if node.getAttribute('name') == 'generator':
            node.parentNode.removeChild(node)

    xml = xml.getElementsByTagName('body')[0]
    html = xml.toxml()
    html_cleaned = []
    for line in html.split('\n'):
        # line to modify
        line = re.sub(r'class="[^"]*"', '', line)
        line = re.sub(r'id="[^"]*"', '', line)
        line = re.sub(r'<li><p>', '<li>', line)
        line = re.sub(r'</p></li>', '</li>', line)
        line = re.sub(r'</?(dd|dt|div|body)[ ]*>', '', line)
        line = line.strip()
        if line != '':
            html_cleaned.append(line)
    # make html compact

    with open(pathCL, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_cleaned))

    if False:
        with open(pathCL + '.html', 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_cleaned))
    s = ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create the BitFlagRenderer Plugin')
    args = parser.parse_args()
    create_plugin()
    exit()