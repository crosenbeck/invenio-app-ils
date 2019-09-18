# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2019 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI for Invenio App ILS."""
import random
from datetime import datetime, timedelta
from random import randint

import click
import lorem
from flask import current_app
from flask.cli import with_appcontext
from invenio_accounts.models import User
from invenio_circulation.api import Loan
from invenio_circulation.pidstore.pids import CIRCULATION_LOAN_PID_TYPE
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, \
    RecordIdentifier
from invenio_search import current_search

from invenio_app_ils.config import CIRCULATION_DELIVERY_METHODS

from .indexer import PatronsIndexer
from .records.api import Document, DocumentRequest, EItem, InternalLocation, \
    Item, Location, Patron, Series, Tag
from .records_relations.api import RecordRelationsParentChild, \
    RecordRelationsSiblings
from .relations.api import Relation

from .pidstore.pids import (  # isort:skip
    DOCUMENT_PID_TYPE,
    DOCUMENT_REQUEST_PID_TYPE,
    EITEM_PID_TYPE,
    ITEM_PID_TYPE,
    INTERNAL_LOCATION_PID_TYPE,
    LOCATION_PID_TYPE,
    SERIES_PID_TYPE,
    TAG_PID_TYPE,
)


def minter(pid_type, pid_field, record):
    """Mint the given PID for the given record."""
    PersistentIdentifier.create(
        pid_type=pid_type,
        pid_value=record[pid_field],
        object_type="rec",
        object_uuid=record.id,
        status=PIDStatus.REGISTERED,
    )
    RecordIdentifier.next()


class Holder():
    """Hold generated data."""

    def __init__(self,
                 patrons_pids,
                 librarian_pid,
                 total_intloc,
                 total_tags,
                 total_items,
                 total_eitems,
                 total_documents,
                 total_loans,
                 total_series,
                 total_document_requests):
        """Constructor."""
        self.patrons_pids = patrons_pids
        self.librarian_pid = librarian_pid

        self.location = {}
        self.internal_locations = {
            'objs': [],
            'total': total_intloc
        }
        self.tags = {
            'objs': [],
            'total': total_tags
        }
        self.items = {
            'objs': [],
            'total': total_items
        }
        self.eitems = {
            'objs': [],
            'total': total_eitems
        }
        self.documents = {
            'objs': [],
            'total': total_documents
        }
        self.loans = {
            'objs': [],
            'total': total_loans
        }
        self.series = {
            'objs': [],
            'total': total_series
        }
        self.related_records = {
            'objs': [],
            'total': 0,
        }
        self.document_requests = {
            'objs': [],
            'total': total_document_requests
        }

    def pids(self, collection, pid_field):
        """Get a list of PIDs for a collection."""
        return [obj[pid_field] for obj in getattr(self, collection)['objs']]


class Generator():
    """Generator."""

    def __init__(self, holder, minter):
        """Constructor."""
        self.holder = holder
        self.minter = minter

    def _persist(self, pid_type, pid_field, record):
        """Mint PID and store in the db."""
        minter(pid_type, pid_field, record)
        record.commit()
        return record


class LocationGenerator(Generator):
    """Location Generator."""

    def generate(self):
        """Generate."""
        self.holder.location = {
            "pid": "1",
            "name": "Central Library",
            "address": "Rue de Meyrin",
            "email": "library@cern.ch",
        }

    def persist(self):
        """Persist."""
        record = Location.create(self.holder.location)
        return self._persist(LOCATION_PID_TYPE, "pid", record)


class InternalLocationGenerator(Generator):
    """InternalLocation Generator."""

    def generate(self):
        """Generate."""
        size = self.holder.internal_locations['total']
        location_pid_value = self.holder.location["pid"]
        objs = [{
            "pid": str(pid),
            "legacy_id": "{}".format(randint(100000, 999999)),
            "name": "Building {}".format(randint(1, 10)),
            "notes": lorem.sentence(),
            "physical_location": lorem.sentence(),
            "location_pid": location_pid_value
        } for pid in range(1, size + 1)]

        self.holder.internal_locations['objs'] = objs

    def persist(self):
        """Persist."""
        recs = []
        for obj in self.holder.internal_locations['objs']:
            rec = self._persist(
                INTERNAL_LOCATION_PID_TYPE,
                "pid",
                InternalLocation.create(obj)
            )
            recs.append(rec)
        db.session.commit()
        return recs


