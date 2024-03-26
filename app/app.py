#!/usr/bin/env python
# coding: utf-8

# In[1]:


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

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle,Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from svglib.svglib import svg2rlg
import warnings
warnings.filterwarnings("ignore")


# In[ ]:


vars = list()
with open('token/git_pat.txt', 'r') as file:
    for line in file:
        vars.append(line.replace('\n', ''))
        
token = vars[0]
repo_for_upload = vars[1]

g = Github(token)

repo = g.get_repo(repo_for_upload)


# In[ ]:


def read_from_git(path):
    owner = vars[1].split('/')[0]
    repo = vars[1].split('/')[1]
    token = vars[0]
    
    r = requests.get('https://api.github.com/repos/{owner}/{repo}/contents/{path}'.format(owner=owner, repo=repo, path=path),
                     headers={'accept': 'application/vnd.github.v3.raw','authorization': 'token {}'.format(token)})
    return r   


# In[ ]:


# Processing the charts to be pasted into PDF

def figure_chart(chart):
    imgdata = io.BytesIO()
    chart.write_image(imgdata,format='svg')
    imgdata.seek(0)
    drawing=svg2rlg(imgdata)
    I = Image(drawing)
    I.drawHeight = 2.5*inch*I.drawHeight / I.drawWidth
    I.drawWidth = 8*inch
    return I


# Defining Style to the PDF Doc
styleSheet = getSampleStyleSheet()
styleSub=ParagraphStyle(name='Normal',fontSize=12,fontName='Helvetica',alignment=TA_CENTER)
style = ParagraphStyle(name='Normal',fontSize=8,fontName='Helvetica')
style2 = ParagraphStyle(name='Normal',fontSize=6,fontName='Helvetica')
styleth = ParagraphStyle(name='Normal',fontSize=8,fontName='Helvetica',alignment=TA_CENTER)
stylech = ParagraphStyle(name='Normal',fontSize=12,fontName='Helvetica',alignment=TA_CENTER,leading=0)
styleH=ParagraphStyle(name='Heading1',fontSize=12,fontName='Helvetica',leading=24)
styleT=ParagraphStyle(name='Heading1',fontSize=24,fontName='Helvetica',leading=36,alignment=TA_CENTER)
styleS=ParagraphStyle(name='Heading3',fontSize=12,fontName='Helvetica',leading=16,alignment=TA_LEFT)
styleD=ParagraphStyle(name='Normal',fontSize=8,fontName='Helvetica',leftIndent=6,spaceAfter=10,spaceBefore=6)
def addPageNumber(canvas, doc):
    page_num = canvas.getPageNumber()
    text = "Page %s" % page_num
    canvas.drawRightString(200*mm, 10*mm, text)


# In[ ]:


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)


# In[ ]:


h1_style={'color':'#344e41','backgroundColor':'#dad7cd','text-align': 'center','font-weight':'bold'}

Tab_Style={'backgroundColor': '#000000','border':'none','padding': '6px','fontWeight': 'bold','color': 'white'}

Tab_Selected_Style={'borderTop': '4px solid #0000FF','borderBottom': '1px solid black','borderLeft': '1px solid black',
    'borderRight': '1px solid black','backgroundColor': '#1F1F1F','color': 'white','padding': '6px'}


# In[ ]:


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
        
    folder='input/session_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest_path_on_git_hub=folder+'/'+re.sub('.xlsx','',re.sub('.csv','',filename))+'.json'
    commit_message=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+': JSON file uploaded'
    json_data=df.to_json()
    repo.create_file(dest_path_on_git_hub, commit_message, json_data)
    repo.create_file(folder+'/dtype.json', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+': dtype file uploaded', json.dumps({x:str(df[x].dtype) for x in df.columns}))
    file_contents=repo.get_contents('current_dest_path_on_git_hub.txt')
    repo.update_file('current_dest_path_on_git_hub.txt', 'path updated', dest_path_on_git_hub,file_contents.sha)
    
    return [df.to_dict('records'),[{'name': i, 'id': i} for i in df.columns]]


