import { Error, Loader } from '@components';
import { RelationSerial } from '@pages/backoffice/components/Relations/RelationSerial';
import _get from 'lodash/get';
import PropTypes from 'prop-types';
import React, { Component } from 'react';
import {
  Accordion,
  Container,
  Divider,
  Grid,
  Icon,
  Popup,
  Ref,
  Segment,
  Sticky,
} from 'semantic-ui-react';
import { SeriesActionMenu } from './';
import { SeriesDocuments, SeriesMultipartMonographs } from './components';
import SeriesMetadataTabs from './components/SeriesMetadata/SeriesMetadataTabs';
import { SeriesRelations } from './components/SeriesRelations/';
import { SeriesHeader } from './SeriesHeader';

export default class SeriesDetails extends Component {
  constructor(props) {
    super(props);
    this.menuRef = React.createRef();
    this.headerRef = React.createRef();
    this.fetchSeriesDetails = this.props.fetchSeriesDetails;
  }

  componentDidMount() {
    this.props.fetchSeriesDetails(this.props.match.params.seriesPid);
  }

  componentDidUpdate(prevProps, prevState) {
    if (
      prevProps.match.params.seriesPid !== this.props.match.params.seriesPid
    ) {
      this.props.fetchSeriesDetails(this.props.match.params.seriesPid);
    }
  }

  seriesPanels = () => {
    const { data } = this.props;

    const isSerial =
      _get(this.props.data, 'metadata.mode_of_issuance', '') === 'SERIAL';

    const _docsInSeries = _get(this.props.documentsInSeries, 'total', -1);
    const docsInSeries = _docsInSeries >= 0 ? ` (${_docsInSeries})` : '';
    const _multiMonoInSeries = _get(
      this.props.multipartMonographsInSeries,
      'total',
      -1
    );
    const multiMonoInSeries =
      _multiMonoInSeries >= 0 ? ` (${_multiMonoInSeries})` : '';

    const docsTitle = (
      <Accordion.Title>
        <Icon name="dropdown" />
        Documents in this series{docsInSeries}
        <Popup
          trigger={<Icon name="help circle" style={{ float: 'right' }} />}
          content="You can add/remove documents to this series by using the series panel in the document details"
          position="top right"
        />
      </Accordion.Title>
    );
    const panes = [
      {
        key: 'series-documents',
        title: docsTitle,
        content: (
          <Accordion.Content>
            <div id="series-documents">
              <SeriesDocuments />
            </div>
          </Accordion.Content>
        ),
      },
    ];

    const mmTitle = (
      <Accordion.Title>
        <Icon name="dropdown" />
        Multipart monographs in this series{multiMonoInSeries}
        <Popup
          trigger={<Icon name="help circle" style={{ float: 'right' }} />}
          content="You can add/remove multipart monograph to this series by using the series panel in the document details"
          position="top right"
        />
      </Accordion.Title>
    );
    const multiMonoInSeriesPane = {
      key: 'series-monographs',
      title: mmTitle,
      content: (
        <Accordion.Content>
          <div id="series-monographs">
            <SeriesMultipartMonographs />
          </div>
        </Accordion.Content>
      ),
    };
    const serialParentsPane = {
      key: 'series-serials',
      title: 'Part of serials',
      content: (
        <Accordion.Content>
          <div id="series-serials">
            <Segment>
              <RelationSerial recordDetails={data} />
            </Segment>
          </div>
        </Accordion.Content>
      ),
    };

    if (isSerial) {
      // it is Serial, show children Multipart Monograph
      panes.push(multiMonoInSeriesPane);
    } else {
      // it is Multipart Monograph, show parents serials pane
      panes.push(serialParentsPane);
    }

    panes.push({
      key: 'series-relations',
      title: 'Relations',
      content: (
        <Accordion.Content>
          <div id="series-relations">
            <SeriesRelations />
          </div>
        </Accordion.Content>
      ),
    });

    return panes;
  };

  render() {
    const { isLoading, error, data, relations } = this.props;
    return (
      <div ref={this.headerRef}>
        <Container fluid>
          <Loader isLoading={isLoading}>
            <Error error={error}>
              <Sticky context={this.headerRef} className="solid-background">
                <Container fluid className="spaced">
                  <SeriesHeader data={data} />
                </Container>
                <Divider />
              </Sticky>
              <Container fluid>
                <Ref innerRef={this.menuRef}>
                  <Grid columns={2}>
                    <Grid.Column width={13}>
                      <Container className="spaced">
                        <div id="metadata">
                          <SeriesMetadataTabs series={data} />
                        </div>
                        <Accordion
                          fluid
                          styled
                          className="highlighted"
                          panels={this.seriesPanels()}
                          exclusive={false}
                          defaultActiveIndex={[0, 1, 2]}
                        />
                      </Container>
                    </Grid.Column>
                    <Grid.Column width={3}>
                      <Sticky context={this.menuRef} offset={150}>
                        <SeriesActionMenu
                          anchors={this.anchors}
                          series={data}
                          relations={relations}
                        />
                      </Sticky>
                    </Grid.Column>
                  </Grid>
                </Ref>
              </Container>
            </Error>
          </Loader>
        </Container>
      </div>
    );
  }
}

SeriesDetails.propTypes = {
  isLoading: PropTypes.bool.isRequired,
  data: PropTypes.object,
  relations: PropTypes.object,
  error: PropTypes.object,
  // from redux state
  documentsInSeries: PropTypes.object,
  multipartMonographsInSeries: PropTypes.object,
};
