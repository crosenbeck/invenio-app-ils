import { IS_LOADING, SUCCESS, HAS_ERROR } from './types';
import { series as seriesApi } from '@api';
import { sendErrorNotification } from '@components/Notifications';

export const fetchSeriesMultipartMonographs = seriesPid => {
  return async dispatch => {
    dispatch({
      type: IS_LOADING,
    });

    await seriesApi
      .list(
        seriesApi
          .query()
          .withModeOfIssuance('MULTIPART_MONOGRAPH')
          .withSerialPid(seriesPid)
          .qs()
      )
      .then(response => {
        dispatch({
          type: SUCCESS,
          payload: response.data,
        });
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