class TagGenerator(Generator):
    """Tag Generator."""

    def generate(self):
        """Generate."""
        size = self.holder.tags['total']
        objs = [{
            "pid": str(pid),
            "name": lorem.sentence().split()[0],
            "provenance": lorem.sentence(),
        } for pid in range(1, size + 1)]

        self.holder.tags['objs'] = objs

    def persist(self):
        """Persist."""
        recs = []
        for obj in self.holder.tags['objs']:
            rec = self._persist(
                TAG_PID_TYPE,
                "pid",
                Tag.create(obj)
            )
            recs.append(rec)
        db.session.commit()
        return recs


class ItemGenerator(Generator):
    """Item Generator."""

    ITEM_CIRCULATION_RESTRICTIONS = ["NO_RESTRICTION", "FOR_REFERENCE_ONLY"]
    ITEM_MEDIUMS = ["NOT_SPECIFIED", "ONLINE", "PAPER", "CDROM", "DVD", "VHS"]
    ITEM_STATUSES = ["CAN_CIRCULATE", "MISSING", "IN_BINDING"]

    def generate(self):
        """Generate."""
        size = self.holder.items['total']
        iloc_pids = self.holder.pids('internal_locations', "pid")
        doc_pids = self.holder.pids('documents', "pid")
        objs = [{
            "pid": str(pid),
            "document_pid": random.choice(doc_pids),
            "internal_location_pid": random.choice(iloc_pids),
            "legacy_id": "{}".format(randint(100000, 999999)),
            "legacy_library_id": "{}".format(randint(5, 50)),
            "barcode": "{}".format(randint(10000000, 99999999)),
            "shelf": "{}".format(lorem.sentence()),
            "description": "{}".format(lorem.text()),
            "internal_notes": "{}".format(lorem.text()),
            "medium": random.choice(self.ITEM_MEDIUMS),
            "status": random.choice(self.ITEM_STATUSES),
            "circulation_restriction": random.choice(
                self.ITEM_CIRCULATION_RESTRICTIONS),
        } for pid in range(1, size + 1)]

        self.holder.items['objs'] = objs

    def persist(self):
        """Persist."""
        recs = []
        for obj in self.holder.items['objs']:
            rec = self._persist(
                ITEM_PID_TYPE,
                "pid",
                Item.create(obj)
            )
            recs.append(rec)
        db.session.commit()
        return recs


class EItemGenerator(Generator):
    """EItem Generator."""

    def generate(self):
        """Generate."""
        size = self.holder.eitems['total']
        doc_pids = self.holder.pids('documents', "pid")

        objs = [{
            "pid": str(pid),
            "document_pid": random.choice(doc_pids),
            "description": "{}".format(lorem.text()),
            "internal_notes": "{}".format(lorem.text()),
            "urls": ["https://home.cern/science/physics/dark-matter",
                     "https://home.cern/science/physics/antimatter"],
            "open_access": bool(random.getrandbits(1))
        } for pid in range(1, size + 1)]

        self.holder.eitems['objs'] = objs

    def persist(self):
        """Persist."""
        recs = []
        for obj in self.holder.eitems['objs']:
            rec = self._persist(
                EITEM_PID_TYPE,
                "pid",
                EItem.create(obj)
            )
            recs.append(rec)
        db.session.commit()
        return recs


