import {
  SearchAggregationsCards,
  SearchControls,
  SearchEmptyResults,
  SearchFooter,
} from '@components/SearchControls';
import EItemList from './EitemList';
import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import { Button, Grid, Header, Container } from 'semantic-ui-react';
import {
  ReactSearchKit,
  SearchBar,
  ResultsList,
  ResultsLoader,
  EmptyResults,
  Error,
  InvenioSearchApi,
} from 'react-searchkit';
import { getSearchConfig } from '@config';
import { Error as IlsError, SearchBar as EItemsSearchBar } from '@components';
import { eitem as eitemApi } from '@api';
import { responseRejectInterceptor } from '@api/base';
import { ExportReactSearchKitResults } from '../../components';
import { NewButton } from '../../components/buttons';
import { BackOfficeRoutes } from '@routes/urls';
import history from '@history';

export class EItemSearch extends Component {
  searchApi = new InvenioSearchApi({
    axios: {
      url: eitemApi.searchBaseURL,
      withCredentials: true,
    },
    interceptors: {
      response: { reject: responseRejectInterceptor },
    },
  });
  searchConfig = getSearchConfig('eitems');

  renderSearchBar = (_, queryString, onInputChange, executeSearch) => {
    const helperFields = [
      {
        name: 'title',
        field: 'document.title',
      },
      {
        name: 'author',
        field: 'authors.full_name',
        defaultValue: '"Doe, John"',
      },
      {
        name: 'created',
        field: '_created',
      },
    ];
    return (
      <EItemsSearchBar
        currentQueryString={queryString}
        onInputChange={onInputChange}
        executeSearch={executeSearch}
        placeholder={'Search for eitems'}
        queryHelperFields={helperFields}
      />
    );
  };

  viewDetails = ({ row }) => {
    return (
      <Button
        as={Link}
        to={BackOfficeRoutes.eitemDetailsFor(row.metadata.pid)}
        compact
        icon="info"
        data-test={row.metadata.pid}
      />
    );
  };

  renderError = error => {
    return <IlsError error={error} />;
  };

  renderCount = totalResults => {
    return <div>{totalResults} results</div>;
  };

  renderEmptyResultsExtra = () => {
    return (
      <NewButton
        text={'Add electronic item'}
        to={BackOfficeRoutes.eitemCreate}
      />
    );
  };

  renderEitemList = results => {
    return <EItemList hits={results} />;
  };

  render() {
    return (
      <>
        <Header as="h2">Electronic items</Header>

        <ReactSearchKit searchApi={this.searchApi} history={history}>
          <Container fluid className="spaced">
            <SearchBar renderElement={this.renderSearchBar} />
          </Container>
          <Grid>
            <Grid.Row columns={2}>
              <ResultsLoader>
                <Grid.Column width={3} className={'search-aggregations'}>
                  <Header content={'Filter by'} />
                  <SearchAggregationsCards modelName={'eitems'} />
                </Grid.Column>
                <Grid.Column width={13}>
                  <Grid columns={2}>
                    <Grid.Column width={8}>
                      <NewButton
                        text={'Add electronic item'}
                        to={BackOfficeRoutes.eitemCreate}
                      />
                    </Grid.Column>
                    <Grid.Column width={8} textAlign={'right'}>
                      <ExportReactSearchKitResults
                        exportBaseUrl={eitemApi.searchBaseURL}
                      />
                    </Grid.Column>
                  </Grid>
                  <EmptyResults renderElement={this.renderEmptyResults} />
                  <Error renderElement={this.renderError} />
                  <SearchControls modelName={'eitems'} />
                  <SearchEmptyResults extras={this.renderEmptyResultsExtra} />
                  <ResultsList renderElement={this.renderEitemList} />
                  <SearchFooter />
                </Grid.Column>
              </ResultsLoader>
            </Grid.Row>
          </Grid>
        </ReactSearchKit>
      </>
    );
  }
}
