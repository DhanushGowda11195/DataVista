#!/usr/bin/env python
# coding: utf-8

# In[1]:


# import sys
# !{sys.executable} -m pip install Pyarrow


# In[2]:


import pandas as pd
import numpy as np
import base64
import io
import datetime
import plotly.graph_objects as go
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback
from dash.exceptions import PreventUpdate
from github import Github
from github import InputGitTreeElement
import json
import re
import requests
import plotly.graph_objs as go


# In[3]:


vars = list()
with open('git_pat.txt', 'r') as file:
    for line in file:
        vars.append(line.replace('\n', ''))
        
token = vars[0]
repo_for_upload = vars[1]

g = Github(token)

repo = g.get_repo(repo_for_upload)


# In[4]:


def read_from_git(path):
    owner = vars[1].split('/')[0]
    repo = vars[1].split('/')[1]
    token = vars[0]
    
    r = requests.get('https://api.github.com/repos/{owner}/{repo}/contents/{path}'.format(owner=owner, repo=repo, path=path),
                     headers={'accept': 'application/vnd.github.v3.raw','authorization': 'token {}'.format(token)})
    return r   


# In[5]:


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)


# In[6]:


h1_style={'color':'#344e41','backgroundColor':'#dad7cd','text-align': 'center','font-weight':'bold'}

Tab_Style={'backgroundColor': '#000000','border':'none','padding': '6px','fontWeight': 'bold','color': 'white'}

Tab_Selected_Style={'borderTop': '4px solid #0000FF','borderBottom': '1px solid black','borderLeft': '1px solid black',
    'borderRight': '1px solid black','backgroundColor': '#1F1F1F','color': 'white','padding': '6px'}


# In[7]:


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xlsx' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        df=pd.DataFrame(data=['There was an error processing the data'],columns=['Error'])
        return [df.to_dict('records'),[{'name': i, 'id': i} for i in df.columns]]
        
    folder='session_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest_path_on_git_hub=folder+'/'+re.sub('.xlsx','',re.sub('.csv','',filename))+'.json'
    commit_message=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+': JSON file uploaded'
    json_data=df.to_json()
    repo.create_file(dest_path_on_git_hub, commit_message, json_data)
    repo.create_file(folder+'/dtype.json', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+': dtype file uploaded', json.dumps({x:str(df[x].dtype) for x in df.columns}))
    file_contents=repo.get_contents('current_dest_path_on_git_hub.txt')
    repo.update_file('current_dest_path_on_git_hub.txt', 'path updated', dest_path_on_git_hub,file_contents.sha)
    
    return [df.to_dict('records'),[{'name': i, 'id': i} for i in df.columns]]


# In[8]:


