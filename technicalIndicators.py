from __future__ import division
from __future__ import absolute_import
import numpy as np
import pandas as pd  

import math as m

class IndicatorMixin(object):

    def _check_fillna(self, serie, value = 0):
        u"""Check if fillna flag is True.
        Args:
            serie(pandas.Series): dataset 'Close' column.
            value(int): value to fill gaps; if -1 fill values using 'backfill' mode.
        Returns:
            pandas.Series: New feature generated.
        """
        if self._fillna:
            serie_output = serie.copy(deep=False)
            serie_output = serie_output.replace([np.inf, -np.inf], np.nan)
            if isinstance(value, int) and value == -1:
                return serie_output.fillna(method=u'ffill').fillna(value=-1)
            else:
                return serie_output.fillna(method=u'ffill').fillna(value)
        else:
            return serie

    def _true_range(self, high, low, prev_close):
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.DataFrame(data={u'tr1': tr1, u'tr2': tr2, u'tr3': tr3}).max(axis=1)
        return tr


class ADXIndicator(IndicatorMixin):
    u"""Average Directional Movement Index (ADX)
    The Plus Directional Indicator (+DI) and Minus Directional Indicator (-DI)
    are derived from smoothed averages of these differences, and measure trend
    direction over time. These two indicators are often referred to
    collectively as the Directional Movement Indicator (DMI).
    The Average Directional Index (ADX) is in turn derived from the smoothed
    averages of the difference between +DI and -DI, and measures the strength
    of the trend (regardless of direction) over time.
    Using these three indicators together, chartists can determine both the
    direction and strength of the trend.
    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx
    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        fillna(bool): if True, fill nan values.
    """

    def __init__(self, high, low, close, n = 14, fillna = False):
        self._high = high
        self._low = low
        self._close = close
        self._n = n
        self._fillna = fillna
        self._run()

    def _run(self):
        assert self._n != 0, u"N may not be 0 and is %r" % n

        cs = self._close.shift(1)
        pdm = get_min_max(self._high, cs, u'max')
        pdn = get_min_max(self._low, cs, u'min')
        tr = pdm - pdn

        self._trs_initial = np.zeros(self._n-1)
        self._trs = np.zeros(len(self._close) - (self._n - 1))
        self._trs[0] = tr.dropna()[0:self._n].sum()
        tr = tr.reset_index(drop=True)

        for i in xrange(1, len(self._trs)-1):
            self._trs[i] = self._trs[i-1] - (self._trs[i-1]/float(self._n)) + tr[self._n+i]

        up = self._high - self._high.shift(1)
        dn = self._low.shift(1) - self._low
        pos = abs(((up > dn) & (up > 0)) * up)
        neg = abs(((dn > up) & (dn > 0)) * dn)

        self._dip = np.zeros(len(self._close) - (self._n - 1))
        self._dip[0] = pos.dropna()[0:self._n].sum()

        pos = pos.reset_index(drop=True)

        for i in xrange(1, len(self._dip)-1):
            self._dip[i] = self._dip[i-1] - (self._dip[i-1]/float(self._n)) + pos[self._n+i]

        self._din = np.zeros(len(self._close) - (self._n - 1))
        self._din[0] = neg.dropna()[0:self._n].sum()

        neg = neg.reset_index(drop=True)

        for i in xrange(1, len(self._din)-1):
            self._din[i] = self._din[i-1] - (self._din[i-1]/float(self._n)) + neg[self._n+i]

    def adx(self):
        u"""Average Directional Index (ADX)
        Returns:
            pandas.Series: New feature generated.
        """
        dip = np.zeros(len(self._trs))
        for i in xrange(len(self._trs)):
            dip[i] = 100 * (self._dip[i]/self._trs[i])

        din = np.zeros(len(self._trs))
        for i in xrange(len(self._trs)):
            din[i] = 100 * (self._din[i]/self._trs[i])

        dx = 100 * np.abs((dip - din) / (dip + din))

        adx = np.zeros(len(self._trs))
        adx[self._n] = dx[0:self._n].mean()

        for i in xrange(self._n+1, len(adx)):
            adx[i] = ((adx[i-1] * (self._n - 1)) + dx[i-1]) / float(self._n)

        adx = np.concatenate((self._trs_initial, adx), axis=0)
        self._adx = pd.Series(data=adx, index=self._close.index)

        adx = self._check_fillna(self._adx, value=20)
        return pd.Series(adx, name=u'adx')

    def adx_pos(self):
        u"""Plus Directional Indicator (+DI)
        Returns:
            pandas.Series: New feature generated.
        """
        dip = np.zeros(len(self._close))
        for i in xrange(1, len(self._trs)-1):
            dip[i+self._n] = 100 * (self._dip[i]/self._trs[i])

        adx_pos = self._check_fillna(pd.Series(dip, index=self._close.index), value=20)
        return pd.Series(adx_pos, name=u'adx_pos')

    def adx_neg(self):
        u"""Minus Directional Indicator (-DI)
        Returns:
            pandas.Series: New feature generated.
        """
        din = np.zeros(len(self._close))
        for i in xrange(1, len(self._trs)-1):
            din[i+self._n] = 100 * (self._din[i]/self._trs[i])

        adx_neg = self._check_fillna(pd.Series(din, index=self._close.index), value=20)
        return pd.Series(adx_neg, name=u'adx_neg')