class DocumentGenerator(Generator):
    """Document Generator."""

    DOCUMENT_TYPES = ["BOOK", "STANDARD", "PROCEEDINGS"]
    LANGUAGES = [u'en', u'fr', u'it', u'el', u'pl', u'ro', u'sv', u'es']

    def generate(self):
        """Generate."""
        size = self.holder.documents['total']
        tag_pids = self.holder.pids('tags', "pid")

        objs = [{
            "pid": str(pid),
            "title": {'title': "{}".format(lorem.sentence())},
            "authors": [
                {"full_name": "{}".format(lorem.sentence())}
            ],
            "abstracts": [{"value": "{}".format(lorem.text())}],
            "document_type": random.choice(self.DOCUMENT_TYPES),
            "_access": {},
            "languages": random.sample(self.LANGUAGES, 1),
            "imprints": [{"publisher": "{}".format(lorem.sentence())}],
            "table_of_content": ["{}".format(lorem.sentence())],
            "notes": [{'value': "{}".format(lorem.text())}],
            "tag_pids": random.sample(tag_pids, randint(0, 5)),
            "edition": str(pid),
            "keywords": lorem.sentence(),
        } for pid in range(1, size + 1)]

        self.holder.documents['objs'] = objs

    def persist(self):
        """Persist."""
        recs = []
        for obj in self.holder.documents['objs']:
            rec = self._persist(
                DOCUMENT_PID_TYPE,
                "pid",
                Document.create(obj)
            )
            recs.append(rec)
        db.session.commit()
        return recs


class LoanGenerator(Generator):
    """Loan Generator."""

    LOAN_STATUSES = ["PENDING", "ITEM_ON_LOAN", "ITEM_RETURNED", "CANCELLED"]

    def _get_item_can_circulate(self, items):
        """Return an item that can circulate."""
        item = items[randint(1, len(items) - 1)]
        if item["status"] != "CAN_CIRCULATE":
            return self._get_item_can_circulate(items)
        return item

    def _get_valid_status(self, item, items_on_loans):
        """Return valid loan status for the item to avoid inconsistencies."""
        # cannot have 2 loans in the same item
        if item["pid"] in items_on_loans:
            status = self.LOAN_STATUSES[0]
        else:
            status = self.LOAN_STATUSES[randint(0, 3)]
        return status

    def generate(self):
        """Generate."""
        size = self.holder.loans['total']
        loc_pid = self.holder.location["pid"]
        items = self.holder.items['objs']
        patrons_pids = self.holder.patrons_pids
        librarian_pid = self.holder.librarian_pid
        doc_pids = self.holder.pids('documents', "pid")

        current_year = datetime.utcnow().year
        items_on_loans = []
        for pid in range(1, size + 1):
            item = self._get_item_can_circulate(items)
            status = self._get_valid_status(item, items_on_loans)
            patron_id = random.choice(patrons_pids)
            transaction_date = datetime(
                current_year, randint(1, 12), randint(1, 28)
            )
            expire_date = transaction_date + timedelta(days=10)
            start_date = transaction_date + timedelta(days=3)
            end_date = transaction_date + timedelta(days=13)

            loan = {
                "pid": str(pid),
                "document_pid": random.choice(doc_pids),
                "extension_count": randint(0, 3),
                "patron_pid": "{}".format(patron_id),
                "pickup_location_pid": "{}".format(loc_pid),
                "state": "{}".format(status),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "transaction_date": transaction_date.isoformat(),
                "transaction_location_pid": "{}".format(loc_pid),
                "transaction_user_pid": "{}".format(librarian_pid),
            }

            if status == "PENDING":
                loan["item_pid"] = ""
            else:
                loan["item_pid"] = "{}".format(item["pid"])
                items_on_loans.append(item["pid"])

            self.holder.loans['objs'].append(loan)

    def persist(self):
        """Persist."""
        recs = []
        for obj in self.holder.loans['objs']:
            rec = self._persist(
                CIRCULATION_LOAN_PID_TYPE,
                "pid",
                Loan.create(obj)
            )
            recs.append(rec)
        db.session.commit()
        return recs