app.layout = html.Div([
    html.Div([html.H1(html.B('DataVista'),style=h1_style,className='row')]),
    dcc.Tabs(id='tabs-1',
              value='tab-1',
              children=[
                    dcc.Tab(label='Data',
                            value='tab-1',
                            # style=Tab_Style,
                            #  selected_style=Tab_Selected_Style,
                            className='custom-tab',
                            selected_className='custom-tab--selected',
                            children=[
                                html.Div([
                                    dcc.Upload(
                                        id='upload-data',
                                        children=html.Div([
                                            'Drag and Drop or ',
                                            html.A('Select Files')
                                        ]),
                                        style={
                                            'width': '100%',
                                            'height': '60px',
                                            'lineHeight': '60px',
                                            'borderWidth': '1px',
                                            'borderStyle': 'dashed',
                                            'borderRadius': '5px',
                                            'textAlign': 'center',
                                            'margin': '10px'
                                        },
                                        className='row',
                                        multiple=False)]),
                                html.Div(html.H4('Data Preview',className='row')),
                                html.Div(children=[dash_table.DataTable(id='dashtable',filter_action="native",sort_action="native",page_size=20)],className='row'),
                                html.Div(html.H4('Data Summarizing'),className='row'),
                                html.Div([
                                    html.Div([html.H6('Row Field',className='row'),
                                                 dcc.Dropdown(id='row_field',multi=True,searchable=True,className='row')],className='three columns'),
                                    html.Div([html.H6('Column Field',className='row'),
                                                 dcc.Dropdown(id='column_field',multi=True,searchable=True,className='row')],className='three columns'),
                                    html.Div([html.H6('Data Field',className='row'),
                                                 dcc.Dropdown(id='data_field',searchable=True,className='row')],className='three columns'),
                                    html.Div([html.H6('Aggregator',className='row'),
                                                 dcc.Dropdown(id='function_field',searchable=True,className='row')],className='three columns')],className='row'),
                                html.Div(id='summary_table',className='row')]),
                    dcc.Tab(label='Charts', 
                            value='tab-2',
                            className='custom-tab',
                            selected_className='custom-tab--selected',
                           children=[
                               html.Div([
                                   html.Div([html.H6('X-Axis',className='row'),
                                             dcc.Dropdown(id='x_axis',searchable=True,className='row')],className='three columns'),
                                   html.Div([html.H6('Y-Axis',className='row'),
                                             dcc.Dropdown(id='y_axis',searchable=True,className='row')],className='three columns'),
                                   html.Div([html.H6('Aggregator',className='row'),
                                             dcc.Dropdown(id='aggregator',searchable=True,className='row')],className='three columns'),
                                   html.Div([html.H6('Chart Type',className='row'),
                                             dcc.Dropdown(id='chart_type',options=['Bar','Line','Pie','Scatter'],searchable=True,className='row')],className='three columns')],className='row'),
                               html.Div(dcc.Graph(id='chart',className='row'),className='row')]),
                    dcc.Tab(label='Report',
                            value='tab-3',
                            className='custom-tab',
                            selected_className='custom-tab--selected')])
])


# In[9]:


@callback([Output('dashtable', 'data'),
          Output('dashtable', 'columns')],
          Input('upload-data', 'contents'),
          State('upload-data', 'filename'),
          State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children=parse_contents(list_of_contents, list_of_names, list_of_dates)
        
        path=read_from_git('current_dest_path_on_git_hub.txt').text
        data=read_from_git(path).json()
        global df
        df=pd.DataFrame(data)
        col_dtypes=read_from_git(path.split('/')[0]+'/'+'dtype.json').json()
        for i in col_dtypes.keys():
            df[i]=df[i].astype(col_dtypes[i])            
        return children
    else:
        df=pd.DataFrame(data=[' '],columns=[' '])
        return [df.to_dict('records'),[{'name': i, 'id': i} for i in df.columns]]


# In[10]:


@callback([Output('row_field', 'options'),
          Output('column_field', 'options'),
          Output('data_field', 'options'),
          Output('x_axis', 'options'),
          Output('y_axis', 'options')],
          [Input('dashtable', 'data'),
          Input('row_field', 'value'),
          Input('column_field', 'value'),
          Input('x_axis', 'value'),
          Input('y_axis', 'value')])
def update_dropdown_options1(list_of_contents,val1,val2,val3,val4):
    if list_of_contents is not None:
        if val2 is not None:
            opt1=[x for x in df.columns if x not in val2]
        else:
            opt1=[x for x in df.columns]
        if val1 is not None:
            opt2=[x for x in df.columns if x not in val1]
        else:
            opt2=[x for x in df.columns]
        opt3=[x for x in df.columns]
        if val4 is not None:
            opt4=[x for x in df.columns if x not in val4]
        else:
            opt4=[x for x in df.columns]
        if val3 is not None:
            opt5=[x for x in df.columns if x not in val3]
        else:
            opt5=[x for x in df.columns]
        return [opt1,opt2,opt3,opt4,opt5]
    else:
        raise PreventUpdate


# In[13]:


@callback(Output('function_field', 'options'),
          Input('data_field', 'value'))
def update_dropdown_options2(value):
    if value is not None:
        if df[value].dtype in ['int64','float64']:
            funcs=['Count','Distinct Count','Maximum','Minimum','Mean','Sum']
        else:
            funcs=['Count','Distinct Count']
        opt=[x for x in funcs]
        return opt
    else:
        return []


# In[14]:


@callback(Output('aggregator', 'options'),
          Input('y_axis', 'value'))
def update_dropdown_options3(value):
    if value is not None:
        if df[value].dtype in ['int64','float64']:
            funcs=['Count','Distinct Count','Maximum','Minimum','Mean','Sum']
        else:
            funcs=['Count','Distinct Count']
        opt=[x for x in funcs]
        return opt
    else:
        return []


# In[15]:


@callback(Output('summary_table', 'children'),
          [Input('row_field', 'value'),
          Input('column_field', 'value'),
          Input('data_field', 'value'),
          Input('function_field', 'value')])
def update_summary_table(row,column,data,function):
    if row is not None and column is not None and data is not None and function is not None:
        if function=='Distinct Count':
            function='nunique'
        elif function=='Maximum':
            function='max'
        elif function=='Minimum':
            function='min'
        else:
            function=function.lower()
        summary=df.pivot_table(values=data,index=row,columns=column,aggfunc=function).reset_index()
        return html.Div([dash_table.DataTable(
            data=summary.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in summary.columns],
            filter_action="native",
            sort_action="native",
            page_size=10,
            export_format='xlsx',
            export_headers='display')])


