import { toShortDate } from '@api/date';
import { CopyButton, CreatedBy, SeriesAuthors } from '@components';
import {
  DocumentCover,
  DocumentTags,
  DocumentTitle,
} from '@components/Document';
import { DetailsHeader, SeriesIcon } from '@pages/backoffice/components';
import { FrontSiteRoutes } from '@routes/urls';
import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import { Header, Icon } from 'semantic-ui-react';

export class SeriesHeader extends Component {
  render() {
    const { data } = this.props;
    const recordInfo = (
      <>
        <label className="muted">Series</label> {data.metadata.pid}{' '}
        <CopyButton text={data.metadata.pid} />
        {data.metadata.created_by && (
          <>
            <br />
            <label className="muted">Created by</label>{' '}
            <CreatedBy metadata={data.metadata} />
          </>
        )}
        <br />
        <label className="muted">Created on</label> {toShortDate(data.created)}
        <br />
        <Link to={FrontSiteRoutes.seriesDetailsFor(data.metadata.pid)}>
          public view <Icon name="linkify" />
        </Link>
      </>
    );
    return (
      <DetailsHeader
        title={
          <>
            <Header.Subheader>
              {data.metadata.mode_of_issuance}
            </Header.Subheader>
            <DocumentTitle metadata={data.metadata} />
          </>
        }
        subTitle={<SeriesAuthors metadata={data.metadata} prefix={'by '} />}
        pid={data.metadata.pid}
        icon={
          data.metadata.coverUrl ? (
            <DocumentCover document={data} imageSize="huge" />
          ) : (
            <SeriesIcon />
          )
        }
        recordInfo={recordInfo}
      >
        <DocumentTags metadata={data.metadata} />
      </DetailsHeader>
    );
  }
}
