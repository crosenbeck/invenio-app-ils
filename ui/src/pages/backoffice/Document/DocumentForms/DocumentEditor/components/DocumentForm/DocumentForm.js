import { documentRequest as documentRequestApi } from '@api/documentRequests/documentRequest';
import { document as documentApi } from '@api/documents/document';
import { invenioConfig } from '@config';
import {
  BaseForm,
  BooleanField,
  GroupField,
  SelectField,
  StringField,
  TextField,
  UrlsField,
} from '@forms';
import { goTo } from '@history';
import { BackOfficeRoutes } from '@routes/urls';
import { getIn } from 'formik';
import _get from 'lodash/get';
import PropTypes from 'prop-types';
import React, { Component } from 'react';
import {
  AlternativeAbstracts,
  AlternativeIdentifiers,
  AlternativeTitles,
  AuthorsField,
  Copyrights,
  Identifiers,
  LicensesField,
  PublicationInfoField,
  Subjects,
  TableOfContent,
  TagsField,
} from './components';
import { ConferenceInfoField } from './components/ConferenceInfoField';
import { Imprint } from './components/Imprint';
import { InternalNotes } from './components/InternalNotes';
import { Keywords } from './components/Keywords';
import documentSubmitSerializer from './documentSubmitSerializer';

export class DocumentForm extends Component {
  get buttons() {
    if (this.props.pid) {
      return null;
    }

    return [
      {
        name: 'create',
        content: 'Create document',
        primary: true,
        type: 'submit',
      },
      {
        name: 'create-with-item',
        content: 'Create document and item',
        secondary: true,
        type: 'button',
      },
      {
        name: 'create-with-eitem',
        content: 'Create document and eitem',
        secondary: true,
        type: 'button',
      },
    ];
  }

  updateDocument = (pid, data) => {
    return documentApi.update(pid, data);
  };

  createDocument = data => {
    return documentApi.create(data);
  };

  successCallback = async (response, submitButton) => {
    const doc = getIn(response, 'data');
    const documentRequestPid = _get(
      this.props,
      'data.documentRequestPid',
      null
    );
    if (submitButton === 'create-with-item') {
      goTo(BackOfficeRoutes.itemCreate, { document: doc });
    } else if (submitButton === 'create-with-eitem') {
      goTo(BackOfficeRoutes.eitemCreate, { document: doc });
    } else if (documentRequestPid) {
      await documentRequestApi.addDocument(documentRequestPid, {
        document_pid: doc.pid,
      });
      goTo(BackOfficeRoutes.documentRequestDetailsFor(documentRequestPid));
    } else {
      goTo(BackOfficeRoutes.documentDetailsFor(doc.metadata.pid));
    }
  };

  render() {
    return (
      <BaseForm
        initialValues={this.props.data ? this.props.data.metadata : {}}
        editApiMethod={this.updateDocument}
        createApiMethod={this.createDocument}
        successCallback={this.successCallback}
        successSubmitMessage={this.props.successSubmitMessage}
        title={this.props.title}
        pid={this.props.pid}
        submitSerializer={documentSubmitSerializer}
        documentRequestPid={_get(this.props, 'data.documentRequestPid', null)}
        buttons={this.buttons}
      >
        <StringField label="Title" fieldPath="title" required optimized />
        <GroupField widths="equal">
          <SelectField
            options={invenioConfig.documents.types}
            fieldPath="document_type"
            label="Document type"
          />
          <StringField label="Edition" fieldPath="edition" optimized />
          <StringField
            label="Number of pages"
            fieldPath="number_of_pages"
            optimized
          />
        </GroupField>
        <StringField
          label="Source of the metadata"
          fieldPath="source"
          optimized
        />
        <StringField
          label="Publication year"
          fieldPath="publication_year"
          required
          optimized
        />
        <AuthorsField fieldPath="authors" />
        <BooleanField label="Other authors" fieldPath="other_authors" toggle />
        <BooleanField label="Restricted" fieldPath="restricted" toggle />
        <BooleanField label="Document is curated" fieldPath="curated" toggle />
        <TextField label="Abstract" fieldPath="abstract" rows={5} optimized />
        <TextField label="Notes" fieldPath="note" rows={5} optimized />
        <ConferenceInfoField />
        <AlternativeAbstracts />
        <LicensesField fieldPath="licenses" />
        <TableOfContent />
        <TagsField
          fieldPath="tags"
          type={invenioConfig.vocabularies.document.tags}
        />
        <UrlsField />
        <Subjects />
        <InternalNotes />
        <Identifiers />
        <AlternativeIdentifiers />
        <AlternativeTitles />
        <Copyrights />
        <PublicationInfoField />
        <Imprint />
        <Keywords />
      </BaseForm>
    );
  }
}

DocumentForm.propTypes = {
  formInitialData: PropTypes.object,
  successSubmitMessage: PropTypes.string,
  title: PropTypes.string,
  pid: PropTypes.string,
};
