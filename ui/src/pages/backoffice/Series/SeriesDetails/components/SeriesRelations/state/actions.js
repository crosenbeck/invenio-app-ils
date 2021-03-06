import { IS_LOADING, SUCCESS, HAS_ERROR } from './types';
import { series as seriesApi } from '@api';
import {
  sendErrorNotification,
  sendSuccessNotification,
} from '@components/Notifications';

export const createRelations = (pid, relations) => {
  return async dispatch => {
    if (relations.length) {
      dispatch({
        type: IS_LOADING,
      });

      await seriesApi
        .createRelation(pid, relations)
        .then(response => {
          dispatch({
            type: SUCCESS,
            payload: response.data.metadata.relations,
          });
          dispatch(
            sendSuccessNotification(
              'Success!',
              'Relations were successfully added.'
            )
          );
        })
        .catch(error => {
          dispatch({
            type: HAS_ERROR,
            payload: error,
          });
          dispatch(sendErrorNotification(error));
        });
    }
  };
};

export const deleteRelation = (pid, relation) => {
  return async dispatch => {
    dispatch({
      type: IS_LOADING,
    });

    await seriesApi
      .deleteRelation(pid, relation)
      .then(response => {
        dispatch({
          type: SUCCESS,
          payload: response.data.metadata.relations,
        });
        dispatch(
          sendSuccessNotification('Success!', 'Relation successfully removed.')
        );
      })
      .catch(error => {
        dispatch({
          type: HAS_ERROR,
          payload: error,
        });
        dispatch(sendErrorNotification(error));
      });
  };
};