def get_min_max(x1, x2, f=u'min'):
    u"""Find min or max value between two lists for each index
    """
    x1 = np.array(x1)
    x2 = np.array(x2)
    try:
        if f == u'min':
            return pd.Series(np.amin([x1, x2], axis=0))
        elif f == u'max':
            return pd.Series(np.amax([x1, x2], axis=0))
        else:
            raise ValueError(u'"f" variable value should be "min" or "max"')
    except Exception, e:
        return e        
#Exponential Moving Average  
# def EMA(df, n):  
#     EMA = pd.Series(df[u'close'].ewm( span = n, min_periods = n - 1).mean(), name = u'ema' + unicode(n))  
#     df = df.join(EMA)  
#     return df

def ADX(dfPassed, n, n_ADX):  
    i = 0  
    UpI = []  
    DoI = []  
    df = dfPassed[[u'high',u'low', u'close']].copy()
    df = df.reset_index(drop=True)

    while i + 1 <= df.index[-1]:  
        #print(df.loc[i + 1]['high'])
        UpMove = df.loc[i + 1][ u'high'] - df.loc[i][u'high']  
        DoMove = df.loc[i][ u'low'] - df.loc[i + 1][ u'low']  
        if UpMove > DoMove and UpMove > 0:  
            UpD = UpMove  
        else: UpD = 0  
        UpI.append(UpD)  
        if DoMove > UpMove and DoMove > 0:  
            DoD = DoMove  
        else: DoD = 0  
        DoI.append(DoD)  
        i = i + 1  
    i = 0  
    TR_l = [0]  
    while i < df.index[-1]:  
        TR = max(df.loc[i + 1][u'high'], df.loc[i][u'close']) - min(df.loc[i + 1][u'low'], df.loc[i][u'close'])  
        TR_l.append(TR)  
        i = i + 1  
    TR_s = pd.Series(TR_l)  
    ATR = pd.Series(TR_s.ewm( span = n, min_periods = n).mean())  
    UpI = pd.Series(UpI)  
    DoI = pd.Series(DoI)  
    PosDI = pd.Series(UpI.ewm(span = n, min_periods = n - 1).mean() / ATR, name = u'posDI5')  
    NegDI = pd.Series(DoI.ewm(span = n, min_periods = n - 1).mean() / ATR, name = u'negDI5')  
    df = df.join(PosDI)
    df = df.join(NegDI)
    intermediate = abs(PosDI - NegDI) / (PosDI + NegDI)
    ADX = pd.Series(intermediate.ewm( span = n_ADX, min_periods = n_ADX - 1).mean(), name = u'ADX5')  
    df = df.join(ADX)  
    return df

# df = pd.read_csv('/Users/meghamittal/Downloads/IBridgePy_Mac_Python27_64/Strategies/AAPLdata.csv')
# df2 = ADX(df,14,14)
# print(df2)