class MostLoanedGenerator(Generator):
    """Most loaned loan generator.

    Not currently used but is useful to generate a set of loans that is not
    random. Used to test the most loaned stats feature.
    """

    @staticmethod
    def build_loan(pid, document_pid, item_pid, state, start_date, end_date,
                   extensions):
        """Build loan object."""
        return {
            "pid": str(pid),
            "document_pid": document_pid,
            "item_pid": item_pid,
            "patron_pid": "1",
            "state": state,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "transaction_date": start_date.isoformat(),
            "transaction_location_pid": "1",
            "transaction_user_pid": "1",
            "pickup_location_pid": "1",
            "extension_count": extensions,
        }

    def get_doc_pairs(self):
        """Generate four document-item pairs."""
        doc_pids, item_pids = [], []
        for item in self.holder.items['objs']:
            if item['status'] == 'CAN_CIRCULATE' and \
                    item['document_pid'] not in doc_pids:
                doc_pids.append(item['document_pid'])
                item_pids.append(item['pid'])
                if len(doc_pids) == 4:
                    break
        return zip(doc_pids, item_pids)

    def generate(self):
        """Generate."""
        (doc1, item1), (doc2, item2), (doc3, item3), (doc4, item4) = \
            self.get_doc_pairs()

        today = datetime.utcnow()
        current_year = today.year

        # Generate loans for doc1
        pid = 1
        for month in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11):
            start_date = datetime(current_year, month, 2)
            end_date = datetime(current_year, month + 1, 2)
            if start_date <= today <= end_date:
                state = "ITEM_ON_LOAN"
            elif end_date < today:
                state = "ITEM_RETURNED"
            else:
                state = "PENDING"
            loan = self.build_loan(
                pid,
                doc1,
                item1,
                state,
                start_date,
                end_date,
                0
            )
            self.holder.loans['objs'].append(loan)
            pid += 1
        for month in (2, 4, 6, 8, 10):
            start_date = datetime(current_year, month, 10)
            end_date = datetime(current_year, month + 2, 10)
            if start_date <= today <= end_date:
                state = "ITEM_ON_LOAN"
            elif end_date < today:
                state = "ITEM_RETURNED"
            else:
                state = "PENDING"
            loan = self.build_loan(
                pid,
                doc2,
                item2,
                state,
                start_date,
                end_date,
                1
            )
            self.holder.loans['objs'].append(loan)
            pid += 1
        for month in (2, 5, 8):
            start_date = datetime(current_year, month, 20)
            end_date = datetime(current_year, month + 3, 20)
            if start_date <= today <= end_date:
                state = "ITEM_ON_LOAN"
            elif end_date < today:
                state = "ITEM_RETURNED"
            else:
                state = "PENDING"
            loan = self.build_loan(
                pid,
                doc3,
                item3,
                state,
                start_date,
                end_date,
                3
            )
            self.holder.loans['objs'].append(loan)
            pid += 1
        start_date = datetime(current_year, 3, 7)
        end_date = datetime(current_year, 4, 7)
        self.holder.loans['objs'].append(
            self.build_loan(
                pid,
                doc4,
                item4,
                "ITEM_RETURNED",
                start_date,
                end_date,
                0
            )
        )

    def persist(self):
        """Persist."""
        recs = []
        for obj in self.holder.loans['objs']:
            rec = self._persist(
                CIRCULATION_LOAN_PID_TYPE,
                "pid",
                Loan.create(obj)
            )
            recs.append(rec)
        db.session.commit()
        return recs


class SeriesGenerator(Generator):
    """Series Generator."""

    DOCUMENT_TYPES = ["BOOK", "STANDARD", "PROCEEDINGS"]
    LANGUAGES = ["en", "fr", "it", "el", "pl", "ro", "sv", "es"]
    MODE_OF_ISSUANCE = ["MULTIPART_MONOGRAPH", "SERIAL"]

    def random_issn(self):
        """Generate a random ISSN."""
        random_4digit = [randint(1000, 9999), randint(1000, 9999)]
        return '-'.join(str(r) for r in random_4digit)

    def generate(self):
        """Generate."""
        size = self.holder.series['total']
        objs = []
        for pid in range(1, size + 1):
            moi = random.choice(self.MODE_OF_ISSUANCE)
            obj = {
                "pid": str(pid),
                "mode_of_issuance": moi,
                "issn": self.random_issn(),
                "title": {"title": "{}".format(lorem.sentence())},
                "authors": ["{}".format(lorem.sentence())],
                "abstracts": ["{}".format(lorem.text())],
                "language": random.sample(self.LANGUAGES, 1),
                "publishers": ["{}".format(lorem.sentence())],
            }
            if moi == "MULTIPART_MONOGRAPH":
                obj["edition"] = str(pid)
            objs.append(obj)

        self.holder.series['objs'] = objs

    def persist(self):
        """Persist."""
        recs = []
        for obj in self.holder.series['objs']:
            rec = self._persist(
                SERIES_PID_TYPE,
                "pid",
                Series.create(obj)
            )
            recs.append(rec)
        db.session.commit()
        return recs


