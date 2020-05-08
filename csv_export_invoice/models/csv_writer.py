# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
#    CSV data formating inspired from
# http://docs.python.org/2.7/library/csv.html?highlight=csv#examples
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import codecs
import csv

from cStringIO import StringIO


class CSVUnicodeWriter:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwargs):
        # Redirect output to a queue
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwargs)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        # we ensure that we do not try to encode none or bool
        row = (x or u"" for x in row)

        encoded_row = [
            c.encode("utf-8") if isinstance(c, unicode) else c  # noqa
            for c in row
        ]

        self.writer.writerow(encoded_row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