# In[ ]:


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
                            selected_className='custom-tab--selected',
                           children=[
                               html.Div([
                                   html.Div([html.H6('X-Axis',className='row'),
                                             dcc.Dropdown(id='x_axis2',searchable=True,className='row')],className='three columns'),
                                   html.Div([html.H6('Y-Axis',className='row'),
                                             dcc.Dropdown(id='y_axis2',searchable=True,className='row')],className='three columns'),
                                   html.Div([html.H6('Aggregator',className='row'),
                                             dcc.Dropdown(id='aggregator2',searchable=True,className='row')],className='three columns'),
                                   html.Div([html.H6('Chart Type',className='row'),
                                             dcc.Dropdown(id='chart_type2',options=['Bar','Line','Pie','Scatter'],searchable=True,className='row')],className='three columns')],className='row'),
                               html.Div(dcc.Graph(id='chart2',className='row'),className='row'),
                               html.Div(dcc.Textarea(id='txtbox',style={'width': '100%', 'height': 200}),className='row'),
                               html.Div(html.Button('Export to PDF', id='export_btn', n_clicks=0),className='row'),
                               dcc.Download(id="download_pdf")])])])


# In[ ]:


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


# In[ ]:


@callback([Output('row_field', 'options'),
          Output('column_field', 'options'),
          Output('data_field', 'options'),
          Output('x_axis', 'options'),
          Output('y_axis', 'options'),
          Output('x_axis2', 'options'),
          Output('y_axis2', 'options')],
          [Input('dashtable', 'data'),
          Input('row_field', 'value'),
          Input('column_field', 'value'),
          Input('x_axis', 'value'),
          Input('y_axis', 'value'),
          Input('x_axis2', 'value'),
          Input('y_axis2', 'value')])
def update_dropdown_options1(list_of_contents,val1,val2,val3,val4,val5,val6):
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
        if val6 is not None:
            opt6=[x for x in df.columns if x not in val6]
        else:
            opt6=[x for x in df.columns]
        if val5 is not None:
            opt7=[x for x in df.columns if x not in val5]
        else:
            opt7=[x for x in df.columns]
        return [opt1,opt2,opt3,opt4,opt5,opt6,opt7]
    else:
        raise PreventUpdate


# In[ ]:


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


# In[ ]:


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


# In[ ]:


@callback(Output('aggregator2', 'options'),
          Input('y_axis2', 'value'))
def update_dropdown_options4(value):
    if value is not None:
        if df[value].dtype in ['int64','float64']:
            funcs=['Count','Distinct Count','Maximum','Minimum','Mean','Sum']
        else:
            funcs=['Count','Distinct Count']
        opt=[x for x in funcs]
        return opt
    else:
        return []


# In[ ]:


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


# In[ ]:


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
        fig.update_xaxes(showgrid=False,zeroline=False,showticklabels=False,visible=False)
        fig.update_yaxes(showgrid=False,zeroline=False,showticklabels=False,visible=False)
        return fig
    


# In[ ]:


@callback(Output('chart2', 'figure'),
          [Input('x_axis2', 'value'),
          Input('y_axis2', 'value'),
          Input('aggregator2', 'value'),
          Input('chart_type2', 'value')])
def update_chart2(x,y,function,chart_type):
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
        fig.update_xaxes(showgrid=False,zeroline=False,showticklabels=False,visible=False)
        fig.update_yaxes(showgrid=False,zeroline=False,showticklabels=False,visible=False)
        return fig


# In[ ]:


@callback(
    Output("download_pdf", "data"),
    [Input("export_btn", "n_clicks"),
    Input("txtbox", "value"),
    Input('chart2', 'figure')],
    prevent_initial_call=True,
)
def func(n_clicks,val,fig):
    # Building the Final PDF
    if n_clicks>0:
        if fig is not None:
            currentTime=datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")
            buffer=io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    topMargin=0.5*inch,bottomMargin=0.5*inch,leftMargin=0.5*inch,rightMargin=0.5*inch)
            
            elements = []
            elements.append(Paragraph('<b>Report</b>',style=styleT))
            data3=[[figure_chart(go.Figure(fig))],[Paragraph(val)]]            
            ch2=Table(data3)
            ch2.setStyle(TableStyle([('TEXTCOLOR',(0,0),(1,-1),colors.black),('FONTSIZE',(0,0),(1,-1),8),('ALIGN', (1,0), (-1,-1), 'LEFT'),
                                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            elements.append(ch2)
            doc.build(elements)
            buffer.seek(0)
            pdf_content=buffer.getvalue()
            return dcc.send_bytes(pdf_content,'Report'+currentTime+'.pdf')


if __name__ == '__main__':
    app.run(debug=True, jupyter_mode="tab")

