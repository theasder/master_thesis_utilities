# -*- coding: utf-8 -*-

from __future__ import print_function

import os
from os import listdir, path
from os.path import isfile, join

from io import open
from shutil import copyfile, rmtree
import subprocess
from collections import defaultdict
import xml.etree.ElementTree
import subprocess

class TomitaParser(object):

    # TODO: remove some symbols from documents \r, \t, \. \, ...
    # TODO: generate fact_descriptions by fact file
    # TODO: return dataframe with Fact_Property: ('a', 'b')

    def __init__(self, num_threads=2):
        self.binary_path = '/root/tomita-parser/build/bin/tomita-parser'
        self.base_dir = 'tomita_test'
        
        self.list_of_files = [f for f in listdir(self.base_dir) if isfile(join(self.base_dir, f))]
        
        # copying files in local directory
        
        for f in self.list_of_files:
            copyfile(path.join(self.base_dir, f), f)
        
        self.config_file = 'config.proto'
        self.documents_file = 'documents_dlp.txt'
        self.output_file = 'facts.xml'
        self.fact_files = []
        self.num_threads = num_threads
        # TODO: mkdir if not exists.

    def set_documents(self, documents):
        with open(self.documents_file, 'w', encoding='utf8') as fd:
            for doc in documents:
                doc = doc.replace('\n', ' ')
                fd.write(doc + '\n')
            print('Writed documents_dlp.txt')
            self.documents = documents

    def run(self):
        """
        deletes output file and creates new
        :raises: subprocess.CalledProcessError if tomita parser failed
        :returns: True if run was successful
        """
        if os.path.isfile(self.output_file):
            os.unlink(self.output_file)
        try:
            output = subprocess.check_output(
                self.binary_path + ' ' + self.config_file,
                shell=True,
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            )
            print(self.binary_path + ' ' + self.config_file)
        except subprocess.CalledProcessError as e:
            print('Got exception {}'.format(e))
            print('Tomita output {}'.format(e.output))
            raise e
        success = 'End.  (Processing files.)' in output
        return success

    def get_xml(self):
        """ :return: xml.etree.ElementTree root """
        return xml.etree.ElementTree.parse(self.output_file).getroot()

    def parse(self, fact_descriptions):
        """
        :param fact_descriptions: {'DrivingLicense': ['Category']}
        :return: dict with keys as document id numbers.
        If document doesn't contain facts it just skipped in dictionary

        Example:
        expected_result = {
            1: {'Category': ['C', 'СE']},
            3: {'Category': ['C']}
        }
        """
        root = self.get_xml()
        out = [dict() for i in range(len(self.documents))]
        
        for document in root.findall('document'):
            document_id = int(document.attrib['di'])
            doc_facts = defaultdict(list)
            facts = document.find('facts')
            for fact_name in fact_descriptions:
                attributes = facts.findall(fact_name)
                for attr in attributes:
                    for attribute_name in fact_descriptions[fact_name]:
                        try:
                            value = attr.find(attribute_name).attrib.get('val')
                            doc_facts[attribute_name].append(value)
                        except AttributeError:
                            pass
            doc_facts = dict(doc_facts)
            out[document_id - 1] = doc_facts
            
        for i in range(len(self.documents)):
            out[i]['text'] = self.documents[i]
            for fact_name in fact_descriptions:
                for attribute_name in fact_descriptions[fact_name]:
                    if attribute_name not in out[i]:
                        out[i][attribute_name] = []
                
        return out

    def clean(self):
        """ Deletes temporary files from working directory. """
        files_to_delete = [
            self.documents_file,
            self.output_file,
        ]
        files = os.listdir('.')

        for f in files:
            if f.endswith(".bin"):
                os.remove(f)
        try:
            rmtree('__pycache__')
        except FileNotFoundError:
            pass
        files_to_delete.extend(self.list_of_files)
        
        for file in files_to_delete:
            try:
                os.unlink(file)
            except OSError:
                pass
