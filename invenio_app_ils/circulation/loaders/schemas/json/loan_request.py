# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio App ILS circulation Loan Request loader JSON schema."""

from datetime import timedelta

import arrow
from flask import current_app
from flask_babelex import lazy_gettext as _
from invenio_circulation.records.loaders.schemas.json import DateString
from marshmallow import Schema, ValidationError, fields, post_load, \
    validates, validates_schema

from .base import LoanBaseSchemaV1


def request_start_date_default():
    """Set default value for request_start_date field."""
    return arrow.get().utcnow().date().isoformat()


def request_expire_date_default():
    """Set default value for request_expire_date field."""
    duration_days = current_app.config[
        "CIRCULATION_LOAN_REQUEST_DURATION_DAYS"
    ]
    duration = timedelta(days=duration_days)
    now = arrow.get().utcnow()
    return (now + duration).date().isoformat()


class LoanRequestDeliverySchemaV1(Schema):
    """Loan common delivery Schema."""

    class Meta:
        """Meta attributes for the schema."""

        from marshmallow import EXCLUDE
        unknown = EXCLUDE

    method = fields.Str(required=True)

    @validates("method")
    def validate_method(self, value,  **kwargs):
        """Validate the delivery method."""
        delivery_methods = list(
            current_app.config["CIRCULATION_DELIVERY_METHODS"].keys()
        )
        if value not in delivery_methods:
            raise ValidationError(_("Invalid loan request delivery method."))


class LoanRequestSchemaV1(LoanBaseSchemaV1):
    """Loan request schema."""

    delivery = fields.Nested(LoanRequestDeliverySchemaV1)
    request_expire_date = DateString(missing=request_expire_date_default)
    request_start_date = DateString(missing=request_start_date_default)

    @validates_schema()
    def validates_schema(self, data, **kwargs):
        """Validate schema delivery field."""
        delivery = data.get("delivery")
        # if delivery methods is configured, it has to be a mandatory field
        if (
            current_app.config.get("CIRCULATION_DELIVERY_METHODS", {})
            and not delivery
        ):
            raise ValidationError(
                _("Delivery is required."), field_names=["delivery"]
            )

    @post_load()
    def postload_checks(self, data, **kwargs):
        """Validate dates values."""
        start = arrow.get(data["request_start_date"]).date()
        end = arrow.get(data["request_expire_date"]).date()
        duration_days = current_app.config[
            "CIRCULATION_LOAN_REQUEST_DURATION_DAYS"
        ]
        duration = timedelta(days=duration_days)

        if end < start:
            raise ValidationError(
                _("The request end date cannot be before the start date."),
                field_names=["request_start_date", "request_expire_date"],
            )
        elif end - start > duration:
            raise ValidationError(
                _(
                    "The request duration cannot be longer "
                    "than {} days.".format(duration_days)
                ),
                field_names=["request_start_date", "request_expire_date"],
            )
        return data