class RecordRelationsGenerator(Generator):
    """Related records generator."""

    @staticmethod
    def random_series(series, moi):
        """Get a random series with a specific mode of issuance."""
        for s in random.sample(series, len(series)):
            if s['mode_of_issuance'] == moi:
                return s

    def generate_parent_child_relations(self, documents, series):
        """Generate parent-child relations."""
        def random_docs():
            return random.sample(documents, randint(1, min(5, len(documents))))

        objs = self.holder.related_records['objs']
        serial_parent = self.random_series(series, 'SERIAL')
        multipart_parent = self.random_series(series, 'MULTIPART_MONOGRAPH')
        serial_children = documents  # random_docs()
        multipart_children = random_docs()

        objs.append(serial_parent)
        rr = RecordRelationsParentChild()
        serial_relation = Relation.get_relation_by_name('serial')
        multipart_relation = Relation.get_relation_by_name(
            'multipart_monograph')
        for index, child in enumerate(serial_children):
            rr.add(
                serial_parent,
                child,
                relation_type=serial_relation,
                volume='{}'.format(index + 1)
            )
            objs.append(child)
        for index, child in enumerate(multipart_children):
            rr.add(
                multipart_parent,
                child,
                relation_type=multipart_relation,
                volume='{}'.format(index + 1)
            )
            objs.append(child)

    def generate_sibling_relations(self, documents, series):
        """Generate sibling relations."""
        objs = self.holder.related_records['objs']
        rr = RecordRelationsSiblings()

        def add_random_relations(relation_type):
            random_docs = random.sample(documents,
                                        randint(2, min(5, len(documents))))

            objs.append(random_docs[0])
            for record in random_docs[1:]:
                rr.add(random_docs[0], record, relation_type=relation_type)
                objs.append(record)

            if relation_type.name == 'edition':
                record = self.random_series(series, 'MULTIPART_MONOGRAPH')
                rr.add(random_docs[0], record, relation_type=relation_type)
                objs.append(record)

        add_random_relations(Relation.get_relation_by_name('language'))
        add_random_relations(Relation.get_relation_by_name('edition'))

    def generate(self, rec_docs, rec_series):
        """Generate related records."""
        self.generate_parent_child_relations(rec_docs, rec_series)
        self.generate_sibling_relations(rec_docs, rec_series)

    def persist(self):
        """Persist."""
        db.session.commit()
        return self.holder.related_records['objs']


class DocumentRequestGenerator(Generator):
    """Document requests generator."""

    def random_document_pid(self, state):
        """Get a random document PID if the state is FULFILLED."""
        if state == "FULFILLED":
            return random.choice(self.holder.pids("documents", "pid"))
        return None

    def generate(self):
        """Generate."""
        size = self.holder.series['total']
        objs = []
        for pid in range(1, size + 1):
            obj = {
                "pid": str(pid),
                "patron_pid": random.choice(self.holder.patrons_pids),
                "title": lorem.sentence(),
                "authors": lorem.sentence(),
                "publication_year": randint(1700, 2019),
            }
            objs.append(obj)

        self.holder.document_requests['objs'] = objs

    def persist(self):
        """Persist."""
        recs = []
        for obj in self.holder.document_requests['objs']:
            rec = self._persist(
                DOCUMENT_REQUEST_PID_TYPE,
                "pid",
                DocumentRequest.create(obj)
            )
            recs.append(rec)
        db.session.commit()
        return recs


