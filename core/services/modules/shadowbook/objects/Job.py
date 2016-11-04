#!/usr/bin/env python
# -*- coding: utf8 -*-

#Hippocampe: Intel aggregator
#@author 2015 CERT-BDF <cert@banque-france.fr>
#@see The GNU Public License (GPL)
#
#This file is part of Hippocampe.
#
#Hippocampe is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 3 of the License, or
#(at your option) any later version.
#
#Hippocampe is distributed in the hope that it will be useful, but
#WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
#or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
#for more details.
#
#You should have received a copy of the GNU General Public License along
#with Hippocampe; if not, write to the Free Software Foundation, Inc.,
#59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#or see <http://www.gnu.org/licenses/>.
#

"""
	This module contains the class Source.
	======================================
"""
from ObjToIndex import ObjToIndex
import os, sys
install_dir = os.path.dirname(os.path.abspath(__file__)) + '/../../../../'
getConfPath = install_dir + 'services/modules/common'
sys.path.insert(0, getConfPath)
from getConf import getHippoConf
from IndexSource import IndexSource
from time import strftime
import logging
logger = logging.getLogger(__name__)
import dateutil.parser

class Job(ObjToIndex):

	def __init__(self):
		super(Job, self).__init__()
		cfg = getHippoConf()
		self.indexNameES = cfg.get('elasticsearch', 'indexNameES')
		self.typeNameES = cfg.get('elasticsearch', 'typeNameESJobs')
		self.status = str()
		self.startTime = str()
		self.endTime = str()
		self.duration = str()
		self.report = dict()

	def forgeDocSearchOngoing(self):
		"""
			Forges the search query to search source in elasticsearch.
		"""
		self.docSearch = {
		    "query": {
		        "bool": {
		            "must": [
		                {
		                    "match": {
		                        "status": "ongoing"
		                    }
		                }
		            ]
		        }
		    }
		}


	def forgeDocIndexOngoing(self):
		self.docIndex = {
		    "status": "ongoing",
		    "startTime": strftime("%Y%m%dT%H%M%S%z"),

		}
	
	def forgeDocUpdateJob(self):
		self.docUpdate = {
		    "script": "ctx._source.status = status; ctx._source.endTime = endTime; ctx._source.duration = duration; ctx._source.report=report",
		    "params": {
		        "status": self.status,
		        "endTime": self.endTime,
		        "duration": self.duration,
		        "report": self.report,
		    }
		}

	def searchOngoingJob(self):
		self.forgeDocSearchOngoing()
		nbOngoingJob = self.search()
		return nbOngoingJob

	def indexOngoingJob(self):
		self.forgeDocIndexOngoing()
		self.indexInES()
		return self.idInES

	def getStartTime(self):
		self.searchOngoingJob()
		#self.resSearch looks like:
		#{u'hits': {u'hits': [{u'_score': 11.907724, u'_type': u'jobs', u'_id': u'AVQkDgNs5CYfHJgxlSLE', u'_source': {u'status': u'ongoing', u'startTime': u'20160417T134938+0200'}, u'_index': u'hippocampe'}], u'total': 1, u'max_score': 11.907724}, u'_shards': {u'successful': 5, u'failed': 0, u'total': 5}, u'took': 1, u'timed_out': False}
		startTime = self.resSearch['hits']['hits'][0]['_source']['startTime']
		return startTime

	def calcDuration(self):
		self.startTime = self.getStartTime()
		duration = dateutil.parser.parse(self.endTime) - dateutil.parser.parse(self.startTime)
		#duration in seconds
		duration = duration.total_seconds()
		#duration in minutes
		duration = duration / 60.0
		#limiting to 2 digits
		self.duration = "%.2f" % duration

	def updateStatus(self, report, status):
		self.endTime = strftime("%Y%m%dT%H%M%S%z")
		self.status = status
		self.report = report

		self.calcDuration()
		self.forgeDocUpdateJob()
		self.update()