# In[16]:


@callback(Output('chart', 'figure'),
          [Input('x_axis', 'value'),
          Input('y_axis', 'value'),
          Input('aggregator', 'value'),
          Input('chart_type', 'value')])
def update_chart(x,y,function,chart_type):
    if x is not None and y is not None and chart_type is not None and function is not None:
        layout = dict(plot_bgcolor='white',
                  margin=dict(t=20, l=20, r=20, b=20),
                  xaxis=dict(title=x,showgrid=False),
                  yaxis=dict(title=function+' of '+y,showgrid=False))
        if function=='Distinct Count':
            function='nunique'
        elif function=='Maximum':
            function='max'
        elif function=='Minimum':
            function='min'
        else:
            function=function.lower()
        group=df.pivot_table(values=y,index=x,aggfunc=function).reset_index()
        
        if chart_type=='Pie':
            fig=go.Figure(data=go.Pie(labels=group[x].values,values=group[y].values,text=group[x].values),layout=layout)
        elif chart_type=='Bar':
            fig=go.Figure(data=go.Bar(x=group[x].values,y=group[y].values,text=group[y].values),layout=layout)
        elif chart_type=='Line':
            fig=go.Figure(data=go.Scatter(x=group[x].values,y=group[y].values,text=group[y].values),layout=layout)
        elif chart_type=='Scatter':
            fig=go.Figure(data=go.Scatter(x=group[x].values,y=group[y].values,text=group[y].values,mode='markers'),layout=layout)
        return fig
    else:
        fig=go.Figure()
        # fig.update_layout(plot_bgcolor='white',paper_bgcolor='white',
        #                   font=dict(color='white'),annotations=[{"text": "No Data Available","xref": "paper","yref": "paper",
        #                     "showarrow": False,"font": {"size": 28}}])
        fig.update_xaxes(showgrid=False,zeroline=False,showticklabels=False,visible=False)
        fig.update_yaxes(showgrid=False,zeroline=False,showticklabels=False,visible=False)
        return fig
    


# In[17]:


# df=pd.read_excel('Global_Superstore.xlsx')
# df


# In[18]:


if __name__ == '__main__':
    app.run(debug=True, jupyter_mode="tab")


# In[19]:


# path.split('/')[0].split('_')[1]+sha