@click.group()
def demo():
    """Demo data CLI."""


@demo.command()
@click.option("--docs", "n_docs", default=20)
@click.option("--items", "n_items", default=50)
@click.option("--eitems", "n_eitems", default=30)
@click.option("--loans", "n_loans", default=100)
@click.option("--tags", "n_tags", default=40)
@click.option("--internal-locations", "n_intlocs", default=10)
@click.option("--series", "n_series", default=10)
@click.option("--document-requests", "n_document_requests", default=10)
@with_appcontext
def data(n_docs, n_items, n_eitems, n_loans, n_tags, n_intlocs, n_series,
         n_document_requests):
    """Insert demo data."""
    click.secho('Generating demo data', fg='yellow')

    indexer = RecordIndexer()

    holder = Holder(
        patrons_pids=["1", "2", "5", "6"],
        librarian_pid="4",
        total_intloc=n_intlocs,
        total_tags=n_tags,
        total_items=n_items,
        total_eitems=n_eitems,
        total_documents=n_docs,
        total_loans=n_loans,
        total_series=n_series,
        total_document_requests=n_document_requests,
    )

    click.echo('Creating locations...')
    loc_generator = LocationGenerator(holder, minter)
    loc_generator.generate()
    rec = loc_generator.persist()
    indexer.index(rec)

    # InternalLocations
    intlocs_generator = InternalLocationGenerator(holder, minter)
    intlocs_generator.generate()
    rec_intlocs = intlocs_generator.persist()

    # Tags
    click.echo('Creating tags...')
    tags_generator = TagGenerator(holder, minter)
    tags_generator.generate()
    rec_tags = tags_generator.persist()

    # Series
    click.echo('Creating series...')
    series_generator = SeriesGenerator(holder, minter)
    series_generator.generate()
    rec_series = series_generator.persist()

    # Documents
    click.echo('Creating documents...')
    documents_generator = DocumentGenerator(holder, minter)
    documents_generator.generate()
    rec_docs = documents_generator.persist()

    # Items
    click.echo('Creating items...')
    items_generator = ItemGenerator(holder, minter)
    items_generator.generate()
    rec_items = items_generator.persist()

    # EItems
    click.echo('Creating eitems...')
    eitems_generator = EItemGenerator(holder, minter)
    eitems_generator.generate()
    rec_eitems = eitems_generator.persist()

    # Loans
    click.echo('Creating loans...')
    loans_generator = LoanGenerator(holder, minter)
    loans_generator.generate()
    rec_loans = loans_generator.persist()

    # Related records
    click.echo('Creating related records...')
    related_generator = RecordRelationsGenerator(holder, minter)
    related_generator.generate(rec_docs, rec_series)
    related_generator.persist()

    # Document requests
    click.echo('Creating document requests...')
    document_requests_generator = DocumentRequestGenerator(holder, minter)
    document_requests_generator.generate()
    rec_requests = document_requests_generator.persist()

    # index locations
    indexer.bulk_index([str(r.id) for r in rec_intlocs])
    click.echo('Sent to the indexing queue {0} locations'.format(
        len(rec_intlocs)))

    # index tags
    indexer.bulk_index([str(r.id) for r in rec_tags])
    click.echo('Sent to the indexing queue {0} tags'.format(
        len(rec_tags)))
    # process queue so series can resolve tags correctly
    indexer.process_bulk_queue()

    # index series
    indexer.bulk_index([str(r.id) for r in rec_series])
    click.echo('Sent to the indexing queue {0} series'.format(
        len(rec_series)))

    # index loans
    indexer.bulk_index([str(r.id) for r in rec_loans])
    click.echo('Sent to the indexing queue {0} loans'.format(len(rec_loans)))

    click.secho('Now indexing...', fg='green')
    # process queue so items can resolve circulation status correctly
    indexer.process_bulk_queue()

    # index eitems
    indexer.bulk_index([str(r.id) for r in rec_eitems])
    click.echo('Sent to the indexing queue {0} eitems'.format(len(rec_eitems)))

    # index items
    indexer.bulk_index([str(r.id) for r in rec_items])
    click.echo('Sent to the indexing queue {0} items'.format(len(rec_items)))

    click.secho('Now indexing...', fg='green')
    # process queue so documents can resolve circulation correctly
    indexer.process_bulk_queue()

    # index document requests
    indexer.bulk_index([str(r.id) for r in rec_requests])
    click.echo('Sent to the indexing queue {0} document requests'.format(
        len(rec_requests)))

    click.secho('Now indexing...', fg='green')
    indexer.process_bulk_queue()

    # flush all indices after indexing, otherwise ES won't be ready for tests
    current_search.flush_and_refresh(index='*')

    # index documents
    indexer.bulk_index([str(r.id) for r in rec_docs])
    click.echo('Sent to the indexing queue {0} documents'.format(
        len(rec_docs)))

    click.secho('Now indexing...', fg='green')
    indexer.process_bulk_queue()


