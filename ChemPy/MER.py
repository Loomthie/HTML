import pandas as pd
import plotly.graph_objects as go


class Therm_Stream:

    def __init__(self,name,T_in,T_out,mCp):
        self.Name = name
        self.T_in = T_in
        self.T_out = T_out
        self.mCp = mCp
        self.dTemp = self.T_out - self.T_in
        self.Enthalpy = abs(self.dTemp*self.mCp)


class MER:

    def __init__(self,*Streams:Therm_Stream,t_min=10.):
        self.heated_streams = [a for a in filter(lambda x: x.T_out>x.T_in,Streams)]
        self.cooled_streams = [a for a in filter(lambda x: x.T_in>x.T_out,Streams)]
        self.t_min = t_min
        self.res = self.__MER()

    def __MER(self):
        adj_c_strm = [Therm_Stream(a.Name,a.T_in - self.t_min,a.T_out-self.t_min,a.mCp) for a in self.cooled_streams]
        self.adj_cooled_streams = adj_c_strm

        crit_Ts = [*[a.__dict__[key] for key in ['T_in','T_out'] for a in self.heated_streams],
                   *[a.__dict__[key] for key in ['T_in', 'T_out'] for a in adj_c_strm]]

        crit_Ts = list(set(crit_Ts))
        crit_Ts.sort(reverse=True)

        self.crit_Ts = crit_Ts

        columns = ['Interval','T_hi','T_lo','mCp','dH','R']
        data = [
            ['(Steam)',0,0,0,0,0],
            *[[i+1,crit_Ts[i],crit_Ts[i+1],0,0,0] for i in range(len(crit_Ts)-1)]
        ]

        df = pd.DataFrame(data,columns=columns)
        for row_i in range(len(df.iloc[:])):
            row = df.iloc[row_i].copy()
            mCp = 0
            for s in self.heated_streams:
                if s.T_out >= row.T_hi and row.T_lo >= s.T_in:
                    mCp -= s.mCp

            for s in adj_c_strm:
                if s.T_in >= row.T_hi and s.T_out <= row.T_lo:
                    mCp += s.mCp

            row.mCp = mCp
            row.dH = mCp * (row.T_hi-row.T_lo)
            row.R = row.dH if row_i == 0 else row.dH + df.iloc[row_i-1].R

            df.iloc[row_i] = row

        df.R += max(-df.R)

        return df

    def show_diagram(self):
        fig = go.Figure()

        i = 1
        for s in self.heated_streams:
            fig.add_trace(
                go.Scatter(
                    x=2*[s.Name],
                    y=[s.T_in,s.T_out],
                    line = dict(
                        color='#ff0000'
                    ),
                    marker=dict(
                        size=10,
                        symbol='arrow-bar-up',
                        angleref='previous'
                    )
                )
            )

            i += 1

        j = 1
        for s in self.adj_cooled_streams:
            fig.add_trace(
                go.Scatter(
                    x=2*[s.Name],
                    y=[s.T_in,s.T_out],
                    line=dict(
                        color='#0000ff'
                    ),
                    marker=dict(
                        size=10,
                        symbol='arrow-bar-up',
                        angleref='previous'
                    )
                )
            )
            j+=1

        for t in self.crit_Ts:
            fig.add_trace(
                go.Scatter(
                    x=['C1',f'H{j-1}'],
                    y=2*[t],
                    line=dict(
                        color='#000',
                        dash='dash'
                    ),
                    mode='lines'
                )
            )

        fig.update_layout(
            showlegend=False,
            yaxis = dict(
                showgrid=False,
                tickvals=self.crit_Ts
            ),
            xaxis=dict(
                showgrid=False
            )
        )

        fig.show()