@click.group()
def patrons():
    """Patrons data CLI."""


@patrons.command()
@with_appcontext
def index():
    """Index patrons."""
    from flask import current_app
    from invenio_app_ils.pidstore.pids import PATRON_PID_TYPE
    patrons = User.query.all()
    indexer = PatronsIndexer()

    click.secho('Now indexing {0} patrons'.format(len(patrons)), fg='green')

    rest_config = current_app.config["RECORDS_REST_ENDPOINTS"]
    patron_cls = rest_config[PATRON_PID_TYPE]["record_class"] or Patron
    for pat in patrons:
        patron = patron_cls(pat.id)
        indexer.index(patron)


@click.command()
@click.option('--recreate-db', is_flag=True, help='Recreating DB.')
@click.option('--skip-demo-data', is_flag=True,
              help='Skip creating demo data.')
@click.option('--skip-patrons', is_flag=True, help='Skip creating patrons.')
@click.option('--verbose', is_flag=True, help='Verbose output.')
@with_appcontext
def setup(recreate_db, skip_demo_data, skip_patrons, verbose):
    """ILS setup command."""
    from flask import current_app
    from invenio_base.app import create_cli
    import redis

    click.secho('ils setup started...', fg='blue')

    # Clean redis
    redis.StrictRedis.from_url(
        current_app.config['CACHE_REDIS_URL']).flushall()
    click.secho('redis cache cleared...', fg='red')

    cli = create_cli()
    runner = current_app.test_cli_runner()

    def run_command(command, catch_exceptions=False):
        click.secho('ils {}...'.format(command), fg='green')
        res = runner.invoke(cli, command, catch_exceptions=catch_exceptions)
        if verbose:
            click.secho(res.output)

    # Remove and create db and indexes
    if recreate_db:
        run_command('db destroy --yes-i-know', catch_exceptions=True)
        run_command('db init')
    else:
        run_command('db drop --yes-i-know')
    run_command('db create')
    run_command('index destroy --force --yes-i-know')
    run_command('index init --force')
    run_command('index queue init purge')

    # Create roles to restrict access
    run_command('roles create admin')
    run_command('roles create librarian')

    if not skip_patrons:
        # Create users
        run_command(
            'users create patron1@test.ch -a --password=123456')  # ID 1
        run_command(
            'users create patron2@test.ch -a --password=123456')  # ID 2
        run_command('users create admin@test.ch -a --password=123456')  # ID 3
        run_command(
            'users create librarian@test.ch -a --password=123456')  # ID 4
        run_command(
            'users create patron3@test.ch -a --password=123456')  # ID 5
        run_command(
            'users create patron4@test.ch -a --password=123456')  # ID 6

        # Assign roles
        run_command('roles add admin@test.ch admin')
        run_command('roles add librarian@test.ch librarian')

    # Assign actions
    run_command('access allow superuser-access role admin')
    run_command('access allow ils-backoffice-access role librarian')

    # Index patrons
    run_command('patrons index')

    # Generate demo data
    if not skip_demo_data:
        run_command('demo data')

    click.secho('ils setup finished successfully', fg='blue')
